"""Equivalence of capture and inspect before and after optimizations P1/P2.

`reference_capture` is a verbatim copy of core.capture from 1.0.0, computing
the redacted text of every file without any cache. The optimized capture must
return byte-identical results (or the same error) for the same tree, and
inspect must produce the same status, hashes and changes whether or not the
redacted text of unchanged files is taken from the approved baseline (P1).
"""
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mcp_sentry_gateway import core
from fixture_cleanup import remove_fixture
from mcp_sentry_gateway.core import (EXCLUDED_CAPTURE_PARTS, SentryError, approve, canon, digest,
                                     inspect, load, safe_text)


def reference_capture(manifest_path, roots_override=None, *, allow_missing=False):
    manifest, root = load(manifest_path); roots = roots_override or manifest["inspect_roots"]
    manifest_raw = manifest_path.read_bytes()
    files = [{"path":"@manifest", "sha256":digest(manifest_raw), "content":safe_text(manifest_raw)}]
    seen=set(); missing=[]
    for item in roots:
        candidate=(root/item).resolve()
        if not (candidate == root or root in candidate.parents): raise SentryError("raiz de inspeção escapa project_root")
        if any(part in EXCLUDED_CAPTURE_PARTS for part in Path(item).parts):
            raise SentryError("raiz de inspeção inclui ambiente virtual ou cache")
        found = [candidate] if candidate.is_file() else sorted(x for x in candidate.rglob("*") if x.is_file())
        if not found:
            if not allow_missing:
                raise SentryError(f"raiz vazia ou inexistente: {item}")
            missing.append(item)
            continue
        for file in found:
            relative = file.relative_to(root)
            if any(part in EXCLUDED_CAPTURE_PARTS for part in relative.parts) or file.suffix.lower() in {".pyc", ".pyo"}:
                continue
            if file.name.startswith(".env") or file.name.lower() in {"credentials.json", "token.json", "client_secret.json"}:
                raise SentryError("retire credenciais das raízes inspecionadas")
            resolved_file = file.resolve()
            if not (resolved_file == root or root in resolved_file.parents):
                raise SentryError("arquivo inspecionado escapa project_root")
            if file in seen: continue
            seen.add(file); raw=file.read_bytes(); sha256=digest(raw)
            files.append({"path":file.relative_to(root).as_posix(), "sha256":sha256, "content":safe_text(raw)})
    result = {"manifest":manifest, "root":str(root), "files":sorted(files, key=lambda x:x["path"])}
    if missing:
        result["missing_roots"] = missing
    return result


SECRET_SOURCE = 'API_KEY = "sk-live-123456"\npassword: "hunter2"\nprint("ok")\n'


def make_link(link: Path, target: Path, directory: bool):
    if directory:
        try:
            import _winapi
            _winapi.CreateJunction(str(target), str(link))
            return
        except (ImportError, AttributeError, OSError):
            pass
    link.symlink_to(target, target_is_directory=directory)


class CaptureEquivalenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = Path(tempfile.mkdtemp(prefix="mcp-sentry-capture-test-", dir=Path(__file__).parent))
        self.addCleanup(remove_fixture, self.temp)
        self.project = self.temp / "server"
        self.outside = self.temp / "outside"
        for folder in (self.project / "pkg" / "sub", self.project / "__pycache__", self.project / "pkg" / ".cache",
                       self.project / "empty", self.outside):
            folder.mkdir(parents=True)
        (self.project / "server.py").write_bytes(b"import pkg\r\nprint('crlf')\r\n")
        (self.project / "pkg" / "__init__.py").write_bytes(SECRET_SOURCE.encode())
        (self.project / "pkg" / "sub" / "deep.js").write_bytes("const token = 'abc';\nconsole.log('ção');\n".encode())
        (self.project / "pkg" / "binary.bin").write_bytes(bytes(range(256)))
        (self.project / "pkg" / "cached.pyc").write_bytes(b"compiled")
        (self.project / "__pycache__" / "x.pyc").write_bytes(b"compiled")
        (self.project / "pkg" / ".cache" / "c.txt").write_bytes(b"cache")
        (self.project / "notes.md").write_bytes("-----BEGIN RSA PRIVATE KEY-----\nAAAA\n-----END RSA PRIVATE KEY-----\n".encode())
        self.manifest = self.temp / "manifest.json"
        self.state = self.temp / "state"
        self.data = {"manifest_version": 1, "project_root": "server",
                     "inspect_roots": ["server.py", "pkg", "notes.md", "pkg/__init__.py"],
                     "metadata": {"tools": []}, "configuration": {"command": ["python", "server.py"], "cwd": "."}}
        self.save()

    def save(self):
        self.manifest.write_text(json.dumps(self.data), encoding="utf-8")

    def clear_cache(self):
        with core._TEXT_CACHE_LOCK:
            core._TEXT_CACHE.clear()
            core._TEXT_CACHE_BYTES = 0

    def assert_same_capture(self, **kwargs):
        for warm in (False, True):
            if not warm:
                self.clear_cache()
            try:
                expected = canon(reference_capture(self.manifest, **kwargs))
            except SentryError as exc:
                with self.assertRaisesRegex(SentryError, str(exc)):
                    core.capture(self.manifest, **kwargs)
                continue
            self.assertEqual(canon(core.capture(self.manifest, **kwargs)), expected)

    def test_tree_with_nested_binary_excluded_and_duplicate_entries(self):
        self.assert_same_capture()

    def test_roots_override_and_missing_roots(self):
        self.assert_same_capture(roots_override=["pkg/sub", "missing"], allow_missing=True)
        self.assert_same_capture(roots_override=["missing"])
        self.assert_same_capture(roots_override=["empty"], allow_missing=True)

    def test_rejections_are_identical(self):
        cases = {
            "credential": lambda: (self.project / "pkg" / "credentials.json").write_text("{}"),
            "env": lambda: (self.project / "pkg" / ".env.local").write_text("A=1"),
            "escaping root": lambda: self.data.update(inspect_roots=["../outside"]),
            "excluded root": lambda: self.data.update(inspect_roots=["__pycache__"]),
        }
        for name, change in cases.items():
            with self.subTest(case=name):
                self.setUp()
                change(); self.save()
                self.assert_same_capture()

    def test_links_inside_and_outside_project(self):
        cases = {  # name: (link inside pkg, target relative to temp, is directory)
            "file link inside": ("alias.py", "server/server.py", False),
            "file link outside": ("alias.py", "outside/outside.py", False),
            "folder link inside": ("alias", "server/pkg/sub", True),
            "folder link outside": ("alias", "outside/pkgdir", True),
            "folder link to sibling sharing the name prefix": ("alias", "server-other", True),
        }
        for name, (link, target, directory) in cases.items():
            with self.subTest(case=name):
                self.setUp()
                (self.outside / "outside.py").write_bytes(b"outside = True\n")
                (self.outside / "pkgdir").mkdir()
                (self.outside / "pkgdir" / "m.py").write_bytes(b"m = 1\n")
                (self.temp / "server-other").mkdir()
                (self.temp / "server-other" / "n.py").write_bytes(b"n = 1\n")
                try:
                    make_link(self.project / "pkg" / link, self.temp / target, directory)
                except (OSError, NotImplementedError) as exc:
                    self.skipTest(f"links unavailable: {exc}")
                self.assert_same_capture()


class InspectEquivalenceTests(CaptureEquivalenceTests):
    """P1: the approved text of unchanged files may replace recomputation."""

    def run_inspect(self, *, cold):
        if cold:
            self.clear_cache()
        result = inspect(self.manifest, self.state)
        return {"status": result["status"], "dossier": result["dossier"]}

    def assert_same_inspect(self):
        with unittest.mock.patch.object(core, "capture", reference_capture):
            expected = self.run_inspect(cold=True)
        for cold in (True, False):
            with self.subTest(cold=cold):
                self.assertEqual(canon(self.run_inspect(cold=cold)), canon(expected))

    def test_unchanged_version(self):
        approve(self.manifest, self.state)
        self.assert_same_inspect()

    def test_changed_added_and_removed_files_with_secrets(self):
        approve(self.manifest, self.state)
        (self.project / "pkg" / "__init__.py").write_bytes((SECRET_SOURCE + 'secret = "new-value"\n').encode())
        (self.project / "pkg" / "sub" / "new.js").write_bytes(b"const apiKey = 'zzz';\n")
        (self.project / "notes.md").unlink()
        self.assert_same_inspect()

    def test_changed_manifest_and_missing_root(self):
        approve(self.manifest, self.state)
        self.data["inspect_roots"].append("missing")
        self.data["metadata"]["tools"] = [{"name": "new_tool"}]
        self.save()
        self.assert_same_inspect()

    def test_file_moved_to_identical_bytes_elsewhere(self):
        approve(self.manifest, self.state)
        (self.project / "pkg" / "copy.py").write_bytes(SECRET_SOURCE.encode())
        self.assert_same_inspect()

    # Capture-only cases already ran in the parent class; avoid repeating them here.
    test_tree_with_nested_binary_excluded_and_duplicate_entries = None
    test_roots_override_and_missing_roots = None
    test_rejections_are_identical = None
    test_links_inside_and_outside_project = None


import unittest.mock  # noqa: E402  (used by InspectEquivalenceTests)

if __name__ == "__main__":
    unittest.main()
