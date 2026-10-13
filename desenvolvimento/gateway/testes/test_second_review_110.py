"""Second-review regressions: atomic containment, inherited pipes and text identity."""
import ctypes
import os
import re
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest import mock

sys.path[:0] = [str(Path(__file__).resolve().parent), str(Path(__file__).resolve().parents[1])]
from mcp_sentry_gateway import core, process_tree, verified_copies
import test_verified_copy_equivalence as copies
import test_review_findings_110 as findings


@unittest.skipUnless(os.name == "nt", "Windows job creation")
class AtomicJobTests(unittest.TestCase):
    def test_job_failures_never_start_backend(self):
        for api in ("CreateJobObjectW", "SetInformationJobObject", "UpdateProcThreadAttribute", "CreateProcessW"):
            with self.subTest(api=api), tempfile.TemporaryDirectory() as folder:
                marker = Path(folder) / "executed"
                command = [sys.executable, "-c", f"from pathlib import Path; Path({str(marker)!r}).touch()"]
                with mock.patch.object(process_tree._kernel32, api, return_value=0), \
                        mock.patch.object(process_tree._ntdll, "NtResumeProcess", wraps=process_tree._ntdll.NtResumeProcess) as resume:
                    with self.assertRaises(OSError):
                        process_tree.spawn(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    resume.assert_not_called()
                self.assertFalse(marker.exists())

    def test_legacy_assignment_failure_kills_suspended_process(self):
        process = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"],
                                   creationflags=process_tree.creation_flags())
        try:
            with mock.patch.object(process_tree._kernel32, "AssignProcessToJobObject", return_value=0), \
                    mock.patch.object(process_tree._ntdll, "NtResumeProcess") as resume:
                with self.assertRaises(OSError):
                    process_tree.ProcessTree.contain(process)
                resume.assert_not_called()
            self.assertIsNotNone(process.poll())
        finally:
            if process.poll() is None:
                process.kill(); process.wait(timeout=5)

    def test_resume_failure_kills_job_and_closes_process_pipes(self):
        with mock.patch.object(process_tree._ntdll, "NtResumeProcess", return_value=-1):
            with self.assertRaises(OSError):
                process_tree.spawn([sys.executable, "-c", "import time; time.sleep(60)"],
                                   stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def test_gateway_death_before_resume_kills_already_assigned_process(self):
        with tempfile.TemporaryDirectory() as folder:
            pidfile = Path(folder) / "backend.pid"
            worker = '''import sys,time,subprocess
from pathlib import Path
from mcp_sentry_gateway import process_tree as p
def before_resume(handle):
    time.sleep(60)
    return 0
original=p._JobPopen._execute_child
def record(self,*args,**kwargs):
    original(self,*args,**kwargs)
    Path(sys.argv[1]).write_text(str(self.pid))
p._JobPopen._execute_child=record
p._ntdll.NtResumeProcess=before_resume
p.spawn([sys.executable,'-c','import time; time.sleep(60)'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
'''
            gateway = subprocess.Popen([sys.executable, "-B", "-c", worker, str(pidfile)],
                                       cwd=Path(__file__).resolve().parents[1],
                                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            pid = None
            try:
                self.assertTrue(findings.wait_until(lambda: pidfile.exists() and pidfile.stat().st_size > 0))
                pid = int(pidfile.read_text())
                self.assertTrue(findings.process_alive(pid))
                gateway.kill(); gateway.wait(timeout=5)
                self.assertTrue(findings.wait_until(lambda: not findings.process_alive(pid)))
            finally:
                if gateway.poll() is None:
                    gateway.kill(); gateway.wait(timeout=5)
                if pid is not None and findings.process_alive(pid):
                    findings.kill(pid)

    def test_pipe_inheritance_does_not_block_gateway_close(self):
        fixture = copies.QuietServerTests("test_copies_do_not_accumulate")
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        pidfile = fixture.outside / "child.pid"
        prefix = f'''import subprocess,sys
from pathlib import Path
child=subprocess.Popen([sys.executable,'-c','import time; time.sleep(60)'])
Path({str(pidfile)!r}).write_text(str(child.pid))
'''
        (fixture.project / "server.py").write_text(prefix + fixture.server_source, encoding="utf-8")
        core.approve(fixture.manifest, fixture.state)
        gateway = fixture.open()
        fixture.whoami(gateway)
        pid = int(pidfile.read_text())
        done = threading.Event()
        errors = []
        def close():
            try:
                gateway.backend.close()
            except BaseException as exc:
                errors.append(exc)
            finally:
                done.set()
        thread = threading.Thread(target=close, daemon=True)
        thread.start()
        try:
            finished = done.wait(8)
        finally:
            if findings.process_alive(pid):
                findings.kill(pid)
            thread.join(timeout=5)
        self.assertTrue(finished, "close blocked before killing a descendant that inherited stderr")
        self.assertEqual(errors, [])
        self.assertFalse(findings.process_alive(pid))

    def test_query_failure_is_not_confirmed_on_second_terminate(self):
        process, tree = process_tree.spawn([sys.executable, "-c", "import time; time.sleep(60)"])
        try:
            with mock.patch.object(tree, "active_processes", return_value=None):
                self.assertFalse(tree.terminate(timeout=0.05))
            self.assertFalse(tree.terminate())
        finally:
            tree.terminate()
            process.wait(timeout=5)

    def test_nested_job_with_virtual_environment_launcher(self):
        with tempfile.TemporaryDirectory() as folder:
            environment = Path(folder) / "venv"
            subprocess.run([sys.executable, "-m", "venv", "--without-pip", str(environment)],
                           check=True, timeout=30, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            worker = '''import sys,subprocess
from mcp_sentry_gateway import process_tree as p
backend,inner=p.spawn([sys.argv[1],'-c','import time; print("ready",flush=True); time.sleep(60)'],
                      stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
try:
    assert backend.stdout.readline().strip()=='ready'
    assert inner.active_processes()>=2  # venv launcher and the real interpreter
    assert inner.terminate()
    backend.wait(timeout=5)
finally:
    inner.terminate()
    for stream in (backend.stdin,backend.stdout,backend.stderr): stream.close()
'''
            outer, tree = process_tree.spawn(
                [sys.executable, "-B", "-c", worker, str(environment / "Scripts/python.exe")],
                cwd=Path(__file__).resolve().parents[1],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            try:
                stdout, stderr = outer.communicate(timeout=15)
                self.assertEqual(outer.returncode, 0, stderr)
                self.assertTrue(tree.terminate())
            finally:
                tree.terminate()
                outer.wait(timeout=5)


class ReplacementPathTests(unittest.TestCase):
    def test_kept_copy_never_serves_a_new_connection_at_its_old_path(self):
        """Killed (in-use mark) copies are moved and rechecked; contaminated ones are replaced."""
        for interrupted in (True, False):
            with self.subTest(interrupted=interrupted), tempfile.TemporaryDirectory() as folder:
                pool = Path(folder) / "pool"
                files = [{"path": "x", "sha256": core.digest(b"approved")}]
                first = verified_copies.lease(pool, "a" * 64, files, ".", reusable=True)
                (first.root / "x").write_bytes(b"approved")
                first.release(keep=True)
                if interrupted:
                    verified_copies._in_use_path(first.root).touch()
                else:
                    (first.root / "x").write_bytes(b"contaminated")
                second = verified_copies.lease(pool, "a" * 64, files, ".", reusable=True)
                try:
                    self.assertEqual(second.reused, interrupted)
                    self.assertNotEqual(second.root, first.root)
                    self.assertFalse(first.root.exists())
                finally:
                    second.release(keep=False)


class TextRuleIdentityTests(unittest.TestCase):
    def test_regex_flags_change_identity_and_prevent_old_text_seeding(self):
        fixture = copies.QuietServerTests("test_copies_do_not_accumulate")
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        self.addCleanup(findings.RedactionRuleChangeTests.clear)
        raw = 'VALUE = "approved helper"\népassword = "public-probe-value"\n'.encode()
        (fixture.project / "helper.py").write_bytes(raw)
        core.approve(fixture.manifest, fixture.state)
        original = core.TEXT_RULES_FINGERPRINT
        pattern = re.compile(core._SECRET_ASSIGNMENT.pattern,
                             (core._SECRET_ASSIGNMENT.flags & ~re.UNICODE) | re.ASCII)
        with mock.patch.object(core, "_SECRET_ASSIGNMENT", pattern):
            fingerprint = core._text_rules_fingerprint()
            self.assertNotEqual(fingerprint, original)
            with mock.patch.object(core, "TEXT_RULES_FINGERPRINT", fingerprint):
                hashes = []
                for clear in (False, True, False):
                    if clear:
                        findings.RedactionRuleChangeTests.clear()
                    result = core.inspect(fixture.manifest, fixture.state, return_capture=True)
                    text = next(f["content"] for f in result["_capture"]["files"] if f["path"] == "helper.py")
                    self.assertEqual(text, core.safe_text(raw))
                    self.assertNotIn("public-probe-value", text)
                    hashes.append(result["dossier"]["current_hash"])
                self.assertEqual(len(set(hashes)), 1)


@unittest.skipUnless(os.name == "nt", "Windows stream enumeration")
class StreamPathTests(unittest.TestCase):
    def test_extended_paths_for_drive_unc_and_already_extended_unc(self):
        paths = {r"C:\copy": r"\\?\C:\copy",
                 r"\\server\share\copy": r"\\?\UNC\server\share\copy",
                 r"\\?\UNC\server\share\copy": r"\\?\UNC\server\share\copy"}
        for original, expected in paths.items():
            with self.subTest(path=original), \
                    mock.patch.object(verified_copies._kernel32, "FindFirstStreamW", return_value=verified_copies._INVALID_HANDLE) as api, \
                    mock.patch.object(ctypes, "get_last_error", return_value=38):
                self.assertEqual(verified_copies._streams(original), [])
                self.assertEqual(api.call_args.args[0], expected)


if __name__ == "__main__":
    unittest.main()
