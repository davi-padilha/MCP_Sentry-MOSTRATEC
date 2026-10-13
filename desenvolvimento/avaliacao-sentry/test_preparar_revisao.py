"""Preparation regression tests; real Git, disposable code/state, no approvals."""
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import preparar_revisao as preparador


class PreparationTests(unittest.TestCase):
    def test_lf_patch_ignores_inherited_windows_autocrlf_and_restore_is_exact(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
            root = Path(directory)
            config = {
                "servidores": {"G": {"nome": "git", "codigo": str(root / "code"),
                                     "estado": str(root / "state")}},
                "fotografias": str(root / "photos"), "patches": str(root / "patches"),
                "evidencias": str(root / "evidence"), "registro": str(root / "register.csv"),
            }
            code, state = root / "code", root / "state"
            code.mkdir(); state.mkdir(); (root / "patches").mkdir()
            original = b"first\nsecond\nthird\n"
            (code / "server.py").write_bytes(original)
            (state / preparador.APPROVED_VERSION_FILE).write_text("{}")
            preparador.snapshot(config, "G")
            (root / "patches/G1.patch").write_bytes(
                b"diff --git a/server.py b/server.py\n--- a/server.py\n+++ b/server.py\n"
                b"@@ -1,3 +1,4 @@\n first\n second\n+added\n third\n")
            inherited = {"GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": "core.autocrlf",
                         "GIT_CONFIG_VALUE_0": "true", "GIT_CEILING_DIRECTORIES": str(root)}
            with patch.dict(os.environ, inherited):
                result = preparador.prepare(config, "G1", "R1")
            self.assertEqual((code / "server.py").read_bytes(), b"first\nsecond\nadded\nthird\n")
            self.assertEqual(result["patch_sha256"], preparador.sha256(root / "patches/G1.patch"))
            (state / "previous-review.json").write_text("{}")
            preparador.restore(config, "G")
            self.assertEqual((code / "server.py").read_bytes(), original)
            self.assertFalse((state / "previous-review.json").exists())
            patch_file = root / "patches/G1.patch"
            patch_file.write_bytes(patch_file.read_bytes().replace(b"\n", b"\r\n"))
            (code / "server.py").write_bytes(b"do not restore on invalid input\n")
            with self.assertRaisesRegex(preparador.PreparoError, "LF"):
                preparador.prepare(config, "G1", "R2")
            self.assertEqual((code / "server.py").read_bytes(), b"do not restore on invalid input\n")

    def test_draw_contains_two_reviews_of_all_24_versions(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
            config = {"servidores": {key: {} for key in "FGD"}, "evidencias": directory}
            first = preparador.draw_order(config, 20261005)
            raw = Path(first["arquivo"]).read_bytes()
            preparador.draw_order(config, 20261005)
            self.assertEqual(Path(first["arquivo"]).read_bytes(), raw)
            self.assertEqual(first["revisoes"], 48)
            import csv
            with Path(first["arquivo"]).open(newline="", encoding="utf-8") as stream:
                rows = list(csv.DictReader(stream))
            self.assertEqual(len({(x["versao"], x["repeticao"]) for x in rows}), 48)
            self.assertEqual({x["versao"] for x in rows},
                             {f"{p}{n}" for p in "FGD" for n in range(1, 9)})


if __name__ == "__main__":
    unittest.main()
