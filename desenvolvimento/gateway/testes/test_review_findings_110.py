"""Regression tests for the independent review of 1.1.0 (findings A, B, D, E, F, G).

A: a descendant of the backend must not survive to write into a kept copy.
B: NTFS alternate data streams in a kept copy make it non-reusable.
D: reused redacted text must always equal what the current rules produce.
E/F: concurrent releases keep at most one idle copy; lock files do not pile up.
G: the root-prefix check keeps characters that belong to a POSIX name.
"""
import ctypes
import json
import ntpath
import os
import posixpath
import sys
import threading
import time
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import test_verified_copy_equivalence as copies
from mcp_sentry_gateway import core, verified_copies
from mcp_sentry_gateway.core import VERIFIED_COPIES_DIR, accept_current, approve, inspect

WINDOWS = os.name == "nt"

CHILD_PREFIX = '''import os, subprocess, sys
_pid_file = os.environ.get("CHILD_PID_FILE")
if _pid_file:
    _flags = getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    _child = subprocess.Popen([sys.executable, "-c", "import time\\nwhile True: time.sleep(0.2)"],
                              creationflags=_flags, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    with open(_pid_file, "w") as _stream:
        _stream.write(str(_child.pid))
'''

ADS_PREFIX = '''import os
_here = os.path.dirname(os.path.abspath(__file__))
_streams = [os.path.abspath(__file__) + ":backend-state", _here + ":folder-state"]
_ads_existed = []
for _stream in _streams:
    try:
        with open(_stream, encoding="utf-8") as _handle:
            _ads_existed.append(_handle.read())
    except OSError:
        pass
for _stream in _streams:
    with open(_stream, "w", encoding="utf-8") as _handle:
        _handle.write("written by the backend")
'''


def process_alive(pid):
    if not WINDOWS:
        try:
            os.kill(pid, 0)
        except OSError:
            return False
        return True
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.OpenProcess.restype = ctypes.c_void_p
    handle = kernel32.OpenProcess(0x00100000, False, pid)  # SYNCHRONIZE
    if not handle:
        return False
    try:
        return kernel32.WaitForSingleObject(ctypes.c_void_p(handle), 0) == 0x102  # WAIT_TIMEOUT
    finally:
        kernel32.CloseHandle(ctypes.c_void_p(handle))


def kill(pid):
    if not WINDOWS:
        os.kill(pid, 9)
        return
    import subprocess
    # The tree: a virtual-environment python.exe starts a second interpreter.
    subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], capture_output=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.OpenProcess.restype = ctypes.c_void_p
    handle = kernel32.OpenProcess(0x0001, False, pid)  # PROCESS_TERMINATE
    if handle:
        kernel32.TerminateProcess(ctypes.c_void_p(handle), 1)
        kernel32.CloseHandle(ctypes.c_void_p(handle))


def only_own_tests(cls):
    """Reuse the fixture helpers without re-running the inherited equivalence tests."""
    for name in dir(cls):
        if name.startswith("test_") and name not in cls.__dict__:
            setattr(cls, name, None)
    return cls


def wait_until(condition, seconds=5.0):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if condition():
            return True
        time.sleep(0.05)
    return condition()


@only_own_tests
@unittest.skipUnless(WINDOWS, "descendant containment requires Windows jobs")
class SurvivingDescendantTests(copies.QuietServerTests):
    """Finding A."""

    def setUp(self):
        super().setUp()
        source = CHILD_PREFIX + self.server_source
        (self.project / "server.py").write_bytes(source.encode("utf-8"))
        self.manifest_data["configuration"]["passthrough_names"] = ["CHILD_PID_FILE"]
        self.save_manifest()
        self.pid_file = self.outside / "child.pid"
        patcher = mock.patch.dict(os.environ, {"CHILD_PID_FILE": str(self.pid_file)})
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(self.kill_child)

    def kill_child(self):
        if self.pid_file.exists():
            kill(int(self.pid_file.read_text()))

    def approved_report(self, source=None):
        report = super().approved_report(source or CHILD_PREFIX + self.server_source)
        return report

    def change_source(self, marker):
        source = CHILD_PREFIX + self.server_source + f"\n# {marker}\n"
        (self.project / "server.py").write_bytes(source.encode("utf-8"))
        return source

    def test_descendant_does_not_survive_a_normal_close(self):
        approve(self.manifest, self.state)
        self.run_once()
        pid = int(self.pid_file.read_text())
        self.assertTrue(wait_until(lambda: not process_alive(pid)),
                        "a descendant of the backend survived and could write into a kept copy")

    def test_descendant_does_not_survive_the_death_of_the_gateway(self):
        if not WINDOWS:
            self.skipTest("gateway death containment is implemented with Windows job objects")
        approve(self.manifest, self.state)
        import subprocess
        gateway = subprocess.Popen(
            [sys.executable, "-m", "mcp_sentry_gateway.gateway", "--interface", "execution",
             "--manifest", str(self.manifest), "--store", str(self.state)],
            cwd=str(Path(__file__).resolve().parents[1]), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, text=True, encoding="utf-8")
        try:
            for message in ({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
                                "protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "t", "version": "1"}}},
                            {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "whoami", "arguments": {}}}):
                gateway.stdin.write(json.dumps(message) + "\n"); gateway.stdin.flush()
                self.assertIn('"id"', gateway.stdout.readline())
            pid = int(self.pid_file.read_text())
            self.assertTrue(process_alive(pid))
        finally:
            gateway.kill()  # abrupt death: no close() runs
            gateway.wait()
            gateway.stdin.close()
            gateway.stdout.close()
        self.assertTrue(wait_until(lambda: not process_alive(pid)),
                        "a descendant survived the death of the gateway")
        report, _ = self.run_once()
        self.assertEqual(report["server_sha256"], self.approved_report()["server_sha256"])


@only_own_tests
@unittest.skipUnless(WINDOWS, "NTFS alternate data streams")
class AlternateDataStreamTests(copies.QuietServerTests):
    """Finding B."""

    def setUp(self):
        super().setUp()
        (self.project / "server.py").write_bytes((ADS_PREFIX + self.server_source).encode("utf-8"))
        self.save_manifest()

    def approved_report(self, source=None):
        return super().approved_report(source or ADS_PREFIX + self.server_source)

    def change_source(self, marker):
        source = ADS_PREFIX + self.server_source + f"\n# {marker}\n"
        (self.project / "server.py").write_bytes(source.encode("utf-8"))
        return source

    def test_streams_written_by_the_backend_do_not_reach_the_next_connection(self):
        approve(self.manifest, self.state)
        self.run_once()
        self.run_once()
        self.assertEqual(self.last_start().get("copy_reused"), 0)

    def test_planted_stream_on_a_quiet_copy_prevents_reuse(self):
        (self.project / "server.py").write_bytes(self.server_source.encode("utf-8"))
        approve(self.manifest, self.state)
        self.run_once()
        copy = self.kept_copies()[0]
        with open(str(copy / "server.py") + ":planted", "w", encoding="utf-8") as stream:
            stream.write("state")
        self.run_once()
        self.assertEqual(self.last_start().get("copy_reused"), 0)
        self.run_once()
        self.assertEqual(self.last_start().get("copy_reused"), 1, "a clean replacement copy is reusable again")


class RedactionRuleChangeTests(unittest.TestCase):
    """Finding D: seeded text must equal the output of the current rules."""

    def setUp(self):
        fixture = copies.VerifiedCopyEquivalenceTests("test_copies_do_not_accumulate")
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        self.manifest, self.state, self.project = fixture.manifest, fixture.state, fixture.project
        (self.project / "helper.py").write_bytes(b'VALUE = "approved helper"\nlabel = "classified-word"\n')
        self.clear()

    @staticmethod
    def clear():
        with core._TEXT_CACHE_LOCK:
            core._TEXT_CACHE.clear()
            core._TEXT_CACHE_BYTES = 0

    def new_rules(self):
        original = core.safe_text
        def stricter(raw):
            return original(raw).replace("classified-word", "[REDACTED]")
        return mock.patch.multiple(core, safe_text=stricter, TEXT_RULES_FINGERPRINT="test-new-rules")

    def test_hash_does_not_depend_on_the_cache_after_a_rule_change(self):
        approve(self.manifest, self.state)
        inspect(self.manifest, self.state)  # old rules: may record that the baseline text is current
        with self.new_rules():
            self.clear()
            cold = inspect(self.manifest, self.state)["dossier"]["current_hash"]
            warm = inspect(self.manifest, self.state)["dossier"]["current_hash"]
            self.clear()
            again = inspect(self.manifest, self.state)["dossier"]["current_hash"]
        self.assertEqual(cold, warm)
        self.assertEqual(cold, again)

    def test_new_file_with_known_bytes_uses_the_current_rules(self):
        approve(self.manifest, self.state)
        inspect(self.manifest, self.state)
        (self.project / "twin.py").write_bytes((self.project / "helper.py").read_bytes())
        data = json.loads(self.manifest.read_text(encoding="utf-8"))
        data["inspect_roots"].append("twin.py")
        self.manifest.write_text(json.dumps(data), encoding="utf-8")
        with self.new_rules():
            self.clear()
            dossier = inspect(self.manifest, self.state)["dossier"]
        twin = next(change for change in dossier["changes"] if change["path"] == "twin.py")
        self.assertNotIn("classified-word", twin["diff"])

    def test_same_rules_still_skip_redaction_for_unchanged_files(self):
        """P1 keeps its gain once the baseline text is confirmed for the current rules."""
        approve(self.manifest, self.state)
        self.clear()
        inspect(self.manifest, self.state)
        self.clear()
        with mock.patch.object(core, "safe_text", wraps=core.safe_text) as counted:
            inspect(self.manifest, self.state)
        redacted = [call.args[0] for call in counted.call_args_list]
        for name in ("server.py", "helper.py"):
            self.assertNotIn((self.project / name).read_bytes(), redacted, f"{name} was redacted again")


@only_own_tests
@unittest.skipUnless(WINDOWS, "kept copies require Windows jobs")
class PoolCoordinationTests(copies.QuietServerTests):
    """Findings E and F."""

    def test_concurrent_releases_keep_at_most_one_idle_copy(self):
        approve(self.manifest, self.state)
        first, second = self.open(), self.open()
        self.whoami(first); self.whoami(second)
        original = verified_copies.CopyLease._free_sibling_exists
        def slow(lease):
            result = original(lease)
            time.sleep(0.3)
            return result
        with mock.patch.object(verified_copies.CopyLease, "_free_sibling_exists", slow):
            threads = [threading.Thread(target=gateway.backend.close) for gateway in (first, second)]
            for thread in threads: thread.start()
            for thread in threads: thread.join()
        self.assertLessEqual(len(self.kept_copies()), 1)

    def test_copy_left_by_a_killed_connection_is_reused_only_at_a_new_path(self):
        """Clients such as Codex kill the gateway; its job already killed the backend tree."""
        approve(self.manifest, self.state)
        self.run_once()
        copy = self.kept_copies()[0]
        (copy.parent / (copy.name + verified_copies.IN_USE_SUFFIX)).touch()  # as left by a killed gateway
        report, _ = self.run_once()
        self.assertEqual(report, self.approved_report())
        self.assertEqual(self.last_start().get("copy_reused"), 1)
        self.assertFalse(copy.exists(), "the old path must not remain usable")
        self.assertNotIn(copy, self.kept_copies())

    @unittest.skipUnless(WINDOWS, "Windows refuses to move a folder that is in use")
    def test_copy_still_in_use_by_a_process_is_not_reused(self):
        approve(self.manifest, self.state)
        self.run_once()
        copy = self.kept_copies()[0]
        holder = open(copy / "helper.py", "rb")  # a process still using the copy
        try:
            report, _ = self.run_once()
        finally:
            holder.close()
        self.assertEqual(report, self.approved_report())
        self.assertEqual(self.last_start().get("copy_reused"), 0)

    def test_lock_files_do_not_accumulate_across_versions(self):
        approve(self.manifest, self.state)
        for number in range(6):
            self.change_source(f"version {number}")
            accept_current(self.manifest, self.state)
            self.run_once()
        pool = self.state / VERIFIED_COPIES_DIR
        locks = [path for path in pool.glob("*.lock") if path.name != verified_copies.POOL_LOCK_NAME]
        orphans = [path for path in locks if not path.with_suffix("").exists()]
        self.assertEqual(orphans, [])
        self.assertLessEqual(len(self.kept_copies()), 1)


class RootPrefixTests(unittest.TestCase):
    """Finding G."""

    def test_posix_name_ending_in_backslash(self):
        prefix = core._root_prefix("/tmp/project\\", posixpath)
        self.assertTrue(posixpath.normcase("/tmp/project\\/x.py").startswith(prefix))
        self.assertFalse(posixpath.normcase("/tmp/project-other/x.py").startswith(prefix))

    def test_windows_roots(self):
        cases = {"C:\\": "c:\\x.py", "C:\\Proj": "c:\\proj\\x.py", "\\\\server\\share\\proj": "\\\\server\\share\\proj\\x.py",
                 "\\\\?\\C:\\Proj": "\\\\?\\c:\\proj\\x.py"}
        for root, inside in cases.items():
            with self.subTest(root=root):
                prefix = core._root_prefix(root, ntpath)
                self.assertTrue(ntpath.normcase(inside).startswith(prefix))
                self.assertFalse(ntpath.normcase(root.rstrip("\\") + "-other\\x.py").startswith(prefix))


if __name__ == "__main__":
    unittest.main()
