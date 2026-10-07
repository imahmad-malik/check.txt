#!/usr/bin/env python3
"""Actual owner admin/AJAX and no-JS multipart upload tests; synthetic data only."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parent
SITE='http://127.0.0.1:8766'
ARCHIVE=Path('/workspace/wp-test/artifacts/isolated-qa-browser-upload.zip')

def main():
    report={'purpose':'Isolated unapproved synthetic CODE media upload; not hairstyle photographs or launch assets.','checks':{}}
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
        admin=browser.new_context(storage_state='/workspace/wp-test/qa-auth-state.json')
        page=admin.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        response=page.goto(SITE+'/wp-admin/tools.php?page=bixie-setup',wait_until='networkidle')
        assert response.status==200 and page.locator('#adminmenu').count()==1
        assert page.locator('#bixie-bundle-files').get_attribute('multiple') is not None
        nonce=page.evaluate('window.BixieBundles.nonce')
        invalid=admin.request.post(SITE+'/wp-admin/admin-ajax.php',form={'action':'bixie_media_bundle_status','nonce':'invalid-test-nonce'})
        assert invalid.status==403;report['checks']['invalidNonce403']=True
        subscriber=browser.new_context(storage_state='/workspace/wp-test/qa-subscriber-state.json')
        own_nonce=json.loads(Path('/workspace/wp-test/qa-subscriber-nonce.json').read_text())['nonce']
        denied=subscriber.request.post(SITE+'/wp-admin/admin-ajax.php',form={'action':'bixie_media_bundle_status','nonce':own_nonce})
        assert denied.status==403;report['checks']['authenticatedSubscriberCapability403']=True;subscriber.close()
        anonymous=browser.new_context();denied=anonymous.request.post(SITE+'/wp-admin/admin-ajax.php',form={'action':'bixie_media_bundle_upload','nonce':nonce})
        assert denied.status>=400;report['checks']['anonymousUploadDenied']=True;anonymous.close()
        # Real input selection, XHR multipart transfer, server verification and UI state.
        page.locator('#bixie-bundle-files').set_input_files(str(ARCHIVE));page.locator('#bixie-bundle-upload').click()
        page.wait_for_function("()=>document.querySelector('#bixie-bundle-status').textContent.startsWith('1 of 1 selected part(s) verified')")
        assert 'isolated-qa-browser-upload' in page.locator('#bixie-bundle-list').inner_text()
        assert page.locator('#bixie-bundle-upload').is_enabled();report['checks']['realAdminMultipartUploadVerified']=True
        page.reload(wait_until='networkidle');assert 'isolated-qa-browser-upload' in page.locator('#bixie-bundle-list').inner_text();report['checks']['verifiedPartPersistsReload']=True
        page.locator('#bixie-bundle-files').set_input_files(str(ARCHIVE));page.locator('#bixie-bundle-upload').click()
        page.wait_for_function("()=>document.querySelector('#bixie-bundle-status').textContent.startsWith('1 of 1 selected part(s) verified')")
        parts=json.loads(page.locator('#bixie-bundle-list').inner_text());assert sum(part['bundle_id']=='isolated-qa-browser-upload' for part in parts)==1;report['checks']['samePartUploadIdempotent']=True
        # Separate actual owner GUI importer, default preserve mode, no automatic publish.
        assert not page.locator('#bixie-overwrite').is_checked()
        page.locator('#bixie-import-start').click();page.wait_for_function("()=>document.querySelector('#bixie-import-message').textContent.startsWith('Import finished.')",timeout=60000)
        state=json.loads(page.locator('#bixie-import-log').inner_text());assert state['status']=='complete' and state['counts']['errors']==0 and state['counts']['media']==3
        report['checks']['realAdminGuiImportComplete']=True;report['importCounts']=state['counts']
        assert not errors;report['pageErrors']=[]
        # Native multipart fallback remains usable with scripting disabled.
        native=browser.new_context(storage_state='/workspace/wp-test/qa-auth-state.json',java_script_enabled=False)
        fallback=native.new_page();fallback.goto(SITE+'/wp-admin/tools.php?page=bixie-setup',wait_until='networkidle')
        fallback.locator('#bixie-bundle-files').set_input_files(str(ARCHIVE));fallback.locator('#bixie-bundle-upload').click();fallback.wait_for_url('**/tools.php?page=bixie-setup#bixie-bundles')
        assert 'Verified: isolated-qa-browser-upload' in fallback.locator('#bixie-bundle-status').inner_text();report['checks']['noJavascriptNativeFormVerified']=True
        native.close();admin.close();browser.close()
    report['status']='passed';(ROOT/'wp-admin-upload-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))

if __name__=='__main__':main()
