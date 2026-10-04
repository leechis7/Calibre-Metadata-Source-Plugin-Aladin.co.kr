#!/usr/bin/env python
"""Build deterministic, standalone Calibre plugin archives."""
import argparse
import ast
import hashlib
from pathlib import Path
import zipfile

ROOT_DIR = Path(__file__).resolve().parents[1]
DIST_DIR = ROOT_DIR / 'dist'
PLUGIN_CONFIGS = {'aladin': ('Aladin', 'aladin_co_kr'), 'yes24': ('YES24', 'yes24_com'),
                  'kyobo': ('Kyobo', 'kyobobook_co_kr')}


def get_plugin_version(path):
    tree = ast.parse(Path(path).read_text(encoding='utf-8'))
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'version' for t in node.targets):
            value = ast.literal_eval(node.value)
            if isinstance(value, tuple) and len(value) == 3 and all(type(v) is int and v >= 0 for v in value):
                return '.'.join(map(str, value))
    raise ValueError('Missing valid version in ' + str(path))


def build_plugin(key, output_dir=None):
    display, namespace = PLUGIN_CONFIGS[key]
    plugin_dir = ROOT_DIR / 'plugins' / key
    version = get_plugin_version(plugin_dir / '__init__.py')
    marker = 'plugin-import-name-' + namespace + '.txt'
    if not (plugin_dir / marker).is_file():
        raise ValueError('Missing plugin marker: ' + marker)
    files = {}
    for path in sorted((ROOT_DIR / 'shared').glob('*.py')):
        files[path.name] = path
    for path in sorted(plugin_dir.rglob('*')):
        relative = path.relative_to(plugin_dir)
        if not path.is_file() or any(p.startswith('.') or p == '__pycache__' for p in relative.parts) or path.suffix in ('.pyc', '.pyo'):
            continue
        name = relative.as_posix()
        if name in files:
            raise ValueError('Shared/plugin file collision: ' + name)
        files[name] = path
    files['LICENSE'] = ROOT_DIR / 'LICENSE'
    for name, path in files.items():
        if name.endswith('.py'):
            compile(path.read_bytes(), name, 'exec')
    output_dir = Path(output_dir or DIST_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)
    destination = output_dir / ('Calibre-Metadata-Plugin-%s-v%s.zip' % (display, version))
    temporary = destination.with_suffix('.zip.tmp')
    with zipfile.ZipFile(temporary, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name, path in sorted(files.items()):
            info = zipfile.ZipInfo(name, (2020, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, path.read_bytes())
    temporary.replace(destination)
    print('Built ' + destination.name)
    return destination


def build_all(targets=None, output_dir=None):
    targets = list(targets or PLUGIN_CONFIGS)
    if len(targets) == len(PLUGIN_CONFIGS):
        versions = {get_plugin_version(ROOT_DIR / 'plugins' / key / '__init__.py') for key in targets}
        if len(versions) != 1:
            raise ValueError('All plugins must have the same release version')
    paths = [build_plugin(key, output_dir) for key in targets]
    manifest = paths[0].parent / 'SHA256SUMS.txt'
    manifest.write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest() + '  ' + p.name + '\n' for p in paths), encoding='utf-8')
    return paths


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('target', nargs='?', choices=['all'] + list(PLUGIN_CONFIGS), default='all')
    parser.add_argument('--output-dir', type=Path)
    args = parser.parse_args()
    build_all(None if args.target == 'all' else [args.target], args.output_dir)


if __name__ == '__main__':
    main()
