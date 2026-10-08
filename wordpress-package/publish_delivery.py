#!/usr/bin/env python3
"""Publish only verified final artifacts, preserving checkout/main and its index."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
BRANCH = 'bixie-wordpress-download'


def git(*args, env=None, input=None):
    return subprocess.check_output(['git', *args], cwd=REPO, env=env, input=input, text=True).strip()


def checked_files(directory, rows):
    paths = []
    for row in rows:
        filename = row['file']
        if Path(filename).name != filename or not filename.endswith('.zip'):
            raise ValueError('Delivery filenames must be single safe ZIP names.')
        path = directory / filename
        if path.is_symlink() or not path.is_file() or not 0 < path.stat().st_size < 95 * 1024 * 1024:
            raise ValueError('Every Git delivery artifact must be a regular file below95MiB.')
        if path.stat().st_size != row['bytes'] or hashlib.sha256(path.read_bytes()).hexdigest() != row['sha256']:
            raise ValueError('Actual artifact size/SHA differs from delivery manifest.')
        paths.append(str(path.relative_to(REPO)))
    return paths


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage', choices=['media', 'code'], required=True)
    args = parser.parse_args()
    catalog = json.loads((ROOT / 'content/catalog.json').read_text())
    audit = json.loads((ROOT / 'tests/production-media-report.json').read_text())
    if len(catalog['looks']) != 154 or catalog['counts']['provided_unique_primary_collection_images'] != 462 or catalog['counts']['provided_approved_home_role_images'] != 25 or audit['status'] != 'verified_complete_assets':
        raise ValueError('Final publication requires the actual completed154-look/487-photo audit.')
    media = REPO / 'wordpress-media-release'
    media_manifest = json.loads((media / 'media-download-manifest.json').read_text())
    if media_manifest['actual_approved_media_records'] != 488 or media_manifest['actual_complete_look_records'] != 154:
        raise ValueError('Final media must contain487 actual photographs and one reviewed movie.')
    paths = checked_files(media, media_manifest['parts'])
    paths += [str((media / name).relative_to(REPO)) for name in ['media-download-manifest.json', 'SHA256SUMS.txt']]
    if args.stage == 'code':
        code = REPO / 'wordpress-release'
        release = json.loads((code / 'release-manifest.json').read_text())
        if release['release_state'] != 'assets_complete_target_host_checks_required':
            raise ValueError('Incomplete engineering ZIPs cannot enter final download publication.')
        paths += checked_files(code, release['artifacts'])
        paths += [str(p.relative_to(REPO)) for p in sorted(code.glob('*.md'))]
        paths += [str((code / name).relative_to(REPO)) for name in ['release-manifest.json', 'SHA256SUMS.txt']]
        index = json.loads((ROOT / 'plugin/bixie-library/content/release-index.json').read_text())
        expected = {(row['file'], row['sha256'], row['bytes']) for row in media_manifest['parts']}
        actual = {(row['url'].rsplit('/', 1)[-1], row['sha256'], row['bytes']) for row in index['parts']}
        if expected != actual:
            raise ValueError('The final plugin media index does not match actual verified parts.')
    existing = git('ls-remote', '--heads', 'origin', BRANCH)
    if existing:
        parent = existing.split()[0]
        try:
            git('cat-file', '-e', parent + '^{commit}')
        except subprocess.CalledProcessError:
            git('fetch', 'origin', BRANCH)
    else:
        parent = git('rev-parse', 'HEAD')
    head = git('rev-parse', 'HEAD')
    normal_index = REPO / '.git/index'
    previous_index = normal_index.read_bytes() if normal_index.is_file() else None
    with tempfile.TemporaryDirectory(prefix='bixie-final-delivery-', dir='/tmp') as temporary:
        env = dict(os.environ, GIT_INDEX_FILE=str(Path(temporary) / 'index'))
        git('read-tree', parent, env=env)
        # Replace only this task's generated delivery directories in the temporary
        # index. Retain unrelated branch files and all normal checkout changes.
        git('rm', '-r', '--cached', '--ignore-unmatch', '--', 'wordpress-media-release', 'wordpress-release', env=env)
        git('add', '--', *paths, env=env)
        tracked = git('ls-files', env=env).splitlines()
        for relative in tracked:
            if relative.startswith(('wordpress-media-release/', 'wordpress-release/')) and relative not in paths:
                raise ValueError('An unselected delivery file entered the final index.')
        tree = git('write-tree', env=env)
        commit = git('commit-tree', tree, '-p', parent, input='Publish verified final Bixie WordPress ' + args.stage + ' artifacts\n')
        git('push', 'origin', commit + ':refs/heads/' + BRANCH)
        git('update-ref', 'refs/heads/' + BRANCH, commit)
    assert git('rev-parse', 'HEAD') == head
    assert (normal_index.read_bytes() if normal_index.is_file() else None) == previous_index
    report = {'stage': args.stage, 'branch': BRANCH, 'commit': commit, 'checkout_head_preserved': head, 'normal_index_preserved': True, 'selected_files': paths,
              'full_zip_url': 'https://codeload.github.com/imahmad-malik/check.txt/zip/' + commit}
    (REPO / ('wordpress-final-' + args.stage + '-publish.json')).write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
