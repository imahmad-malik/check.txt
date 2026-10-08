#!/usr/bin/env python3
"""Publish the explicitly incomplete, verified saved WordPress checkpoint."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

from publish_delivery import checked_files, git

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
BRANCH = 'bixie-wordpress-saved-download'
SCOPE = 'engineering_installable_media_incomplete'
EXPECTED = {'looks': 128, 'photos': 422, 'films': 1, 'uniqueSourceSHA256': 423}


def read_json(path):
    if path.is_symlink() or not path.is_file():
        raise ValueError('A delivery input must be an actual regular file: ' + str(path))
    return json.loads(path.read_text())


def digest(data):
    return hashlib.sha256(data).hexdigest()


def metadata_file(path):
    if path.is_symlink() or not path.is_file() or path.stat().st_size >= 10 * 1024 * 1024:
        raise ValueError('Delivery metadata must be a regular small file.')
    return str(path.relative_to(REPO))


def publication_inputs():
    catalog = read_json(ROOT / 'content/catalog.json')
    progress = read_json(ROOT / 'media/progress.json')['counts']
    audit = read_json(ROOT / 'tests/production-media-report.json')
    if (len(catalog['looks']) != 128
            or catalog['counts']['provided_unique_primary_collection_images'] != 384
            or catalog['counts']['provided_approved_home_role_images'] != 25
            or progress['reviewed_approved_production_photos'] != 422
            or progress['collections_completed'] != 16
            or audit.get('status') != 'verified_partial_assets'
            or audit.get('actual_complete_looks') != 128
            or not audit.get('checks')
            or any(check.get('passed') is not True for check in audit['checks'])):
        raise ValueError('This saved publication requires the actual audited 128-look incomplete checkpoint.')
    directory = REPO / 'wordpress-media-release'
    manifest = read_json(directory / 'media-download-manifest.json')
    if (manifest.get('status') != 'built'
            or manifest.get('actual_approved_media_records') != 423
            or manifest.get('actual_complete_look_records') != 128
            or len(manifest.get('parts', [])) != 33):
        raise ValueError('Expected 33 actual saved parts with 422 photographs and one film.')
    expected_names = ['bixie-saved-20261008-' + str(i).zfill(3) + '.zip' for i in range(1, 34)]
    if [part['file'] for part in manifest['parts']] != expected_names:
        raise ValueError('Only the exact saved-checkpoint parts may be published.')
    if any(part['bytes'] > 25 * 1024 * 1024 for part in manifest['parts']):
        raise ValueError('A saved part exceeds the actual importer part size bound.')
    paths = checked_files(directory, manifest['parts'])
    paths += [metadata_file(directory / name) for name in ['media-download-manifest.json', 'SHA256SUMS.txt']]
    expected_sums = ''.join(f"{part['sha256']}  {part['file']}\n" for part in manifest['parts'])
    if (directory / 'SHA256SUMS.txt').read_text() != expected_sums:
        raise ValueError('Media checksum text disagrees with the actual media manifest.')
    return manifest, paths


def pin_index(manifest):
    published = read_json(REPO / 'wordpress-saved-media-publish.json')
    commit = published.get('commit', '')
    if (published.get('stage') != 'media' or published.get('release_scope') != SCOPE
            or not re.fullmatch(r'[0-9a-f]{40}', commit)):
        raise ValueError('An actual immutable saved media publication is required.')
    rows = []
    for part in manifest['parts']:
        relative = 'wordpress-media-release/' + part['file']
        if relative not in published['selected_files']:
            raise ValueError('Media part is absent from the actual saved publication.')
        data = subprocess.check_output(['git', 'show', commit + ':' + relative], cwd=REPO)
        if len(data) != part['bytes'] or digest(data) != part['sha256']:
            raise ValueError('Published Git bytes differ from the saved media manifest.')
        rows.append({'bundle_id': part['file'][:-4],
                     'url': 'https://raw.githubusercontent.com/imahmad-malik/check.txt/' + commit + '/' + relative,
                     'sha256': part['sha256'], 'bytes': part['bytes']})
    index = {'version': 1, 'release': 'bixie-saved-' + commit[:12], 'parts': rows}
    (ROOT / 'plugin/bixie-library/content/release-index.json').write_text(json.dumps(index, indent=2) + '\n')
    result = {'status': 'pinned_to_actual_saved_media_publication', 'release_scope': SCOPE,
              'commit': commit, 'verified_parts': len(rows), 'total_bytes': sum(row['bytes'] for row in rows)}
    print(json.dumps(result, indent=2))


def check_code(manifest, paths):
    code = REPO / 'wordpress-release'
    release = read_json(code / 'release-manifest.json')
    if (release.get('release_state') != SCOPE or release.get('complete_launch_looks') != 128
            or release.get('gallery_photographs') != 384 or release.get('homepage_photographs') != 25
            or release.get('completed_movies') != 1):
        raise ValueError('The saved code artifacts must clearly identify the incomplete actual checkpoint.')
    acceptance = read_json(ROOT / 'tests/wp-saved-acceptance-report.json')
    if (acceptance.get('passed') is not True or acceptance.get('release_scope') != SCOPE
            or any(acceptance.get('actual_counts', {}).get(key) != value for key, value in EXPECTED.items())):
        raise ValueError('Actual saved-checkpoint WordPress acceptance is required; pilot/final evidence cannot substitute.')
    if not acceptance.get('supporting_reports'):
        raise ValueError('Actual saved-checkpoint acceptance must identify its supporting checks.')
    for filename in acceptance['supporting_reports']:
        if Path(filename).name != filename or read_json(ROOT / 'tests' / filename).get('passed') is not True:
            raise ValueError('A required saved-checkpoint runtime report is missing or failing.')
    tested = acceptance.get('tested_archives', {})
    for row in release['artifacts']:
        if row['file'] in {'bixie-editorial.zip', 'bixie-library.zip'} and tested.get(row['file']) != row['sha256']:
            raise ValueError('An installable ZIP differs from the ZIP actually installed and tested.')
    for row in manifest['parts']:
        if tested.get(row['file']) != row['sha256']:
            raise ValueError('A saved media part differs from the actual owner GUI upload test.')
    archive = read_json(ROOT / 'tests/release-archive-report.json')
    if archive.get('status') != 'passed' or archive.get('release_state') != SCOPE:
        raise ValueError('Saved release archive checks must pass before publishing code.')
    index = read_json(ROOT / 'plugin/bixie-library/content/release-index.json')
    media_published = read_json(REPO / 'wordpress-saved-media-publish.json')
    commit = media_published['commit']
    expected = {(row['file'], row['sha256'], row['bytes']) for row in manifest['parts']}
    actual = {(row['url'].rsplit('/', 1)[-1], row['sha256'], row['bytes']) for row in index['parts']}
    prefix = 'https://raw.githubusercontent.com/imahmad-malik/check.txt/' + commit + '/wordpress-media-release/'
    if expected != actual or any(row['url'] != prefix + row['bundle_id'] + '.zip' for row in index['parts']):
        raise ValueError('The saved plugin media index must pin exactly the actual saved media commit.')
    paths += checked_files(code, release['artifacts'])
    paths += [metadata_file(path) for path in sorted(code.glob('*.md'))]
    paths += [metadata_file(code / name) for name in ['release-manifest.json', 'SHA256SUMS.txt']]
    expected_sums = ''.join(f"{part['sha256']}  {part['file']}\n" for part in release['artifacts'])
    if (code / 'SHA256SUMS.txt').read_text() != expected_sums:
        raise ValueError('Code checksum text disagrees with the actual release manifest.')
    return paths


def publish(stage, paths):
    expected = [{'path': relative, 'bytes': (REPO / relative).stat().st_size,
                 'sha256': digest((REPO / relative).read_bytes())} for relative in paths]
    existing = git('ls-remote', '--heads', 'origin', BRANCH)
    parent = existing.split()[0] if existing else git('rev-parse', 'HEAD')
    if existing:
        try:
            git('cat-file', '-e', parent + '^{commit}')
        except subprocess.CalledProcessError:
            git('fetch', 'origin', BRANCH)
    head = git('rev-parse', 'HEAD')
    normal_index = REPO / '.git/index'
    previous_index = normal_index.read_bytes() if normal_index.is_file() else None
    with tempfile.TemporaryDirectory(prefix='bixie-saved-delivery-', dir='/tmp') as temporary:
        env = dict(os.environ, GIT_INDEX_FILE=str(Path(temporary) / 'index'))
        git('read-tree', parent, env=env)
        # This private index holds the previous delivery tree, which can differ
        # from both checkout HEAD and newly rebuilt files. Replace those cached
        # entries without touching the worktree or the normal Git index.
        git('rm', '-r', '-f', '--cached', '--ignore-unmatch', '--', 'wordpress-media-release', 'wordpress-release', env=env)
        git('add', '--', *paths, env=env)
        tracked = git('ls-files', env=env).splitlines()
        if any(relative.startswith(('wordpress-media-release/', 'wordpress-release/')) and relative not in paths for relative in tracked):
            raise ValueError('An unselected delivery file entered the saved index.')
        tree = git('write-tree', env=env)
        commit = git('commit-tree', tree, '-p', parent, input='Publish verified incomplete Bixie WordPress saved ' + stage + ' checkpoint\n')
        for row in expected:
            data = subprocess.check_output(['git', 'show', commit + ':' + row['path']], cwd=REPO)
            if len(data) != row['bytes'] or digest(data) != row['sha256']:
                raise ValueError('Actual staged Git bytes differ from the checked delivery inputs.')
        # ZIP parts are already compressed. Avoid spending CPU searching for
        # deltas between unrelated archives; this affects only this command.
        git('-c', 'pack.window=0', '-c', 'core.compression=1', 'push', 'origin', commit + ':refs/heads/' + BRANCH)
        git('update-ref', 'refs/heads/' + BRANCH, commit)
    if git('rev-parse', 'HEAD') != head or (normal_index.read_bytes() if normal_index.is_file() else None) != previous_index:
        raise RuntimeError('Saved publication unexpectedly changed the checkout or normal index.')
    report = {'stage': stage, 'release_scope': SCOPE, 'branch': BRANCH, 'commit': commit,
              'actual_counts': EXPECTED, 'checkout_head_preserved': head, 'normal_index_preserved': True,
              'selected_files': paths, 'published_files': expected,
              'full_zip_url': 'https://codeload.github.com/imahmad-malik/check.txt/zip/' + commit}
    (REPO / ('wordpress-saved-' + stage + '-publish.json')).write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage', choices=['media', 'index', 'code'], required=True)
    args = parser.parse_args()
    manifest, paths = publication_inputs()
    if args.stage == 'index':
        pin_index(manifest)
    else:
        if args.stage == 'code':
            paths = check_code(manifest, paths)
        publish(args.stage, paths)


if __name__ == '__main__':
    main()
