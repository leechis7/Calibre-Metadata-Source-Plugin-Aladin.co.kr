"""Run built ZIPs with calibre-debug and a separate test configuration.

Set CALIBRE_CONFIG_DIRECTORY to a folder inside this repository before running.
This script uses the real Calibre loader, browser, Metadata and HTML sanitizer.
"""
import argparse
import importlib.util
import os
from pathlib import Path
from queue import Queue
from threading import Event

spec = importlib.util.spec_from_file_location('korean_plugin_build', Path(__file__).with_name('build.py'))
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)
PLUGIN_CONFIGS, ROOT_DIR, get_plugin_version = build.PLUGIN_CONFIGS, build.ROOT_DIR, build.get_plugin_version


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--store', choices=['all'] + list(PLUGIN_CONFIGS), default='all')
    parser.add_argument('--title', default='트렌드 코리아 2027')
    parser.add_argument('--isbn', default='9791124073483')
    parser.add_argument('--author', action='append', default=[], help='Author to include in title searches.')
    parser.add_argument('--allow-missing-toc', action='store_true', help='Some foreign titles have no YES24 table of contents.')
    args = parser.parse_args()
    configured = os.environ.get('CALIBRE_CONFIG_DIRECTORY')
    if not configured or not Path(configured).resolve().is_relative_to(ROOT_DIR):
        raise SystemExit('Set CALIBRE_CONFIG_DIRECTORY to a separate test folder inside this repository.')

    from calibre.constants import __version__, config_dir
    from calibre.customize.ui import add_plugin, metadata_plugins
    from calibre.utils.logging import ThreadSafeLog
    if Path(config_dir).resolve() != Path(configured).resolve():
        raise SystemExit('Calibre is not using the requested test configuration.')
    names = []
    for store, (label, _) in PLUGIN_CONFIGS.items():
        if args.store not in ('all', store):
            continue
        version = get_plugin_version(ROOT_DIR / 'plugins' / store / '__init__.py')
        archive = ROOT_DIR / 'dist' / f'Calibre-Metadata-Plugin-{label}-v{version}.zip'
        source = add_plugin(str(archive))
        names.append(source.name)
    print('Calibre', __version__, flush=True)
    for source in metadata_plugins(['identify']):
        if source.name not in names:
            continue
        for title, identifiers in ((args.title, {}), (None, {'isbn': args.isbn})):
            q, log = Queue(), ThreadSafeLog()
            source.identify(log, q, Event(), title=title, authors=args.author if title else None, identifiers=identifiers, timeout=30)
            rows = []
            while not q.empty():
                rows.append(q.get_nowait())
            mi = next((m for m in rows if m.isbn == args.isbn), None)
            # Calibre's bundled interpreter can run with assertions disabled.
            if mi is None:
                raise RuntimeError('Expected metadata missing: %s %r' % (source.name, [(m.title, m.isbn) for m in rows]))
            if not mi.authors or not mi.publisher or not mi.comments:
                raise RuntimeError('Incomplete metadata: ' + source.name)
            if not args.allow_missing_toc:
                if '목차' not in mi.comments:
                    raise RuntimeError('Missing table of contents: ' + source.name)
            covers = Queue()
            source.download_cover(log, covers, Event(), identifiers=mi.identifiers, timeout=30)
            _, raw = covers.get_nowait()
            if not raw.startswith((b'\xff\xd8', b'\x89PNG', b'RIFF', b'GIF')):
                raise RuntimeError('Invalid cover: ' + source.name)
            print(f'{source.name} {"title" if title else "ISBN"}: {mi.title} / {mi.isbn} / cover {len(raw)} bytes / OK', flush=True)


if __name__ == '__main__':
    main()
