#!/usr/bin/env python3
"""Actual owner GUI multipart import on separate final localhost noindex WordPress.

Run with --parts DIRECTORY --phase integration|final. Credentials and cookies stay
private outside the package. Every checkpoint is persisted before assertions.
"""
import argparse
import hashlib
import json
import os
import subprocess
import traceback
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import sync_playwright

TESTS = Path(__file__).resolve().parent
PRIVATE = Path('/workspace/wp-final-test')
SITE = 'http://127.0.0.1:8767'
AUTH = PRIVATE / 'qa-auth-state.json'


def inspect():
    result = subprocess.run([str(PRIVATE / 'php'), str(TESTS / 'wp-final-state.php'), str(PRIVATE / 'wordpress/wp-load.php')], text=True, capture_output=True, check=True)
    return json.loads(result.stdout)


def authenticate(browser):
    context = browser.new_context(storage_state=str(AUTH) if AUTH.exists() else None)
    page = context.new_page()
    page.goto(SITE + '/wp-admin/tools.php?page=bixie-setup', wait_until='networkidle')
    if page.locator('#adminmenu').count() != 1:
        credentials = json.loads((PRIVATE / 'qa-credentials.json').read_text())
        page.locator('#user_login').fill(credentials['admin_user'])
        page.locator('#user_pass').fill(credentials['admin_password'])
        page.locator('#wp-submit').click()
        page.wait_for_url('**/wp-admin/**')
        page.goto(SITE + '/wp-admin/tools.php?page=bixie-setup', wait_until='networkidle')
    assert page.locator('#adminmenu').count() == 1, 'Owner authentication did not reach WordPress admin.'
    context.storage_state(path=str(AUTH))
    AUTH.chmod(0o600)
    return context, page


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--parts', type=Path)
    parser.add_argument('--phase', choices=['integration', 'final'], default='integration')
    parser.add_argument('--authenticate-only', action='store_true')
    parser.add_argument('--repeat', action='store_true')
    args = parser.parse_args()
    destination = TESTS / ('wp-final-' + args.phase + '-import-report.json')
    report = {'generatedAtUTC': datetime.now(timezone.utc).isoformat(), 'scope': 'Actual native authenticated WordPress owner GUI upload/import on the separate localhost8767 noindex site. Only actual supplied sources; no synthetic fixture import.', 'phase': args.phase, 'finalAcceptance': args.phase == 'final', 'checks': {}, 'parts': [], 'passed': False, 'remoteWordPressHTTPSFetchVerified': False}

    def save():
        destination.write_text(json.dumps(report, indent=2) + '\n')

    try:
        if not args.authenticate_only:
            assert args.parts and args.parts.is_dir(), 'Provide immutable multipart directory.'
            paths = sorted(args.parts.glob('*.zip'))
            assert paths
            download_index_path = args.parts / 'media-download-manifest.json'
            download_index = json.loads(download_index_path.read_text()) if download_index_path.exists() else None
            indexed = {Path(entry.get('filename') or entry['file']).name: entry for entry in download_index['parts']} if download_index else {}
            keys = set()
            for path in paths:
                digest = hashlib.sha256(path.read_bytes()).hexdigest()
                assert 0 < path.stat().st_size <= 25 * 1024 * 1024, path.name
                if download_index:
                    assert path.name in indexed and indexed[path.name]['sha256'] == digest and indexed[path.name]['bytes'] == path.stat().st_size, 'Immutable download manifest mismatch: ' + path.name
                with zipfile.ZipFile(path) as archive:
                    manifest = json.loads(archive.read('manifest.json'))
                assert not keys.intersection(record['key'] for record in manifest.get('records', [])), 'Duplicate media keys across selected parts.'
                keys.update(record['key'] for record in manifest.get('records', []))
                report['parts'].append({'filename': path.name, 'bundleID': manifest['bundle_id'], 'bytes': path.stat().st_size, 'sha256': digest, 'records': len(manifest.get('records', [])), 'looks': len(manifest.get('looks', []))})
            report['expectedSuppliedUniqueMedia'] = len(keys)
            if download_index:
                assert len(paths) == len(indexed)
                report['checks']['selectedPartsMatchImmutableDownloadManifestHashesAndBytes'] = True
            report['before'] = inspect()
            save()
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox'])
            context, page = authenticate(browser)
            report['checks']['ownerAuthenticatedViaNativeGUI'] = True
            save()
            if args.authenticate_only:
                report['passed'] = True
                save()
                print(json.dumps({'authenticated': True, 'privateAuthMode': oct(AUTH.stat().st_mode & 0o777)}))
                context.close(); browser.close()
                return
            errors = []
            page.on('pageerror', lambda error: errors.append(str(error)))
            assert not page.locator('#bixie-overwrite').is_checked()
            page.locator('#bixie-configure').check()
            page.locator('#bixie-bundle-files').set_input_files([str(path) for path in paths])
            page.locator('#bixie-bundle-upload').click()
            page.wait_for_function('(count)=>document.querySelector("#bixie-bundle-status").textContent.startsWith(count+" of "+count+" selected part(s) verified")', arg=len(paths), timeout=600000)
            report['checks']['actualMultipartGUIUploadVerifierCompleted'] = True
            report['uploadStatus'] = page.locator('#bixie-bundle-status').inner_text()
            report['afterUpload'] = inspect()
            save()
            for part in report['parts']:
                actual = report['afterUpload']['parts'][part['bundleID']]
                assert actual['archive_sha256'] == part['sha256'], part['bundleID']
            report['checks']['realUploadedZIPHashesMatchSelectedImmutableParts'] = True
            page.locator('#bixie-import-start').click()
            page.wait_for_function('()=>!document.querySelector("#bixie-import-start").disabled&&document.querySelector("#bixie-import-message").textContent.startsWith("Import finished.")', timeout=900000)
            report['after'] = inspect()
            report['checks']['actualOwnerGUIImportCompleted'] = report['after']['import']['status'] == 'complete'
            report['pageErrors'] = errors
            save()
            assert not errors
            if args.repeat:
                before_repeat = report['after']
                page.locator('#bixie-import-start').click()
                page.wait_for_function('()=>!document.querySelector("#bixie-import-start").disabled&&document.querySelector("#bixie-import-message").textContent.startsWith("Import finished.")', timeout=900000)
                report['afterRepeat'] = inspect()
                assert before_repeat['preservation'] == report['afterRepeat']['preservation'], 'Repeated preserve import changed stored content, relationships or settings.'
                report['checks']['repeatedPreserveGUIImportIdempotent'] = True
                save()
            report['passed'] = True
            context.close(); browser.close()
    except Exception as error:
        report['failure'] = str(error)
        report['traceback'] = traceback.format_exc()
        raise
    finally:
        save()
        print(json.dumps({'passed': report['passed'], 'phase': args.phase, 'report': str(destination), 'checks': report['checks'], 'failure': report.get('failure')}, indent=2), flush=True)


if __name__ == '__main__':
    main()
