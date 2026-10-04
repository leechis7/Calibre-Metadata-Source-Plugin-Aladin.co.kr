"""Load pure adapters from built ZIPs in separate calibre_plugins namespaces."""
import importlib.util
from pathlib import Path
import sys
import tempfile
import types
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from build import build_all

TEMP = tempfile.TemporaryDirectory()
ARCHIVES = build_all(output_dir=Path(TEMP.name))
parent = types.ModuleType('calibre_plugins')
parent.__path__ = []
sys.modules.setdefault('calibre_plugins', parent)


def load_adapter(store):
    names = {'yes24': 'yes24_com', 'kyobo': 'kyobobook_co_kr', 'aladin': 'aladin_co_kr'}
    name = 'calibre_plugins.' + names[store]
    folder = Path(TEMP.name) / store
    folder.mkdir(exist_ok=True)
    archive = next(p for p in ARCHIVES if ('-' + {'yes24':'YES24', 'kyobo':'Kyobo', 'aladin':'Aladin'}[store] + '-') in p.name)
    with zipfile.ZipFile(archive) as zf:
        zf.extractall(folder)
    package = types.ModuleType(name)
    package.__path__ = [str(folder)]
    sys.modules[name] = package
    return __import__(name + '.worker', fromlist=['worker'])


def fixture(name):
    return (ROOT / 'tests/fixtures' / name).read_text(encoding='utf-8')
