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
    if catalog.get('looks') or manifest.get('records'):
        raise ValueError('This engineering-only release expects zero launch media; review the release state before bundling approved assets.')

    for directory, name in [('theme/bixie-editorial', 'bixie-editorial.zip'),
                            ('plugin/bixie-library', 'bixie-library.zip')]:
        base = ROOT / directory
        build_zip(output / name, [(str(p.relative_to(base.parent)), p) for p in source_files(base)])
    content_base = ROOT / 'content'
    build_zip(output / 'content-plan.zip', [(str(p.relative_to(ROOT)), p) for p in source_files(content_base)])

    notice = '''# Bixie WordPress engineering package — media incomplete

This is an installable theme and companion plugin, with editable page content,
collection definitions and an importer. It is NOT the completed launch requested.
There are 0 approved launch photographs, 0 complete public looks and no completed
movie. The 487 image requests are a production plan, not delivered assets.

Install bixie-editorial.zip in Appearance → Themes → Add New → Upload Theme.
Install bixie-library.zip in Plugins → Add New → Upload Plugin; activate both.
Open Tools → Bixie package setup and use the tracked content import. Incomplete
photo-led pages stay in draft. The content plan alone does not fill the galleries.

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
    for directory in ['theme', 'plugin', 'content', 'tests', 'media', 'source-media']:
        entries.extend((str(p.relative_to(ROOT)), p) for p in source_files(ROOT / directory))
    for path in sorted(ROOT.glob('*.py')):
        entries.append((path.name, path))
    build_zip(output / 'Bixie-WordPress-Engineering-Package.zip', entries)

    artifacts = []
    for path in sorted(output.glob('*.zip')):
        artifacts.append({'file': path.name, 'bytes': path.stat().st_size, 'sha256': sha256(path)})
    state = {'release_state': 'engineering_installable_media_incomplete',
             'approved_launch_photographs': 0, 'complete_launch_looks': 0,
             'completed_movies': 0, 'planned_original_photo_requests': 487,
             'artifacts': artifacts}
    (output / 'release-manifest.json').write_text(json.dumps(state, indent=2) + '\n')
    (output / 'SHA256SUMS.txt').write_text(''.join(f"{a['sha256']}  {a['file']}\n" for a in artifacts))
    print(json.dumps(state, indent=2))


if __name__ == '__main__':
    main()
