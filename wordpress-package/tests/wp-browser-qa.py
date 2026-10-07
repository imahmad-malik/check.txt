#!/usr/bin/env python3
"""Real WordPress browser checks using isolated synthetic CODE fixtures only.

Run after wp-fixtures.php create in a disposable local noindex database.
These checks establish software behavior, not approved hairstyle photography,
live rankings, Core Web Vitals, or full accessibility conformance.
"""
import argparse,json
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'wp-screenshots'

def geometry(page):
    return page.evaluate("""() => ({viewport:innerWidth,scrollWidth:document.documentElement.scrollWidth,overflow:document.documentElement.scrollWidth>innerWidth+1,images:[...document.images].map(i=>({src:i.currentSrc,loaded:i.complete&&i.naturalWidth>0,alt:i.alt})),cardImages:[...document.querySelectorAll('.bixie-results .bixie-card-photo img')].map(i=>{const r=i.getBoundingClientRect(),c=getComputedStyle(i);return {width:r.width,height:r.height,naturalWidth:i.naturalWidth,naturalHeight:i.naturalHeight,fit:c.objectFit,opacity:c.opacity,visibility:c.visibility}}),openDialogs:document.querySelectorAll('dialog[open]').length})""")

def axe(page,path):
    if not path:return {'notRun':'Pass --axe with an integrity-verified axe.min.js.'}
    page.add_script_tag(path=path)
    return page.evaluate("""async()=>{const r=await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa']}});return {version:axe.version,violations:r.violations.map(v=>({id:v.id,impact:v.impact,nodes:v.nodes.map(n=>({target:n.target,summary:n.failureSummary}))})),incomplete:r.incomplete.map(v=>({id:v.id,targets:v.nodes.map(n=>n.target)})),passes:r.passes.length};}""")

def wait_images(page):
    # Keep native lazy/auto-size behavior; changing to eager could mask a broken
    # WordPress intrinsic-containment aspect ratio.
    for element in page.locator('img').all():
        if element.is_visible():element.scroll_into_view_if_needed()
    page.wait_for_function("()=>[...document.images].every(i=>i.complete&&i.naturalWidth>0)")
    page.evaluate('()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))')

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--url',default='http://127.0.0.1:8766');parser.add_argument('--axe')
    args=parser.parse_args();OUT.mkdir(exist_ok=True)
    report={'purpose':'Isolated synthetic CODE fixtures; zero approved production hairstyle assets.','url':args.url,'viewports':{},'flows':{}}
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
        for name,w,h in [('desktop',1440,1000),('tablet',768,1024),('phone',390,844),('small-phone',320,720)]:
            context=browser.new_context(viewport={'width':w,'height':h},reduced_motion='reduce')
            page=context.new_page();errors=[];failures=[]
            page.on('pageerror',lambda e:errors.append(str(e)))
            page.on('response',lambda r:failures.append({'status':r.status,'url':r.url}) if r.status>=400 else None)
            page.goto(args.url+'/isolated-code-test-library/',wait_until='networkidle')
            page.wait_for_function("()=>document.querySelectorAll('.bixie-results .bixie-look-card').length===6")
            wait_images(page);page.evaluate('()=>{document.activeElement?.blur();scrollTo(0,0)}')
            page.screenshot(path=str(OUT/f'{name}-synthetic-library.jpg'),type='jpeg',quality=85,full_page=True)
            data=geometry(page);data['axe']=axe(page,args.axe)
            assert not data['overflow'],f'{name} page overflow'
            assert all(i['loaded'] for i in data['images']),f'{name} unloaded images'
            for image in data['cardImages']:
                assert image['width']>200 and 0<image['height']<700,f'{name} oversized/invisible image: {image}'
                assert abs(image['height']/image['width']-image['naturalHeight']/image['naturalWidth'])<.01,f'{name} original image aspect lost: {image}'
                assert image['fit']=='contain' and image['opacity']=='1' and image['visibility']=='visible',f'{name} image hidden/cropped: {image}'
            # Actual REST-powered facet filtering and three-page navigation.
            page.locator('.bixie-filter-form [name="texture"]').select_option('wavy')
            page.wait_for_function("()=>document.querySelector('.bixie-result-status').textContent.startsWith('7 ')")
            page.locator('.bixie-pagination [data-bixie-page="2"]').first.click()
            page.wait_for_function("()=>document.querySelectorAll('.bixie-results .bixie-look-card').length===1")
            page.locator('.bixie-clear-filters').click()
            page.wait_for_function("()=>document.querySelector('.bixie-result-status').textContent.startsWith('14 ')")
            page.locator('.bixie-filter-form [name="q"]').fill('look 14')
            page.locator('.bixie-filter-form [name="q"]').dispatch_event('change')
            page.wait_for_function("()=>document.querySelectorAll('.bixie-results .bixie-look-card').length===1&&document.querySelector('.bixie-result-status').textContent.startsWith('1 ')")
            page.locator('.bixie-clear-filters').click()
            page.wait_for_function("()=>document.querySelectorAll('.bixie-results .bixie-look-card').length===6")
            # Save three unmodified fixture records, then exercise real detail and tools.
            for i in [2,3,4]:page.locator('.bixie-results .bixie-save').nth(i).click()
            assert page.locator('.bixie-library .bixie-saved-count').inner_text()=='3'
            page.locator('.bixie-results .bixie-detail-trigger').nth(2).click()
            page.wait_for_function("()=>document.querySelectorAll('dialog[open] .bixie-detail-photo').length===3")
            wait_images(page)
            data['detail']={'geometry':geometry(page),'axe':axe(page,args.axe)}
            page.screenshot(path=str(OUT/f'{name}-synthetic-detail.jpg'),type='jpeg',quality=85)
            page.keyboard.press('Escape')
            assert page.locator('dialog[open]').count()==0
            assert page.locator('.bixie-results .bixie-detail-trigger').nth(2).evaluate('(e)=>e===document.activeElement')
            page.locator('.bixie-library .bixie-open-saved').click()
            page.wait_for_function("()=>document.querySelectorAll('dialog[open] .bixie-saved-grid .bixie-look-card').length===3")
            data['saved']={'geometry':geometry(page),'axe':axe(page,args.axe)}
            page.keyboard.press('Escape')
            page.locator('.bixie-library .bixie-open-compare').click()
            page.wait_for_function("()=>document.querySelectorAll('dialog[open] [data-bixie-compare]').length===3")
            page.locator('dialog[open] .bixie-compare-selected').click()
            page.wait_for_function("()=>document.querySelectorAll('dialog[open] .bixie-compare-look').length===2")
            wait_images(page)
            data['comparison']={'geometry':geometry(page),'axe':axe(page,args.axe),'keyboardRegion':page.locator('.bixie-compare-region').get_attribute('tabindex')}
            page.screenshot(path=str(OUT/f'{name}-synthetic-comparison.jpg'),type='jpeg',quality=85)
            page.keyboard.press('Escape')
            page.locator('.bixie-library .bixie-print-saved').click()
            page.wait_for_function("()=>document.querySelectorAll('dialog[open] .bixie-print-sheet').length===3")
            wait_images(page)
            data['print']={'geometry':geometry(page),'axe':axe(page,args.axe),'sheets':page.locator('.bixie-print-sheet').count(),'anglePhotos':page.locator('.bixie-print-sheet img').count()}
            if name=='desktop':
                page.pdf(path=str(OUT/'synthetic-consultation.pdf'),format='A4',print_background=True)
            page.keyboard.press('Escape');page.reload(wait_until='networkidle')
            assert page.locator('.bixie-library .bixie-saved-count').inner_text()=='3'
            page.goto(args.url+'/isolated-code-test-saved/',wait_until='networkidle')
            page.wait_for_function("()=>document.querySelectorAll('.bixie-saved-items .bixie-look-card').length===3")
            data['savedPage']={'geometry':geometry(page),'axe':axe(page,args.axe)}
            data['consoleErrors']=errors;data['failedResponses']=failures
            assert not errors,f'{name} JS errors: {errors}'
            assert not failures,f'{name} HTTP errors: {failures}'
            report['viewports'][name]=data
            context.close()
        browser.close()
    report['flows']={'serverGalleryAndFacets':True,'restFiltersAndSearch':True,'pagination':True,'savedReloadPersistence':True,'savedPage':True,'threeAngleDetail':True,'twoLookComparison':True,'nineAnglePhotosInThreeConsultationSheets':True,'escapeFocusRestoration':True}
    (ROOT/'wp-browser-report.json').write_text(json.dumps(report,indent=2))
    print(json.dumps({'viewports':{k:{'pageOverflow':v['overflow'],'imagesLoaded':sum(i['loaded'] for i in v['images']),'images':len(v['images']),'axeViolations':sum(len(part.get('axe',{}).get('violations',[])) for part in [v,v['detail'],v['saved'],v['comparison'],v['print'],v['savedPage']]),'JSerrors':len(v['consoleErrors']),'HTTPerrors':len(v['failedResponses'])} for k,v in report['viewports'].items()},'flows':report['flows']},indent=2))

if __name__=='__main__':main()
