#!/usr/bin/env python
"""Build and publish three ZIPs with GitHub CLI. Preview unless --publish is passed."""
import argparse
import subprocess

from build import ROOT_DIR, build_all, get_plugin_version


def run(*args, capture=False):
    return subprocess.run(args, cwd=ROOT_DIR, check=True, text=True,
                          stdout=subprocess.PIPE if capture else None).stdout


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--publish', action='store_true')
    parser.add_argument('--draft', action='store_true')
    args = parser.parse_args()
    tag = 'v' + get_plugin_version(ROOT_DIR / 'plugins/aladin/__init__.py')
    paths = build_all()
    print('Release: ' + tag)
    for path in paths:
        print('  ' + str(path))
    if not args.publish:
        print('Preview only. Run with --publish [--draft] to upload.')
        return
    if run('git', 'status', '--porcelain', capture=True).strip():
        raise SystemExit('Commit the reviewed changes before publishing a release.')
    run('git', 'rev-parse', '--verify', 'refs/tags/' + tag, capture=True)
    if run('git', 'rev-list', '-n', '1', tag, capture=True).strip() != run('git', 'rev-parse', 'HEAD', capture=True).strip():
        raise SystemExit('Release tag must point to the tested HEAD commit.')
    run('git', 'fetch', 'origin', 'tag', tag)
    run('gh', 'auth', 'status')
    command = ['gh', 'release', 'create', tag, '--verify-tag', '--title', 'Korean Metadata Sources ' + tag,
               '--notes-file', str(ROOT_DIR / 'release-notes.md')]
    if args.draft:
        command.append('--draft')
    command.extend(str(path) for path in paths)
    command.append(str(paths[0].parent / 'SHA256SUMS.txt'))
    run(*command)


if __name__ == '__main__':
    main()
