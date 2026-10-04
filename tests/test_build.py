import hashlib
from pathlib import Path
import tempfile
import unittest
import zipfile
from support import ARCHIVES, ROOT, build_all


class BuildTests(unittest.TestCase):
    def test_standalone_structure_and_namespaces(self):
        namespaces = set()
        for path in ARCHIVES:
            with zipfile.ZipFile(path) as zf:
                self.assertIsNone(zf.testzip())
                names = zf.namelist()
                self.assertIn('__init__.py', names)
                self.assertIn('LICENSE', names)
                self.assertIn('text_cleaner.py', names)
                markers = [n for n in names if n.startswith('plugin-import-name-')]
                self.assertEqual(len(markers), 1)
                namespaces.add(markers[0])
                self.assertFalse(any('\\' in n or '__pycache__' in n for n in names))
                for name in names:
                    if name.endswith('.py'):
                        compile(zf.read(name), name, 'exec')
        self.assertEqual(len(namespaces), 3)

    def test_reproducible(self):
        with tempfile.TemporaryDirectory() as folder:
            rebuilt = build_all(output_dir=Path(folder))
            self.assertEqual([hashlib.sha256(p.read_bytes()).hexdigest() for p in ARCHIVES],
                             [hashlib.sha256(p.read_bytes()).hexdigest() for p in rebuilt])
