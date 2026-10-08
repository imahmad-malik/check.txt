#!/usr/bin/env python3
"""Verify actual launch media independently of plans, encodings and fixture tests."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

from PIL import Image

ROOT = Path(__file__).resolve().parent


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def image_record(row):
    key = row['key']
    errors = []
    if row.get('approved') is not True or row.get('review_status') != 'approved':
        errors.append('explicit approval missing')
    if row.get('upscaled') is not False or row.get('native_8k') is not False or not row.get('native_original'):
        errors.append('accepted native provenance missing')
    paths = {}
    for field, hash_field in [('source_file', 'sha256'), ('file', 'display_sha256'), ('generator_original_file', 'generator_original_sha256')]:
        relative = row.get(field, '')
        path = (ROOT / relative).resolve()
        if not relative or ROOT not in path.parents or not path.is_file() or digest(path) != row.get(hash_field):
            errors.append(field + ' actual path/SHA mismatch')
        else:
            paths[field] = path
    dimensions = (row.get('width'), row.get('height'))
    pixel_hashes = []
    for field, path in paths.items():
        try:
            with Image.open(path) as im:
                if im.size != dimensions:
                    errors.append(field + ' actual dimensions differ')
                if max(im.size) < 1024:
                    errors.append(field + ' below accepted native long edge')
                if field != 'file':
                    pixel_hashes.append(hashlib.sha256(im.convert('RGB').tobytes()).hexdigest())
        except Exception as exception:
            errors.append(field + ' decode failed: ' + type(exception).__name__)
    if len(pixel_hashes) != 2 or len(set(pixel_hashes)) != 1 or pixel_hashes[0] != row.get('native_pixel_sha256'):
        errors.append('native pixels do not match generator-original proof')
    if not row.get('alt') or not row.get('caption') or not row.get('review'):
        errors.append('image-specific text/review missing')
    return {'key': key, 'passed': not errors, 'errors': errors, 'dimensions': dimensions,
            'native_sha256': row.get('sha256'), 'native_pixel_sha256': row.get('native_pixel_sha256')}


def main():
    catalog = json.loads((ROOT / 'content/catalog.json').read_text())
    manifest = json.loads((ROOT / 'media/manifest.json').read_text())
    by_key = {row['key']: row for row in manifest['records'] if row.get('key')}
    gallery = [image for look in catalog['looks'] for image in look['images']]
    home = [by_key[key] for key in catalog['requirements']['required_home_media'] if key in by_key]
    canonical_keys = {row['key'] for row in gallery + home}
    partial_gallery = [row for row in manifest['records']
                       if row.get('key') not in canonical_keys
                       and row.get('approved') is True
                       and row.get('review_status') == 'approved'
                       and row.get('usage') != 'resolution-probe'
                       and row.get('angle') in {'front', 'side', 'back'}
                       and (row.get('look_id') or row.get('look_key'))]
    # Save and independently verify genuine partial angle sources, without
    # pretending they are finished three-angle looks or publishable collections.
    selected = gallery + home + partial_gallery
    failures = []
    for row in gallery:
        canonical = by_key.get(row['key'], {})
        if any(row.get(field) != canonical.get(field) for field in ['source_file', 'file', 'sha256', 'display_sha256', 'width', 'height']):
            failures.append(row['key'] + ': canonical/master source mismatch')
    with ThreadPoolExecutor(max_workers=6) as executor:
        checks = list(executor.map(image_record, selected))
    failures += [item['key'] + ': ' + ', '.join(item['errors']) for item in checks if not item['passed']]
    for field in ['key', 'sha256', 'native_pixel_sha256']:
        values = [row.get(field) for row in selected]
        if None in values or len(values) != len(set(values)):
            failures.append('A launch photograph is reused or lacks unique ' + field)
    film_key = catalog['requirements']['required_home_video']
    film = by_key.get(film_key, {})
    film_result = {'key': film_key, 'verified': False, 'browser_playback': film.get('review', {}).get('browser_playback', 'missing')}
    if film:
        path = (ROOT / film.get('source_file', '')).resolve()
        source_keys = film.get('source_asset_keys', [])
        if ROOT not in path.parents or not path.is_file() or digest(path) != film.get('sha256'):
            failures.append('Film path/SHA mismatch')
        elif not film.get('approved') or film.get('review_status') != 'approved' or not film.get('multiview'):
            failures.append('Film explicit review missing')
        elif len(set(source_keys)) != 3 or not {'front', 'side', 'back'} <= {by_key.get(key, {}).get('angle') for key in source_keys}:
            failures.append('Film real front/side/back source declaration missing')
        else:
            metadata = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(path)]))
            stream = next(s for s in metadata['streams'] if s['codec_type'] == 'video')
            if (stream['width'], stream['height']) != (film['width'], film['height']) or stream['codec_name'] != 'h264' or any(s['codec_type'] == 'audio' for s in metadata['streams']):
                failures.append('Actual silent film stream differs from declared delivery')
            if any(not by_key.get(key, {}).get('approved') for key in source_keys):
                failures.append('Film references an unapproved source')
            subprocess.run(['ffmpeg', '-v', 'error', '-i', str(path), '-f', 'null', '-'], check=True)
            film_result.update({'verified': True, 'dimensions': [stream['width'], stream['height']],
                                'seconds': float(metadata['format']['duration']), 'source_keys': source_keys,
                                'sha256': film['sha256']})
    complete = len(catalog['looks']) == 154 and len(gallery) == 462 and len(home) == 25 and film_result['verified']
    report = {'timestamp': datetime.now(timezone.utc).isoformat(),
              'status': 'verified_complete_assets' if complete and not failures else ('verified_partial_assets' if not failures else 'failed'),
              'actual_complete_looks': len(catalog['looks']), 'actual_gallery_photographs': len(gallery),
              'actual_home_photographs': len(home), 'required_unique_photographs': 487,
              'actual_approved_photographs': len(selected),
              'actual_individually_approved_partial_gallery_photographs': len(partial_gallery),
              'remaining_actual_photographs': max(0, 487 - len(selected)),
              'remaining_gallery_photographs': max(0, 462 - len(gallery)), 'checks': checks,
              'film': film_result, 'failures': failures,
              'limits': ['This checks actual original pixels, encodings, unique identities, dimensions, hashes and declared reviews. Visual inspection is separately recorded per asset.',
                         'WordPress final import, browser paint/editor/motion and target-host checks require their own runtime evidence.']}
    (ROOT / 'tests/production-media-report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({key: value for key, value in report.items() if key != 'checks'}, indent=2))
    raise SystemExit(1 if failures else 0)


if __name__ == '__main__':
    main()
