#!/usr/bin/env python3
"""Build reproducible installable archives without the isolated QA installation."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parent
STAMP = (2026, 10, 7, 0, 0, 0)
FORBIDDEN_NAMES = {'.env', 'wp-config.php', 'qa-credentials.json', 'qa-credentials.txt'}


def source_files(directory: Path):
    for path in sorted(directory.rglob('*')):
        if not path.is_file():
            continue
        if path.is_symlink():
            raise ValueError(f'Symlink must not enter release: {path}')
        if any(part.startswith('.') or part == '__pycache__' for part in path.relative_to(ROOT).parts):
            continue
        if path.name in FORBIDDEN_NAMES or 'credentials' in path.name.lower():
            raise ValueError(f'Private file must not enter release: {path.name}')
        yield path


def add_bytes(archive: zipfile.ZipFile, name: str, data: bytes):
    if name.startswith('/') or '..' in Path(name).parts:
        raise ValueError(f'Unsafe archive path: {name}')
    info = zipfile.ZipInfo(name, STAMP)
    info.create_system = 3
    info.external_attr = 0o100644 << 16
    info.compress_type = zipfile.ZIP_DEFLATED
    archive.writestr(info, data)


def build_zip(target: Path, entries):
    with zipfile.ZipFile(target, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for name, path in entries:
            add_bytes(archive, name, path.read_bytes())
    with zipfile.ZipFile(target) as archive:
        if archive.testzip() is not None:
            raise RuntimeError(f'Archive integrity failed: {target.name}')


def sha256(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT.parent / 'wordpress-release')
    args = parser.parse_args()
    output = args.output.resolve()
    if output == ROOT or ROOT in output.parents:
        raise ValueError('Release output must be outside the source package.')
    output.mkdir(parents=True, exist_ok=True)

    catalog_path = ROOT / 'content/catalog.json'
    embedded = ROOT / 'plugin/bixie-library/content/catalog.json'
    if catalog_path.read_bytes() != embedded.read_bytes():
        raise ValueError('Plugin catalog differs from canonical content catalog.')
    catalog = json.loads(catalog_path.read_text())
    manifest = json.loads((ROOT / 'plugin/bixie-library/content/media/manifest.json').read_text())
    if manifest.get('records'):
        raise ValueError('Bulk actual media belongs in separately verified media parts, not the plugin code archive.')
    counts = catalog.get('counts', {})
    complete_looks = int(counts.get('provided_complete_three_angle_sets', 0))
    gallery_photos = int(counts.get('provided_unique_primary_collection_images', 0))
    home_photos = int(counts.get('provided_approved_home_role_images', 0))
    source_manifest = json.loads((ROOT / 'media/manifest.json').read_text())
    movies = sum(1 for r in source_manifest.get('records', [])
                 if str(r.get('source_file', r.get('file', ''))).endswith('.mp4')
                 and r.get('approved') is True and r.get('review_status') == 'approved')
    assets_complete = complete_looks >= 154 and gallery_photos >= 462 and home_photos >= 25 and movies >= 1
    release_state = 'assets_complete_target_host_checks_required' if assets_complete else 'engineering_installable_media_incomplete'
    bundle_name = 'Bixie-WordPress-Package.zip' if assets_complete else 'Bixie-WordPress-Engineering-Package.zip'

    for directory, name in [('theme/bixie-editorial', 'bixie-editorial.zip'),
                            ('plugin/bixie-library', 'bixie-library.zip')]:
        base = ROOT / directory
        build_zip(output / name, [(str(p.relative_to(base.parent)), p) for p in source_files(base)])
    content_base = ROOT / 'content'
    build_zip(output / 'content-plan.zip', [(str(p.relative_to(ROOT)), p) for p in source_files(content_base)])

    notice = f'''# Bixie WordPress package — {release_state}

This is an installable theme and companion plugin, with editable page content,
collection definitions and an importer.
Actual complete looks: {complete_looks} / 154. Actual gallery photographs:
{gallery_photos} / 462. Actual separate homepage photographs: {home_photos} / 25.
Reviewed production movies: {movies}. Planned images are not delivered assets.
{'Assets are complete; read the validation report for actual software/hosting checks.' if assets_complete else 'This is NOT the completed launch requested. Missing real media keeps launch incomplete.'}

Install bixie-editorial.zip in Appearance → Themes → Add New → Upload Theme.
Install bixie-library.zip in Plugins → Add New → Upload Plugin; activate both.
Open Tools → Bixie package setup. Import the separately provided verified media
parts, then use the tracked content import. Incomplete photo-led pages stay draft.
The code/source archive alone does not include hundreds of bulk photographs.

Read INSTALL.md, OWNER-GUIDE.md, VALIDATION-REPORT.md and LAUNCH-CHECKLIST.md.
The isolated test site's synthetic media are evidence only, never launch assets.
The available generator produced a 1312 × 1199 resolution probe; it is not native
8K. No low-resolution file has been relabelled 8K and no rejected preview photo
is bundled in either installable ZIP.
'''
    (output / 'README.md').write_text(notice)
    docs = [p for p in ROOT.glob('*.md') if p.is_file()]
    for doc in docs:
        (output / doc.name).write_bytes(doc.read_bytes())

    entries = [(name, output / name) for name in ['README.md', 'bixie-editorial.zip', 'bixie-library.zip', 'content-plan.zip']]
    entries += [(p.name, output / p.name) for p in docs if p.name != 'README.md']
    # Preserve source-relative documentation links. Diagnostic probe files live
    # only in this review/source archive, never in either installable ZIP.
    diagnostic_files = {'media/soft-layered-01.webp', 'source-media/soft-layered-01.png'}
    media_suffixes = {'.png', '.jpg', '.jpeg', '.webp', '.avif', '.mp4'}
    for directory in ['theme', 'plugin', 'content', 'tests', 'media', 'source-media', 'dev-environment']:
        for path in source_files(ROOT / directory):
            relative = str(path.relative_to(ROOT))
            if directory in {'media', 'source-media'} and path.suffix.lower() in media_suffixes and relative not in diagnostic_files:
                continue  # Bulk files are delivered in media parts/source backups.
            entries.append((relative, path))
    for path in sorted(ROOT.glob('*.py')):
        entries.append((path.name, path))
    build_zip(output / bundle_name, entries)

    artifacts = []
    for filename in [bundle_name, 'bixie-editorial.zip', 'bixie-library.zip', 'content-plan.zip']:
        path = output / filename
        artifacts.append({'file': path.name, 'bytes': path.stat().st_size, 'sha256': sha256(path)})
    state = {'release_state': release_state,
             'approved_launch_photographs': gallery_photos + home_photos,
             'complete_launch_looks': complete_looks, 'gallery_photographs': gallery_photos,
             'homepage_photographs': home_photos,
             'completed_movies': movies, 'planned_original_photo_requests': 487,
             'artifacts': artifacts}
    (output / 'release-manifest.json').write_text(json.dumps(state, indent=2) + '\n')
    (output / 'SHA256SUMS.txt').write_text(''.join(f"{a['sha256']}  {a['file']}\n" for a in artifacts))
    print(json.dumps(state, indent=2))


if __name__ == '__main__':
    main()
