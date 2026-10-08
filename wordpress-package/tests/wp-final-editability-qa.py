#!/usr/bin/env python3
"""Actual owner native Gutenberg SAVE, preserve-mode GUI import and exact restore."""
import argparse
import hashlib
import json
import subprocess
import traceback
from datetime import datetime, timezone
from playwright.sync_api import sync_playwright
from wp_final_common import inspect, authenticate, SITE, TESTS
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--phase',choices=['integration','engineering','final'],default='integration'); args=parser.parse_args()
    destination=TESTS/('wp-final-'+args.phase+'-editability-report.json')
    report={'generatedAtUTC':datetime.now(timezone.utc).isoformat(),'scope':'Actual authenticated native WordPress Gutenberg SAVE, owner edit preserved by real GUI import in default preserve mode, then exact original public content restored. Only actual project content; no new fixture media or looks.','phase':args.phase,'checks':{},'passed':False}
    def save(): destination.write_text(json.dumps(report,indent=2)+'\n')
    original=None; owner=None; browser=None; backup=Path('/workspace/wp-final-test/restore-backups/about-native-edit-qa.json')
    try:
        baseline=inspect(); record=baseline['pages']['about']; report['beforeCounts']=baseline['databaseCounts']; save()
        with sync_playwright() as playwright:
            browser=playwright.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
            owner, page=authenticate(browser)
            page.goto(record['editURL'],wait_until='networkidle'); page.wait_for_function('()=>window.wp?.data?.select("core/block-editor")?.getBlocks()?.length>0',timeout=60000)
            original=page.evaluate('async id=>await wp.apiFetch({path:"/wp/v2/pages/"+id+"?context=edit"})',record['id'])
            backup.parent.mkdir(exist_ok=True); original['contentSHA256']=hashlib.sha256(original['content']['raw'].encode()).hexdigest(); backup.write_text(json.dumps(original)); backup.chmod(0o600)
            marker='\n<!-- wp:paragraph --><p>Isolated owner edit preservation acceptance.</p><!-- /wp:paragraph -->'
            edited=original['content']['raw']+marker
            page.evaluate('content=>wp.data.dispatch("core/editor").editPost({content})',edited)
            page.evaluate('async()=>await wp.data.dispatch("core/editor").savePost()')
            page.wait_for_function('()=>!wp.data.select("core/editor").isSavingPost()&&!wp.data.select("core/editor").isEditedPostDirty()',timeout=60000)
            edited_state=inspect(); expected_hash=hashlib.sha256(edited.encode()).hexdigest()
            assert edited_state['pages']['about']['contentSHA256']==expected_hash
            report['checks']['actualNativeGutenbergOwnerEditSaved']=True; report['ownerEditedPageID']=record['id']; save()
            page.goto(SITE+'/wp-admin/tools.php?page=bixie-setup',wait_until='networkidle'); assert not page.locator('#bixie-overwrite').is_checked()
            if args.phase=='engineering': page.locator('#bixie-configure').uncheck()
            report['actualImportAJAXBatches']=[]
            def batch_observation(response):
                if '/wp-admin/admin-ajax.php' not in response.url:return
                request=response.request.post_data or ''
                action=next((value.split('=',1)[1] for value in request.split('&') if value.startswith('action=')),'')
                if action not in ['bixie_import_start','bixie_import_batch']:return
                try:
                    result=response.json();data=result.get('data',{})
                    report['actualImportAJAXBatches'].append({'action':action,'HTTP':response.status,'success':result.get('success'),'cursor':data.get('cursor'),'status':data.get('status')});save()
                except Exception:pass
            page.on('response',batch_observation)
            page.locator('#bixie-import-start').click()
            page.wait_for_function('()=>!document.querySelector("#bixie-import-start").disabled&&document.querySelector("#bixie-import-message").textContent.length>0',timeout=900000)
            assert page.locator('#bixie-import-message').inner_text().startswith('Import finished.'),page.locator('#bixie-import-message').inner_text()
            after=inspect(); assert after['import']['status']=='complete'
            assert after['pages']['about']['contentSHA256']==expected_hash
            assert edited_state['preservation']==after['preservation']
            report['checks']['realGUIImportPreservesActualNativeOwnerEditAndAllOtherContentRelationshipsSettings']=True; save()
            page.goto(record['editURL'],wait_until='networkidle'); page.wait_for_function('()=>window.wp?.apiFetch',timeout=60000)
            page.evaluate('async original=>await wp.apiFetch({path:"/wp/v2/pages/"+original.id,method:"POST",data:{content:original.content.raw,status:original.status}})',original)
            restored=inspect(); assert restored['preservation']==baseline['preservation']
            report['checks']['exactOwnerPageContentAndOriginalStatusesRestored']=True; report['afterCounts']=restored['databaseCounts']; original=None; backup.unlink(missing_ok=True)
            owner.close(); browser.close(); browser=None
        report['passed']=True
    except Exception as error:
        report['failure']=str(error); report['traceback']=traceback.format_exc(); raise
    finally:
        if original is not None:
            # Cleanup only the exact selected About ID; source media/looks are never removed.
            try:
                subprocess.run(['/workspace/wp-final-test/php',str(TESTS/'wp-final-restore-page.php'),'/workspace/wp-final-test/wordpress/wp-load.php',str(backup)],capture_output=True,text=True,check=True)
                report['failureCleanupExactOwnerContentRestored']=inspect()['pages']['about']['contentSHA256']==baseline['pages']['about']['contentSHA256']
                if report['failureCleanupExactOwnerContentRestored']: backup.unlink(missing_ok=True)
            except Exception as cleanup_error: report['failureCleanupError']=str(cleanup_error)
        save(); print(json.dumps({'passed':report['passed'],'phase':args.phase,'report':str(destination),'checks':report['checks'],'failure':report.get('failure')},indent=2),flush=True)


if __name__=='__main__': main()
