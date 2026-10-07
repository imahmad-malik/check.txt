#!/usr/bin/env python3
"""Actual native header/footer links and imported draft-link render gate."""
import json,urllib.parse,urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright

def main():
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=browser.new_page()
        page.goto('http://127.0.0.1:8766/isolated-code-test-library/',wait_until='networkidle')
        links=page.locator('header a[href],footer a[href]').evaluate_all('es=>es.map(e=>({label:e.textContent.trim(),href:e.href}))');results=[]
        for link in links:
            parsed=urllib.parse.urlparse(link['href'])
            if parsed.hostname!='127.0.0.1' or parsed.fragment:continue
            with urllib.request.urlopen(link['href'],timeout=20) as response:status=response.status
            assert status==200,(link,status);results.append({'label':link['label'],'path':parsed.path,'status':status})
        assert all(item['path'] not in ['/privacy/','/contact/'] for item in results)
        report={'status':'passed','publicNativeHeaderFooterLinks':results,'knownImportedDraftPrivacyContactLinksSuppressed':True,'rawOwnerEditableBlocksPreserved':'See theme-native-block-report.json; public render gate does not rewrite editor data.'}
        Path(__file__).with_name('wp-navigation-report.json').write_text(json.dumps(report,indent=2))
        print(json.dumps({'status':'passed','headerFooterHTTP200Links':len(results),'draftPrivacyContactHrefAbsent':True}));browser.close()

if __name__=='__main__':main()
