#!/usr/bin/env python3
"""Actual final-source SSR, collection geometry, HTTP and native-editor acceptance.

Use --phase integration for explicitly partial sources; final asserts all counts.
No cookies, credentials, database or private WordPress configuration are packaged.
"""
import argparse
import hashlib
import io
import json
import re
import traceback
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

from PIL import Image, ImageChops, ImageStat
from playwright.sync_api import sync_playwright

from wp_final_common import inspect, authenticate, SITE, TESTS


class PageHTML(HTMLParser):
    def __init__(self, text):
        super().__init__(); self.links = []; self.graphs = []; self.script = None
        self.feed(text)
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'a' and attrs.get('href'): self.links.append(attrs['href'])
        if tag == 'script' and attrs.get('type') == 'application/ld+json': self.script = ''
    def handle_data(self, data):
        if self.script is not None: self.script += data
    def handle_endtag(self, tag):
        if tag == 'script' and self.script is not None:
            try: self.graphs.append(json.loads(self.script))
            finally: self.script = None


def edge_check(painted, original):
    image = Image.open(io.BytesIO(painted)).convert('RGB')
    source = Image.open(io.BytesIO(original)).convert('RGB').resize(image.size, Image.Resampling.BILINEAR)
    values = []
    for y0, y1 in [(.015, .065), (.935, .985)]:
        box = (round(image.width * .1), round(image.height * y0), round(image.width * .9), round(image.height * y1))
        values.append(ImageStat.Stat(ImageChops.difference(image.crop(box), source.crop(box))).mean)
    return {'edgeMeanAbsoluteRGBDifference': values, 'fullSourceEdgesPainted': all(max(value) < 25 for value in values), 'nonFlatPixels': max(ImageStat.Stat(image).var) > 100}


def painted_images(page, selector, context, expected=None, sample_edges=True):
    elements = page.locator(selector)
    if expected is not None: assert elements.count() == expected, (selector, elements.count(), expected)
    observations = []
    for index, element in enumerate(elements.all()):
        element.scroll_into_view_if_needed()
        element.evaluate('async e=>{await e.decode();}')
        observation = element.evaluate(r'''e=>{const r=e.getBoundingClientRect(),s=getComputedStyle(e);return {element:[r.width,r.height],natural:[e.naturalWidth,e.naturalHeight],source:e.currentSrc||e.src,objectFit:s.objectFit,aspectRatio:s.aspectRatio,opacity:s.opacity,visibility:s.visibility,transform:s.transform,containIntrinsicSize:s.containIntrinsicSize,attachmentID:(e.className.match(/wp-image-(\d+)/)||[])[1]||null};}''')
        assert observation['element'][0] > 0 and observation['element'][1] > 0, observation
        assert abs(observation['element'][1] / observation['element'][0] - observation['natural'][1] / observation['natural'][0]) < .015, observation
        assert observation['objectFit'] == 'contain' and observation['opacity'] == '1' and observation['visibility'] == 'visible' and observation['transform'] == 'none', observation
        if sample_edges and index < 3:
            response = context.request.get(observation['source']); assert response.status == 200
            observation['pixels'] = edge_check(element.screenshot(), response.body())
            assert observation['pixels']['fullSourceEdgesPainted'] and observation['pixels']['nonFlatPixels'], observation
        observations.append(observation)
    return observations


def editor_check(browser,data,report,save):
    admin, editor = authenticate(browser)
    representative = data['pages']['about']; editor.goto(representative['editURL'],wait_until='networkidle')
    editor.wait_for_function('()=>window.wp?.data?.select("core/block-editor")?.getBlocks()?.length>0',timeout=60000)
    expected_ids = [record['id'] for kind in ['pages','looks'] for record in data[kind].values()]
    content = editor.evaluate('''async expected=>{const pages=await wp.apiFetch({path:'/wp/v2/pages?context=edit&per_page=100&status[]=publish&status[]=draft&status[]=private&status[]=pending'});const looks1=await wp.apiFetch({path:'/wp/v2/bixie_look?context=edit&per_page=100&page=1&status[]=publish&status[]=draft&status[]=private&status[]=pending'});const looks2=looks1.length===100?await wp.apiFetch({path:'/wp/v2/bixie_look?context=edit&per_page=100&page=2&status[]=publish&status[]=draft&status[]=private&status[]=pending'}):[];const flatten=bs=>bs.flatMap(b=>[b,...flatten(b.innerBlocks||[])]);return [...pages,...looks1,...looks2].filter(p=>expected.includes(p.id)).map(p=>{const bs=wp.blocks.parse(p.content.raw),flat=flatten(bs),round=flatten(wp.blocks.parse(wp.blocks.serialize(bs)));return {id:p.id,type:p.type,status:p.status,totalBlocks:flat.length,invalid:flat.filter(b=>b.isValid===false).map(b=>b.name),roundtripInvalid:round.filter(b=>b.isValid===false).map(b=>b.name)};});}''',expected_ids)
    report['nativeGutenbergRegisteredParseAndRoundtrip'] = content; save()
    assert not any(item['invalid'] or item['roundtripInvalid'] for item in content), [item for item in content if item['invalid'] or item['roundtripInvalid']]
    assert len(content) == len(expected_ids), (len(content),len(expected_ids))
    report['checks']['actualRegisteredGutenbergNativeParseAndRoundtripNoInvalidBlocks'] = True
    admin.close()


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--phase', choices=['integration', 'engineering', 'final'], default='integration'); parser.add_argument('--editor', action='store_true'); parser.add_argument('--editor-only', action='store_true')
    args = parser.parse_args(); destination = TESTS / ('wp-final-' + args.phase + '-browser-report.json')
    report = {'generatedAtUTC': datetime.now(timezone.utc).isoformat(), 'scope': 'Actual sources in separate local noindex WordPress. No synthetic fixture records. Public HTTP, natural geometry, selected painted photo edges, GET no-JavaScript forms and actual registered native Gutenberg parser.', 'phase': args.phase, 'checks': {}, 'collections': {}, 'passed': False}
    def save(): destination.write_text(json.dumps(report, indent=2) + '\n')
    try:
        data = inspect()
        if args.editor_only:
            previous=json.loads(destination.read_text())
            assert previous['databaseCounts']==data['databaseCounts']
            for check in ['everyActualPublishedPageAndLookHTTP200','allRenderedInternalHTTPLinksResolve','everyImportedNativeSourceHTTPHashAndReviewGateVerified','everyReadyCollection21ActualFrontSideBackViewsAtDesktopAndPhone','actualSideBackDetailSelectionAndEscapeFocus','nativeGETFiltersWorkWithJavaScriptDisabled']: assert previous['checks'][check] is True
            report=previous; report['passed']=False; report.pop('failure',None); report.pop('traceback',None); report['continuedAffectedEditorCheckOnly']=True; save()
            with sync_playwright() as playwright:
                browser=playwright.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
                editor_check(browser,data,report,save); browser.close()
            report['passed']=True
            return
        report['databaseCounts'] = data['databaseCounts']; save()
        if args.phase == 'final':
            for key, value in [('looks',154),('publishedLooks',154),('photos',487),('films',1),('pages',42),('readyCollections',22),('readyGuides',7)]: assert data['databaseCounts'][key] == value, (key,data['databaseCounts'][key])
            assert data['home']['status'] == 'publish' and data['home']['gate']['complete'] and len(data['home']['uniquePhotoIDs']) == 77 and len(data['home']['visiblePhotoIDs']) == 78 and data['home']['sectionCount'] == 22
            assert data['settings']['show_on_front'] == 'page' and int(data['settings']['page_on_front']) == data['home']['id']
            assert data['pages']['privacy']['status'] == 'draft' and data['pages']['contact']['status'] == 'draft'
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox'])
            context = browser.new_context(viewport={'width':1440,'height':1000}, reduced_motion='reduce')
            public = []; links = set(); schema_types = {}; source_requests = []
            for kind in ['pages','looks']:
                for key, record in data[kind].items():
                    if record['status'] != 'publish': continue
                    response = context.request.get(record['url']); assert response.status == 200, (key,response.status)
                    html = PageHTML(response.text()); public.append({'key':key,'status':response.status,'url':response.url}); response.dispose()
                    links.update(link.split('#')[0] for link in html.links if link.startswith(SITE) and urlsplit(link).path not in ['/wp-login.php'] and '/wp-admin/' not in link)
                    graph = [node for item in html.graphs for node in item.get('@graph',[])]; schema_types[key] = [node.get('@type') for node in graph]
                    if kind == 'looks':
                        creative = next(node for node in graph if node.get('@type') == 'CreativeWork'); assert len(creative['image']) == 3
                        assert {image['contentUrl'] for image in creative['image']} == {image['originalUrl'] for image in record['images']}
                    if key in data['guides']:
                        article = next(node for node in graph if node.get('@type') == 'Article'); assert len(article['image']) == len(data['guides'][key]['nativePhotoIDs'])
            report['publicHTTP'] = public; report['schemaTypes'] = schema_types; report['checks']['everyActualPublishedPageAndLookHTTP200'] = True; save()
            failed_links = []
            already_verified = {record['url'] for record in public}
            separately_requested = 0
            for link in sorted(links - already_verified):
                response = context.request.get(link)
                separately_requested += 1
                if response.status != 200: failed_links.append({'url':link,'status':response.status})
                response.dispose()
            report['internalLinkHTTP'] = {'uniqueURLs':len(links),'alreadyVerifiedPublicDestinations':len(links & already_verified),'additionalRealHTTPRequests':separately_requested,'failures':failed_links}; save(); assert not failed_links
            report['checks']['allRenderedInternalHTTPLinksResolve'] = True
            for key, attachment in data['attachments'].items():
                assert attachment['sourceExists'] and attachment['displayExists'] and attachment['approved'] and attachment['qualified'], (key,attachment)
                assert attachment['sourceSHA256'] == attachment['expectedSHA256'], key
                response = context.request.get(attachment['nativeURL']); assert response.status == 200 and hashlib.sha256(response.body()).hexdigest() == attachment['sourceSHA256'], key
                response.dispose()
                source_requests.append({'key':key,'HTTP':200,'actualNativeSourceSHA256MatchesManifest':True,'nativeSize':attachment['nativeSize']})
            report['nativeOriginalHTTP'] = source_requests; report['checks']['everyImportedNativeSourceHTTPHashAndReviewGateVerified'] = True; save()
            first_collection = None
            for name,width,height in [('desktop',1440,1000),('phone',390,844)]:
                page = context.new_page(); page.set_viewport_size({'width':width,'height':height}); errors = []; failures = []
                page.on('pageerror',lambda error:errors.append(str(error)))
                page.on('response',lambda response:failures.append({'url':response.url,'status':response.status}) if response.status>=400 else None)
                for slug, collection in data['collections'].items():
                    if not collection['gate']['complete']: continue
                    first_collection = first_collection or collection['url']
                    response = page.goto(collection['url'],wait_until='networkidle'); assert response.status == 200
                    assert page.locator('.bixie-results .bixie-look-card').count() == 7
                    observations = painted_images(page,'.bixie-results .bixie-look-card img',context,21)
                    angles = page.locator('.bixie-results .bixie-card-angle a').evaluate_all('es=>es.map(e=>e.dataset.angle)'); assert angles == ['side','back']*7
                    assert not page.locator('.bixie-empty').count()
                    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
                    report['collections'].setdefault(slug,{})[name] = {'actualPhotos':21,'actualCompleteLooks':7,'sideBackAngleOrder':angles,'naturalGeometry':observations,'overflow':False}; save()
                assert not errors and not failures, (errors,failures)
                page.close()
            report['checks']['everyReadyCollection21ActualFrontSideBackViewsAtDesktopAndPhone'] = True
            assert first_collection
            page = context.new_page(); page.goto(first_collection,wait_until='networkidle')
            for angle in ['side','back']:
                trigger = page.locator('.bixie-card-angle [data-angle="'+angle+'"]').first; trigger.click()
                page.wait_for_function('()=>document.querySelectorAll("dialog[open] .bixie-detail-photo").length===3')
                actual_angle = page.locator('dialog[open] .bixie-detail-photo figcaption').first.inner_text().lower(); assert angle in actual_angle, actual_angle
                painted_images(page,'dialog[open] .bixie-detail-photo img',context,3)
                page.keyboard.press('Escape'); assert trigger.evaluate('e=>e===document.activeElement')
            report['checks']['actualSideBackDetailSelectionAndEscapeFocus'] = True
            page.close()
            report['actualSavedComparePrintFlows'] = {}
            for name,width,height in [('desktop',1440,1000),('phone',390,844)]:
                tools = browser.new_context(viewport={'width':width,'height':height},reduced_motion='reduce')
                page = tools.new_page(); page.goto(first_collection,wait_until='networkidle')
                for index in range(3): page.locator('.bixie-results .bixie-save').nth(index).click()
                assert page.locator('.bixie-library .bixie-saved-count').inner_text() == '3'
                page.locator('.bixie-open-saved').click(); page.wait_for_function('()=>document.querySelectorAll("dialog[open] .bixie-saved-grid .bixie-look-card").length===3')
                saved_photos = painted_images(page,'dialog[open] .bixie-saved-grid .bixie-look-card img',tools,3)
                page.keyboard.press('Escape'); page.locator('.bixie-open-compare').click()
                page.wait_for_function('()=>document.querySelectorAll("dialog[open] [data-bixie-compare]").length===3')
                page.locator('dialog[open] .bixie-compare-selected').click(); page.wait_for_function('()=>document.querySelectorAll("dialog[open] .bixie-compare-look").length===2')
                comparison_photos = painted_images(page,'dialog[open] .bixie-compare-look img',tools,6)
                page.keyboard.press('Escape'); page.locator('.bixie-print-saved').click()
                page.wait_for_function('()=>document.querySelectorAll("dialog[open] .bixie-print-sheet").length===3')
                print_photos = painted_images(page,'dialog[open] .bixie-print-sheet img',tools,9)
                page.keyboard.press('Escape'); page.reload(wait_until='networkidle'); assert page.locator('.bixie-library .bixie-saved-count').inner_text() == '3'
                page.goto(data['pages']['saved-looks']['url'],wait_until='networkidle'); page.wait_for_function('()=>document.querySelectorAll(".bixie-saved-items .bixie-look-card").length===3')
                report['actualSavedComparePrintFlows'][name] = {'threeActualSavedLooksPersistAfterReload':True,'nativeSavedPageThreeActualCards':True,'savedPhotos':saved_photos,'twoLookSixAngleComparisonPhotos':comparison_photos,'threeSheetNineAnglePrintPhotos':print_photos}; save()
                tools.close()
            report['checks']['actualSavedReloadNativeSavedPageSixAngleCompareNineAnglePrintAtDesktopAndPhone'] = True
            nojs = browser.new_context(java_script_enabled=False,viewport={'width':390,'height':844})
            page = nojs.new_page(); page.goto(first_collection,wait_until='networkidle'); assert page.locator('.bixie-results img').count() == 21
            page.locator('.bixie-filter-form [name="sort"]').select_option('title'); page.locator('.bixie-filter-form button[type="submit"]').click(); page.wait_for_load_state('networkidle')
            assert page.locator('.bixie-results img').count() == 21 and 'sort=title' in page.url
            report['noJavaScriptGET'] = {'realBrowserJavaScriptDisabled':True,'sortFormSubmitted':True,'actual21PhotosRemain':True,'url':page.url}; report['checks']['nativeGETFiltersWorkWithJavaScriptDisabled'] = True; save()
            nojs.close()
            if args.editor: editor_check(browser,data,report,save)
            context.close(); browser.close()
        report['passed'] = True
    except Exception as error:
        report['failure'] = str(error); report['traceback'] = traceback.format_exc(); raise
    finally:
        save(); print(json.dumps({'passed':report['passed'],'phase':args.phase,'report':str(destination),'checks':report['checks'],'failure':report.get('failure')},indent=2),flush=True)


if __name__ == '__main__': main()
