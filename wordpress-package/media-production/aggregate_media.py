"""Validate and aggregate actual media without inflating image counts."""
import datetime
import hashlib
import json
import os
from pathlib import Path

root = Path(os.environ.get('BIXIE_PACKAGE_ROOT', Path(__file__).resolve().parents[1]))
path = root / 'media/manifest.json'
manifest = json.loads(path.read_text())
diagnostic = [r for r in manifest.get('records', []) if r.get('usage') == 'resolution-probe']

def verify_record(row):
    for field, digest in [('source_file', 'sha256'), ('file', 'display_sha256')]:
        file = root / row[field]
        if not file.is_file():
            raise ValueError('Missing actual file: ' + row['id'] + ':' + field)
        expected = row.get(digest, row.get('sha256'))
        if hashlib.sha256(file.read_bytes()).hexdigest() != expected:
            raise ValueError('Checksum mismatch: ' + row['id'] + ':' + field)
    if row.get('generator_original_file'):
        original = root / row['generator_original_file']
        if hashlib.sha256(original.read_bytes()).hexdigest() != row['generator_original_sha256']:
            raise ValueError('Generator original checksum mismatch: ' + row['id'])
    return row

records = [verify_record(json.loads(p.read_text())) for p in sorted((root/'media/records').glob('*.json'))]
rejected = [verify_record(json.loads(p.read_text())) for p in sorted((root/'media/records/rejected').glob('*.json'))]
rejected += [r for r in records if r.get('usage') == 'rejected-attempt']
photos = [r for r in records if r.get('usage') in {'collection', 'homepage'}]
films = [r for r in records if r.get('usage') in {'homepage-film', 'photo-sequence-film'}]
bylook = {}
for row in photos:
    if row.get('usage') == 'collection':
        bylook.setdefault(row['look_id'], []).append(row)
seen = set()
approved_looks = []
for worker_file in sorted((root/'media/workers').glob('*.json')):
    worker = json.loads(worker_file.read_text())
    for declaration in worker.get('looks', []):
        look = dict(declaration)
        key = look.get('key')
        if key in seen:
            raise ValueError('Duplicate coherent look declaration: ' + str(key))
        seen.add(key)
        rows = bylook.get(key, [])
        if (look.get('approved') is True and look.get('review_status') == 'approved'
                and len(rows) == 3 and {r.get('angle') for r in rows} == {'front', 'side', 'back'}
                and all(r.get('approved') is True and r.get('review_status') == 'approved' for r in rows)):
            if len({r['sha256'] for r in rows}) != 3:
                raise ValueError('Repeated original within look: ' + key)
            look['images'] = sorted(rows, key=lambda r: ['front', 'side', 'back'].index(r['angle']))
            approved_looks.append(look)
hashes = [r['sha256'] for r in photos]
if len(hashes) != len(set(hashes)):
    raise ValueError('Repeated original source across photographic slots')
pixel_hashes = [r['native_pixel_sha256'] for r in photos if r.get('native_pixel_sha256')]
if len(pixel_hashes) != len(set(pixel_hashes)):
    raise ValueError('Repeated decoded original pixels across photographic slots')
def attempt_identity(row):
    # Historical attribution/recovery can archive one tool output more than
    # once. Each PNG/native/display encoding still represents one photograph.
    if row.get('generator_original_sha256'):
        return ('generator-png', row['generator_original_sha256'])
    if row.get('source_file', '').endswith('.png'):
        return ('generator-png', row['sha256'])
    if row.get('native_pixel_sha256'):
        return ('native-rgb', row['native_pixel_sha256'])
    return ('source-bytes', row['sha256'])
current_attempts = {attempt_identity(r) for r in diagnostic + photos}
rejected_attempts = {attempt_identity(r) for r in rejected} - current_attempts
manifest.update(records=diagnostic + records, rejected_attempts=rejected, looks=approved_looks,
                status='production_underway', updated_at=datetime.datetime.now(datetime.timezone.utc).isoformat())
manifest['counts'] = {
    'actual_originals': len(diagnostic) + len(photos),
    'actual_generated_photo_attempts': len(current_attempts | rejected_attempts),
    'diagnostic_originals': len(diagnostic),
    'actual_production_originals': len(photos),
    'reviewed_approved_production_photos': sum(r.get('approved') is True for r in photos),
    'approved_collection_originals': sum(len(l['images']) for l in approved_looks),
    'complete_looks': len(approved_looks),
    'approved_homepage_originals': sum(r.get('usage') == 'homepage' and r.get('approved') is True for r in photos),
    'actual_photo_sequence_films': len(films),
    'approved_photo_sequence_films': sum(r.get('approved') is True for r in films),
    'rejected_photo_attempts': len(rejected_attempts),
    'rejected_archive_records': len(rejected),
    'collection_photos_required': 462,
    'complete_looks_required': 154,
    'homepage_photos_required': 25,
    'collections_completed': sum(sum(l.get('primary_collection') == c for l in approved_looks) >= 7
                                 for c in {l.get('primary_collection') for l in approved_looks}),
}
def atomic_json(target, value):
    temp = target.with_suffix('.json.aggregate.tmp')
    temp.write_text(json.dumps(value, indent=2) + '\n')
    temp.replace(target)
atomic_json(path, manifest)
plan = json.loads((root/'media/generation-plan.json').read_text())
actual = {r['id'] for r in photos}
approved = {r['id'] for r in photos if r.get('approved') is True and r.get('review_status') == 'approved'}
progress = {
    'updated_at': manifest['updated_at'], 'counts': manifest['counts'],
    'complete_look_keys': [l['key'] for l in approved_looks],
    'missing_image_ids': [r['id'] for r in plan['planned_assets'] if r['id'] not in actual],
    'unapproved_existing_ids': sorted(actual - approved),
    'quality': {'minimum_native_long_edge': 1024, 'native_8k_claim': False, 'upscaling_allowed': False},
    'resume_rule': 'Verify existing originals and hashes before generating missing IDs; preserve failed attempts separately.',
}
atomic_json(root/'media/progress.json', progress)
print(json.dumps(manifest['counts']))
