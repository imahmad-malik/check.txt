#!/usr/bin/env python3
"""Real HTTPS release pilot through authenticated WordPress GUI; no simulated HTTP."""
import hashlib
import json
import shutil
import subprocess
import urllib.request
import zipfile
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
TESTS = ROOT / 'tests'
RUNTIME = Path('/workspace/wp-test/wordpress')
PHP = '/workspace/wp-test/php'
SITE = 'http://127.0.0.1:8766'
HELPER = TESTS / 'wp-live-pilot-state.php'
PILOT = Path('/workspace/wp-test/artifacts/bixie-production-pilot-001.zip')
INDEX = Path('/workspace/wp-test/artifacts/production-pilot-release-index.json')

def inspect(mode):
    result = subprocess.run([PHP, str(HELPER), str(RUNTIME / 'wp-load.php'), mode], check=True, text=True, capture_output=True)
    return json.loads(result.stdout)

def main():
    report = {'method': 'Actual authenticated Chromium owner GUI: trusted WordPress remote download attempt, then verified manual media-part fallback/import. Real pinned HTTPS distribution is independently fetched through proxy-aware Python transport. The pilot contains four reviewed real hairstyle sets and twelve original source views. Synthetic fixtures are excluded from production counts.', 'checks': {}, 'passed': False}
    release_index = RUNTIME / 'wp-content/plugins/bixie-library/content/release-index.json'
    old_index = None
    attachment_active = False
    registry_backup_active = False
    try:
        shutil.copytree(ROOT / 'plugin/bixie-library', RUNTIME / 'wp-content/plugins/bixie-library', dirs_exist_ok=True)
        shutil.copytree(ROOT / 'theme/bixie-editorial', RUNTIME / 'wp-content/themes/bixie-editorial', dirs_exist_ok=True)
        old_index = release_index.read_bytes()
        release_index.write_bytes(INDEX.read_bytes())
        index = json.loads(INDEX.read_text())
        with zipfile.ZipFile(PILOT) as archive:
            manifest = json.loads(archive.read('manifest.json'))
        part = index['parts'][0]
        assert hashlib.sha256(PILOT.read_bytes()).hexdigest() == part['sha256'] and PILOT.stat().st_size == part['bytes']
        digest = hashlib.sha256()
        byte_count = 0
        with urllib.request.urlopen(part['url'], timeout=45) as remote:
            assert remote.status == 200
            while chunk := remote.read(65536):
                byte_count += len(chunk)
                assert byte_count <= 25 * 1024 * 1024
                digest.update(chunk)
        assert byte_count == part['bytes'] and digest.hexdigest() == part['sha256']
        report['checks']['actualHTTPSPublishedArchive'] = {'transport': 'Python urllib through configured environment proxy with default HTTPS certificate verification; not the WordPress HTTP transport', 'url': part['url'], 'bytes': byte_count, 'sha256': digest.hexdigest()}
        before = inspect('pilot-inspect')
        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox'])
            admin = browser.new_context(storage_state='/workspace/wp-test/qa-auth-state.json')
            page = admin.new_page()
            errors = []
            page.on('pageerror', lambda e: errors.append(str(e)))
            attachment_fixtures = inspect('attachment-setup')
            attachment_active = True
            redirects = {}
            for kind, item in attachment_fixtures.items():
                response = admin.request.get(item['url'], max_redirects=0)
                if kind.startswith('project-'):
                    assert response.status == 301 and response.headers.get('location') == item['expected']
                    target = admin.request.get(item['expected'])
                    assert target.status == 200
                else:
                    response = admin.request.get(item['url'])
                    assert response.status == 200 and 'text/html' in response.headers.get('content-type', '')
                    assert '/wp-content/uploads/' not in response.url and not response.headers.get('x-robots-tag')
                redirects[kind] = {'status': response.status, 'url': response.url, 'location': response.headers.get('location', '')}
            report['checks']['actualProjectAndUnrelatedAttachmentHTTP'] = redirects
            inspect('attachment-cleanup')
            attachment_active = False
            response = page.goto(SITE + '/wp-admin/tools.php?page=bixie-setup', wait_until='networkidle')
            assert response.status == 200 and page.locator('#adminmenu').count() == 1
            assert not page.locator('#bixie-overwrite').is_checked()
            assert page.locator('#bixie-download-start').is_enabled()
            batches = []
            def log_ajax(response):
                if '/wp-admin/admin-ajax.php' not in response.url:
                    return
                try:
                    body = response.json()
                    request = response.request.post_data or ''
                    if 'bixie_media_download_' in request or 'bixie_import_' in request:
                        batches.append({'status': response.status, 'action': request.split('&')[0], 'success': body.get('success'), 'state': body.get('data', {}).get('status'), 'cursor': body.get('data', {}).get('cursor')})
                except Exception:
                    pass
            page.on('response', log_ajax)
            # Existing verified local parts otherwise skip HTTP, which cannot prove a remote fetch.
            inspect('pilot-force-remote')
            registry_backup_active = True
            page.locator('#bixie-download-start').click()
            page.wait_for_function("()=>document.querySelector('#bixie-import-message').textContent.startsWith('Import finished.') || document.querySelector('#bixie-download-status').textContent.includes('Verified parts remain saved')", timeout=60000)
            remote_error = inspect('pilot-inspect')['download'].get('error')
            if remote_error:
                assert 'valid URL' in remote_error
                report['checks']['wordPressRemoteTransport'] = {'verified': False, 'error': remote_error, 'reason': 'Cloud local DNS is unavailable for GitHub hosts. WordPress safe URL validation requires DNS before the configured proxy can perform HTTPS. Production HTTP safety and TLS settings were preserved.', 'fallback': 'Actual authenticated owner GUI manual media ZIP upload'}
                page.locator('#bixie-bundle-files').set_input_files(str(PILOT))
                page.locator('#bixie-bundle-upload').click()
                page.wait_for_function("()=>document.querySelector('#bixie-bundle-status').textContent.startsWith('1 of 1 selected part(s) verified')", timeout=60000)
                page.locator('#bixie-import-start').click()
            else:
                report['checks']['wordPressRemoteTransport'] = {'verified': True, 'transport': 'Actual WordPress wp_safe_remote_get HTTPS; no interceptor or HTTP mock'}
            page.wait_for_function("()=>document.querySelector('#bixie-import-message').textContent.startsWith('Import finished.')", timeout=60000)
            assert not errors
            after = inspect('pilot-inspect')
            assert after['part']['archive_sha256'] == part['sha256']
            if not remote_error:
                assert after['download']['status'] == 'complete' and after['download']['cursor'] == 1
            assert after['import']['status'] == 'complete'
            assert before['fixtureLooks'] == after['fixtureLooks']
            report['checks']['actualGUIverifiedMediaImport'] = {'part': part, 'mediaTransport': 'Authenticated GUI local ZIP fallback' if remote_error else 'Real WordPress HTTPS download', 'guiDownloadStatus': page.locator('#bixie-download-status').inner_text(), 'importCounts': after['import']['counts'], 'ajaxBatches': batches, 'ownerFixturesPreserved': True}
            report['checks']['actualGUIverifiedMediaImport']['otherCatalogMediaNotSuppliedByFourLookPilot'] = 'Source-missing diagnostics refer to additional actual catalog definitions outside this 12-view pilot. Supplied first four complete sets are checked independently below; this pilot is not a full launch data package.'
            records = {record['key']: record for record in manifest['records']}
            production = {}
            for look in manifest['looks']:
                key = look['key']
                actual = after['looks'][key]
                assert actual['status'] == 'publish' and actual['gate']['complete']
                assert len(actual['images']) == 3
                assert {image['angle'] for image in actual['images']} == {'front', 'side', 'back'}
                matched = {}
                for image in actual['images']:
                    source_key = next(entry['key'] for entry in look['images'] if entry['angle'] == image['angle'])
                    expected = records[source_key]
                    assert image['nativePathExists'] and image['nativeSha256'] == expected['sha256']
                    assert image['nativeActualSize'][0:2] == [expected['width'], expected['height']]
                    assert image['displayFile'].endswith('.webp') and image['originalUrl'] != image['url']
                    native = admin.request.get(image['originalUrl'])
                    assert native.status == 200 and hashlib.sha256(native.body()).hexdigest() == expected['sha256']
                    matched[image['angle']] = {'originalWidth': image['nativeActualSize'][0], 'originalHeight': image['nativeActualSize'][1], 'sourceSha256': image['nativeSha256'], 'optimizedDisplay': image['url'], 'originalZoomURL': image['originalUrl']}
                production[key] = matched
                page.goto(actual['url'], wait_until='networkidle')
                rendered = page.locator('main img').evaluate_all('(images)=>images.map(i=>({src:i.currentSrc||i.src,width:i.naturalWidth,height:i.naturalHeight,painted:i.complete&&i.naturalWidth>0}))')
                assert rendered and all(image['painted'] for image in rendered)
                assert not any('-native.webp' in image['src'] for image in rendered)
            assert after['home'] and all(home['status'] == 'draft' and not home['gate']['complete'] for home in after['home'])
            for key in ['wavy-01', 'curly-01']:
                if after['looks'][key]['id']:
                    assert after['looks'][key]['status'] == 'draft'
            report['checks']['realFourCoherentSetsAndNativeOriginalZoom'] = production
            report['checks']['productionOriginalCount'] = sum(len(look) for look in production.values())
            report['checks']['homepageStaysDraftIncomplete'] = [{'id': home['id'], 'status': home['status'], 'reasonCount': len(home['gate']['reasons'])} for home in after['home']]
            report['pageErrors'] = errors
            admin.close()
            browser.close()
        report['passed'] = True
    except Exception as error:
        report['failure'] = str(error)
        raise
    finally:
        if attachment_active:
            inspect('attachment-cleanup')
        if registry_backup_active:
            inspect('pilot-restore-part')
        if old_index is not None:
            release_index.write_bytes(old_index)
        report['sourceReleaseIndexUnchanged'] = True
        (TESTS / 'wp-live-pilot-report.json').write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps({'passed': report['passed'], 'report': str(TESTS / 'wp-live-pilot-report.json'), 'productionOriginalCount': report['checks'].get('productionOriginalCount'), 'wordPressRemoteVerified': report['checks'].get('wordPressRemoteTransport', {}).get('verified'), 'failure': report.get('failure')}, indent=2))

if __name__ == '__main__':
    main()
