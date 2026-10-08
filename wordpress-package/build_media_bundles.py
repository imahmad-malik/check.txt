#!/usr/bin/env python3
"""Package actual reviewed media for the companion plugin's multipart importer."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parent
STAMP = (2026, 10, 7, 0, 0, 0)
ALLOWED = {'.png', '.jpg', '.jpeg', '.webp', '.avif', '.mp4'}


def sha(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def actual_approved(record):
    return (record.get('usage') != 'resolution-probe'
            and record.get('import_as_public_look') is not False
            and not record.get('upscaled')
            and (record.get('approved') is True or record.get('review_status') == 'approved'
                 or str(record.get('review', {}).get('release_status', '')).startswith('approved')))


def safe_file(relative: str):
    path = Path(relative)
    if path.is_absolute() or '..' in path.parts or '\\' in relative or ':' in relative:
        raise ValueError(f'Unsafe media path: {relative}')
    resolved = (ROOT / path).resolve(strict=True)
    if ROOT not in resolved.parents or resolved.suffix.lower() not in ALLOWED or not resolved.is_file():
        raise ValueError(f'Unacceptable media source: {relative}')
    return resolved


def put(archive, name, data):
    info = zipfile.ZipInfo(name, STAMP)
    info.create_system = 3
    info.external_attr = 0o100644 << 16
    info.compress_type = zipfile.ZIP_DEFLATED
    archive.writestr(info, data)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, default=ROOT / 'media/manifest.json')
    parser.add_argument('--output', type=Path, default=ROOT.parent / 'wordpress-media-release')
    parser.add_argument('--max-mib', type=int, default=25)
    parser.add_argument('--bundle-prefix', default='bixie-media-part', help='Distinct immutable IDs for integration-only batches; final release uses the default.')
    args = parser.parse_args()
    if not 4 <= args.max_mib <= 25:
        raise ValueError('Media part limit must be between 4 and 25 MiB.')
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,58}', args.bundle_prefix):
        raise ValueError('Bundle prefix must be a safe lowercase identifier no longer than 59 characters.')
    output = args.output.resolve()
    if output == ROOT or ROOT in output.parents:
        raise ValueError('Output must be outside the source package.')
    output.mkdir(parents=True, exist_ok=True)
    source_manifest = json.loads(args.manifest.read_text())
    catalog = json.loads((ROOT / 'content/catalog.json').read_text())
    records = [r for r in source_manifest.get('records', []) if actual_approved(r)]
    assets = []
    seen_keys, seen_hashes = set(), set()
    for raw in records:
        record = dict(raw)
        key = record.get('key') or record.get('id')
        if not key or key in seen_keys:
            raise ValueError('Every actual asset needs a distinct stable key.')
        seen_keys.add(key)
        record['key'] = key
        files = {}
        source = record.get('source_file') or record.get('file')
        if not source:
            raise ValueError(f'Actual source missing for {key}')
        path = safe_file(source)
        expected = record.get('sha256') if record.get('source_file') else record.get('display_sha256', record.get('sha256'))
        digest = sha(path)
        if digest != expected or digest in seen_hashes:
            raise ValueError(f'Source checksum invalid or original reused: {key}')
        seen_hashes.add(digest)
        files[source] = path
        if record.get('file') and record['file'] != source:
            display = safe_file(record['file'])
            if sha(display) != record.get('display_sha256'):
                raise ValueError(f'Display checksum invalid: {key}')
            files[record['file']] = display
        assets.append((record, files))

    # Use uncompressed bytes plus a manifest allowance as a conservative limit.
    # Final compressed sizes are checked before any part is advertised.
    limit = args.max_mib * 1024 * 1024
    metadata_allowance = 1024 * 1024
    groups, group, size = [], [], metadata_allowance
    for asset in assets:
        item_size = sum(p.stat().st_size for p in asset[1].values()) + len(json.dumps(asset[0]).encode()) + 1024
        if item_size + metadata_allowance > limit:
            raise ValueError('One source exceeds the chosen upload part size; increase the supported host limit or repackage without reducing its pixels.')
        if group and size + item_size > limit:
            groups.append(group)
            group, size = [], metadata_allowance
        group.append(asset)
        size += item_size
    if group:
        groups.append(group)

    approved_looks = []
    for look in catalog.get('looks', []):
        views = look.get('images', [])
        if look.get('status') == 'publish' and {v.get('angle') for v in views} >= {'front', 'side', 'back'} and all((v.get('key') or v.get('id')) in seen_keys for v in views):
            # Source provenance, dimensions and hashes already live in the
            # authoritative media records. Do not duplicate all that per-image
            # data154times in the final manifest (the verifier bounds it at2MiB).
            approved_looks.append({**look, 'images': [
                {'key': image.get('key') or image.get('id'), 'angle': image['angle'],
                 'caption': image.get('caption', '')} for image in views]})
    parts = []
    for index, group in enumerate(groups, 1):
        bundle_id = f'{args.bundle_prefix}-{index:03d}'
        filename = f'{bundle_id}.zip'
        target = output / filename
        manifest = {'bundle_id': bundle_id, 'schema_version': '1.0',
                    'records': [a[0] for a in group], 'looks': approved_looks if index == len(groups) else [],
                    'native_resolution_claim': 'Actual original dimensions are recorded per asset; no native 8K claim.'}
        manifest_bytes=(json.dumps(manifest, indent=2) + '\n').encode()
        if len(manifest_bytes)>2*1024*1024:
            raise ValueError('Media manifest exceeds the actual WordPress verifier2MiB bound.')
        with zipfile.ZipFile(target, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
            put(archive, 'manifest.json', manifest_bytes)
            emitted = set()
            for record, files in group:
                for relative, path in files.items():
                    if relative not in emitted:
                        put(archive, relative, path.read_bytes())
                        emitted.add(relative)
        with zipfile.ZipFile(target) as archive:
            if archive.testzip() is not None or target.stat().st_size > limit:
                raise ValueError(f'Part CRC/size verification failed: {filename}')
        parts.append({'file': filename, 'bytes': target.stat().st_size, 'sha256': sha(target),
                      'actual_media_records': len(group), 'look_records': len(manifest['looks'])})
    report = {'status': 'built' if parts else 'no_approved_media_to_package',
              'actual_approved_media_records': len(assets), 'actual_complete_look_records': len(approved_looks),
              'maximum_part_bytes': limit, 'parts': parts,
              'note': 'A partial reviewed batch does not establish the full photographic launch.'}
    (output / 'media-download-manifest.json').write_text(json.dumps(report, indent=2) + '\n')
    (output / 'SHA256SUMS.txt').write_text(''.join(f"{p['sha256']}  {p['file']}\n" for p in parts))
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
