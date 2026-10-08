#!/usr/bin/env python3
"""Pin final media downloads to the actual immutable published Git commit."""
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent


def main():
    published = json.loads((REPO / 'wordpress-final-media-publish.json').read_text())
    commit = published['commit']
    if published['stage'] != 'media' or not re.fullmatch(r'[0-9a-f]{40}', commit):
        raise ValueError('An actual immutable media publication is required.')
    manifest = json.loads((REPO / 'wordpress-media-release/media-download-manifest.json').read_text())
    rows = []
    for part in manifest['parts']:
        name = part['file']
        relative = 'wordpress-media-release/' + name
        if relative not in published['selected_files'] or Path(name).name != name or not name.endswith('.zip'):
            raise ValueError('Part was not included in the pinned actual publication.')
        data = subprocess.check_output(['git', 'show', commit + ':' + relative], cwd=REPO)
        if len(data) != part['bytes'] or hashlib.sha256(data).hexdigest() != part['sha256']:
            raise ValueError('Published Git bytes differ from the actual media-part manifest.')
        rows.append({'bundle_id': name[:-4], 'url': 'https://raw.githubusercontent.com/imahmad-malik/check.txt/' + commit + '/' + relative, 'sha256': part['sha256'], 'bytes': part['bytes']})
    index = {'version': 1, 'release': 'bixie-wordpress-' + commit[:12], 'parts': rows}
    (ROOT / 'plugin/bixie-library/content/release-index.json').write_text(json.dumps(index, indent=2) + '\n')
    print(json.dumps({'status': 'pinned_to_actual_media_publication', 'commit': commit, 'verified_parts': len(rows), 'total_bytes': sum(row['bytes'] for row in rows)}, indent=2))


if __name__ == '__main__':
    main()
