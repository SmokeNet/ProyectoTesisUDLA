import hashlib
import tempfile
import unittest
from pathlib import Path

from observability.evidence import EvidenceStore


class EvidenceTests(unittest.TestCase):
    def test_json_html_y_hash_verificable(self):
        with tempfile.TemporaryDirectory() as directory:
            store = EvidenceStore(Path(directory))
            artifact = store.write_json("evento-1", {"estado_antes": "caido", "estado_despues": "ok"})
            report = store.write_html_report("evento-1", {"diagnostico": "<script>alert(1)</script>"})
            self.assertEqual(artifact.sha256, hashlib.sha256(artifact.path.read_bytes()).hexdigest())
            self.assertIn("&lt;script&gt;", report.path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
