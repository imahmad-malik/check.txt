#!/usr/bin/env python3
"""Download and verify actual HTTPS saved-checkpoint artifacts and the full ZIP."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import ssl
import time
import urllib.parse
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
SCOPE = 'engineering_installable_media_incomplete'
ALLOWED_HOSTS = {'raw.githubusercontent.com', 'codeload.github.com'}


def safe_url(url):
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != 'https' or parsed.hostname not in ALLOWED_HOSTS or parsed.username or parsed.password or parsed.port not in (None, 443):
        raise ValueError('Only the expected GitHub HTTPS download hosts are allowed.')
    return url


class DownloadRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, response, code, message, headers, newurl):
        safe_url(newurl)
        return super().redirect_request(request, response, code, message, headers, newurl)


def stream_download(url, path, expected=None):
    safe_url(url)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_symlink() or any(parent.is_symlink() for parent in path.parents):
        raise ValueError('HTTPS verification output cannot use symlinks.')
    errors = []
    for attempt in range(1, 4):
        started = time.monotonic()
        opener = urllib.request.build_opener(urllib.request.ProxyHandler(),
                                            urllib.request.HTTPSHandler(context=ssl.create_default_context()),
                                            DownloadRedirect())
        partial = path.with_name(path.name + '.partial')
        try:
            request = urllib.request.Request(url, headers={'User-Agent': 'Bixie-saved-delivery-integrity/1.0',
                                                            'Accept-Encoding': 'identity'})
            with opener.open(request, timeout=30) as response:
                if response.status != 200:
                    raise ValueError('The actual HTTPS download did not return HTTP 200.')
                safe_url(response.geturl())
                headers = {key: response.headers.get(key) for key in ['Content-Type', 'Content-Length', 'Content-Disposition']}
                size = 0
                sha = hashlib.sha256()
                with partial.open('wb') as output:
                    while True:
                        remaining = 60 - (time.monotonic() - started)
                        if remaining <= 0:
                            raise TimeoutError('An individual HTTPS download exceeded its 60-second budget.')
                        # Keep each blocking socket read within the remaining
                        # request budget. Proxy TLS validation stays enabled.
                        socket = getattr(getattr(getattr(response, 'fp', None), 'raw', None), '_sock', None)
                        if socket is not None:
                            socket.settimeout(min(remaining, 20))
                        chunk = response.read(1024 * 1024)
                        if not chunk:
                            break
                        output.write(chunk)
                        sha.update(chunk)
                        size += len(chunk)
                        if expected and size > expected['bytes']:
                            raise ValueError('HTTPS response exceeded the actual artifact size.')
                if headers['Content-Length'] and int(headers['Content-Length']) != size:
                    raise ValueError('Actual response length differs from HTTP Content-Length.')
                if expected and (size != expected['bytes'] or sha.hexdigest() != expected['sha256']):
                    raise ValueError('Actual HTTPS response size/SHA differs from the published Git bytes.')
                partial.replace(path)
                return {'url': url, 'http_status': 200, 'tls_certificate_validation': True,
                        'bytes': size, 'sha256': sha.hexdigest(), 'headers': headers,
                        'elapsed_seconds': round(time.monotonic() - started, 3),
                        'attempts': attempt, 'downloaded_file': str(path), 'passed': True}
        except Exception as error:
            partial.unlink(missing_ok=True)
            errors.append(str(error))
    raise RuntimeError('Actual HTTPS download failed after bounded attempts: ' + url + ' / ' + '; '.join(errors))


def digest_member(archive, name):
    sha = hashlib.sha256()
    size = 0
    with archive.open(name) as source:
        while True:
            chunk = source.read(1024 * 1024)
            if not chunk:
                break
            sha.update(chunk)
            size += len(chunk)
    return size, sha.hexdigest()


def verify_full_zip(path, publication, downloaded):
    disposition = downloaded['headers'].get('Content-Disposition') or ''
    if not disposition.lower().startswith('attachment;') or '.zip' not in disposition.lower():
        raise ValueError('The actual full download lacks its ZIP attachment Content-Disposition.')
    expected = {row['path']: row for row in publication['published_files']}
    commit = publication['commit']
    prefix = 'check.txt-' + commit + '/'
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)) or any(name.startswith('/') or '..' in PurePosixPath(name).parts or not name.startswith(prefix) for name in names):
            raise ValueError('Full actual codeload archive paths are unsafe, duplicated, or incorrectly rooted.')
        if archive.testzip() is not None:
            raise ValueError('Actual full codeload ZIP failed its CRC check.')
        selected = {name[len(prefix):] for name in names if name.startswith((prefix + 'wordpress-media-release/', prefix + 'wordpress-release/')) and not name.endswith('/')}
        if selected != set(expected):
            raise ValueError('Full codeload ZIP contains missing or extra checkpoint delivery files.')
        for relative, row in expected.items():
            size, sha = digest_member(archive, prefix + relative)
            if size != row['bytes'] or sha != row['sha256']:
                raise ValueError('A full codeload member differs from the actual published bytes: ' + relative)
        for relative in selected:
            lower = relative.lower()
            if any(token in lower for token in ['qa-credentials', 'wp-config.php', 'auth-state', '/.git/', '/.env', 'private-key']):
                raise ValueError('A private runtime path entered the actual codeload delivery.')
    return {'actual_zip_attachment_header': True, 'safe_unique_paths': True,
            'all_zip_member_crc_checks': True, 'exact_selected_file_inventory': True,
            'all_selected_member_sha256_and_sizes': True, 'selected_files_verified': len(expected)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase', choices=['media', 'code'], default='code')
    parser.add_argument('--workers', type=int, choices=[1, 2, 3, 4], default=4)
    args = parser.parse_args()
    destination = ROOT / 'tests' / ('https-saved-media-report.json' if args.phase == 'media' else 'https-saved-delivery-report.json')
    publication = json.loads((REPO / ('wordpress-saved-' + args.phase + '-publish.json')).read_text())
    commit = publication.get('commit', '')
    if publication.get('release_scope') != SCOPE or publication.get('stage') != args.phase or not re.fullmatch(r'[0-9a-f]{40}', commit):
        raise ValueError('An actual immutable incomplete-checkpoint publication is required.')
    report = {'timestamp_utc': datetime.now(timezone.utc).isoformat(), 'release_scope': SCOPE,
              'phase': args.phase, 'commit': commit, 'passed': False,
              'actual_counts': publication['actual_counts'], 'downloads': [], 'checks': {},
              'limits': ['The remaining 65 gallery originals are not completed or included.',
                         'Actual WordPress server-side remote media download is separately unverified because of runtime DNS; these are actual proxy HTTPS downloads with TLS validation.',
                         'These download checks do not establish a complete 154-look site, rankings, production hosting behavior, or real SEO plugin coexistence.']}
    cache = Path('/tmp') / ('bixie-saved-https-' + commit[:12])

    def save():
        destination.write_text(json.dumps(report, indent=2) + '\n')

    try:
        rows = publication['published_files']
        assert len({row['path'] for row in rows}) == len(rows)
        for row in rows:
            path = PurePosixPath(row['path'])
            if path.is_absolute() or '..' in path.parts or path.parts[0] not in {'wordpress-media-release', 'wordpress-release'}:
                raise ValueError('Unexpected published checkpoint path.')
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            futures = {pool.submit(stream_download,
                                   'https://raw.githubusercontent.com/imahmad-malik/check.txt/' + commit + '/' + row['path'],
                                   cache / row['path'], row): row for row in rows}
            for future in as_completed(futures):
                row = futures[future]
                result = future.result()
                result['path'] = row['path']
                report['downloads'].append(result)
                save()
                print(json.dumps({'verified_https_file': row['path'], 'bytes': result['bytes'],
                                  'verified_files': len(report['downloads']), 'total_files': len(rows)}), flush=True)
        report['checks']['all_selected_actual_https_downloads_status_200_size_sha256_tls'] = True
        if args.phase == 'code':
            index = json.loads((ROOT / 'plugin/bixie-library/content/release-index.json').read_text())
            media_publication = json.loads((REPO / 'wordpress-saved-media-publish.json').read_text())
            media_report = json.loads((ROOT / 'tests/https-saved-media-report.json').read_text())
            if media_report.get('passed') is not True or media_report.get('commit') != media_publication['commit']:
                raise ValueError('Actual pinned media-commit HTTPS download verification is required.')
            pinned = {item['url']: item for item in media_report['downloads']}
            for part in index['parts']:
                actual = pinned.get(part['url'])
                if not actual or actual['sha256'] != part['sha256'] or actual['bytes'] != part['bytes'] or actual.get('passed') is not True:
                    raise ValueError('Plugin pinned media URL lacks an actual verified HTTPS response.')
            report['checks']['all_plugin_pinned_part_urls_verified_from_media_commit'] = True
            downloaded = stream_download(publication['full_zip_url'], cache / 'Bixie-Saved-Checkpoint-Download.zip')
            report['full_zip_download'] = downloaded
            report['checks'].update(verify_full_zip(Path(downloaded['downloaded_file']), publication, downloaded))
            report['download_links'] = {'all_saved_files_zip': publication['full_zip_url'],
                                        'theme_zip': 'https://raw.githubusercontent.com/imahmad-malik/check.txt/' + commit + '/wordpress-release/bixie-editorial.zip',
                                        'plugin_zip': 'https://raw.githubusercontent.com/imahmad-malik/check.txt/' + commit + '/wordpress-release/bixie-library.zip'}
        report['passed'] = True
    except Exception as error:
        report['failure'] = str(error)
        raise
    finally:
        save()
        print(json.dumps({'passed': report['passed'], 'release_scope': SCOPE, 'phase': args.phase,
                          'actual_verified_files': len(report['downloads']), 'report': str(destination),
                          'failure': report.get('failure')}, indent=2), flush=True)


if __name__ == '__main__':
    main()
