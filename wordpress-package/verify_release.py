#!/usr/bin/env python3
"""Verify archive layout, production isolation, references and checksums."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import zipfile

ROOT = Path(__file__).resolve().parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--release', type=Path, default=ROOT.parent / 'wordpress-release')
args = parser.parse_args()
release = args.release.resolve()
manifest = json.loads((release / 'release-manifest.json').read_text())
checks = []


def check(name, condition, detail=''):
    checks.append({'check': name, 'passed': bool(condition), 'detail': detail})


for artifact in manifest['artifacts']:
    path = release / artifact['file']
    check(artifact['file'] + ' checksum', hashlib.sha256(path.read_bytes()).hexdigest() == artifact['sha256'])
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        check(artifact['file'] + ' CRC integrity', archive.testzip() is None)
        check(artifact['file'] + ' safe unique paths', len(names) == len(set(names)) and all(not n.startswith('/') and '..' not in PurePosixPath(n).parts for n in names))
        check(artifact['file'] + ' excludes private runtime files', all(not any(x in n.lower() for x in ['wp-config.php', 'qa-credentials', '/.env', '/.git/', 'runtime-packages', 'wp-test/wordpress/']) for n in names))
        if artifact['file'] in ['bixie-editorial.zip', 'bixie-library.zip']:
            folder = artifact['file'][:-4] + '/'
            check(artifact['file'] + ' single install root', all(n.startswith(folder) for n in names))
            check(artifact['file'] + ' excludes diagnostic and synthetic media', all(not n.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.mp4', '.pdf')) for n in names))
        if artifact['file'] == 'bixie-library.zip':
            catalog = json.loads(archive.read('bixie-library/content/catalog.json'))
            media = json.loads(archive.read('bixie-library/content/media/manifest.json'))
            complete = catalog.get('counts', {}).get('provided_complete_three_angle_sets', 0)
            check('Plugin catalog counts agree with actual complete look records', len(catalog['looks']) == complete)
            check('Plugin bulk media are separate verified parts', not media.get('records'))
        if artifact['file'] in ['Bixie-WordPress-Engineering-Package.zip', 'Bixie-WordPress-Package.zip']:
            broken = []
            for name in names:
                if not name.endswith('.md'):
                    continue
                text = archive.read(name).decode('utf-8')
                for link in re.findall(r'\[[^\]]*\]\(([^)]+)\)', text):
                    if re.match(r'^[a-zA-Z]+:', link) or link.startswith('#'):
                        continue
                    target = link.split('#', 1)[0].strip('<>')
                    candidate = str(PurePosixPath(name).parent / target)
                    if target and candidate not in names:
                        broken.append({'source': name, 'target': target})
            check('Source bundle relative documentation links resolve', not broken, broken)
            notice = archive.read('README.md').decode()
            check('Source bundle identifies its actual media/release state', manifest['release_state'] in notice and 'Planned images are not delivered assets' in notice)

result = {'status': 'passed' if all(c['passed'] for c in checks) else 'failed',
          'checks_passed': sum(c['passed'] for c in checks), 'checks_total': len(checks),
          'release_state': manifest['release_state'], 'checks': checks,
          'limitations': ['Archive checks do not verify WordPress behavior, approved photographs, production hosting or ranking.']}
(ROOT / 'tests/release-archive-report.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
raise SystemExit(0 if result['status'] == 'passed' else 1)
