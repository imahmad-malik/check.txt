#!/usr/bin/env python3
"""Live collection SSR/AJAX photo coverage using synthetic CODE fixtures only."""
import io,json,re
from pathlib import Path
from PIL import Image
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parent
def photos(page):
    elements=page.locator('.bixie-results .bixie-look-card img');assert elements.count()==21
    result=[]
    for element in elements.all():
        element.scroll_into_view_if_needed();element.evaluate('e=>e.decode()');page.evaluate('()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))')
        state=element.evaluate('e=>{const r=e.getBoundingClientRect(),c=getComputedStyle(e);return {width:r.width,height:r.height,natural:[e.naturalWidth,e.naturalHeight],fit:c.objectFit,opacity:c.opacity,visibility:c.visibility,containIntrinsicSize:c.containIntrinsicSize,src:e.currentSrc}}')
        assert state['width']>20 and state['height']>0 and state['height']<700,state
        assert abs(state['height']/state['width']-state['natural'][1]/state['natural'][0])<.01,state
        assert state['fit']=='contain' and state['opacity']=='1' and state['visibility']=='visible' and state['containIntrinsicSize']=='none',state
        match=re.search(r'isolated-qa-(\d+)-(front|side|back)\.png',state['src']);assert match,state
        i=int(match[1]);angle=['front','side','back'].index(match[2]);expected=(180+i*3,150+angle*15,145+i)
        rendered=Image.open(io.BytesIO(element.screenshot())).convert('RGB');actual=rendered.getpixel((int(rendered.width*.05),int(rendered.height*.25)));assert max(abs(a-b) for a,b in zip(actual,expected))<=8,(state,actual,expected)
        result.append({'actualAngle':match[2],'visibleDimensions':[round(state['width'],2),round(state['height'],2)],'originalAspectPreserved':True,'paintedSyntheticPixelVerified':True})
    return result

def main():
    report={'purpose':'Actual WordPress collection code verification. Synthetic panoramic canvases are not hairstyle photography or launch assets.','viewports':{}}
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
        for name,w,h in [('desktop',1440,1000),('phone',390,844)]:
            page=browser.new_page(viewport={'width':w,'height':h},reduced_motion='reduce');errors=[];failures=[];page.on('pageerror',lambda e:errors.append(str(e)));page.on('response',lambda r:failures.append(r.status) if r.status>=400 else None)
            page.goto('http://127.0.0.1:8766/isolated-code-test-collection/',wait_until='networkidle');page.wait_for_function('()=>document.querySelectorAll(".bixie-results .bixie-look-card").length===7')
            initial=photos(page);assert [r['actualAngle'] for r in initial]==['front','side','back']*7
            page.locator('.bixie-pagination :is([data-bixie-page="2"],[data-page="2"])').first.click();page.wait_for_function('()=>document.querySelector(".bixie-library").dataset.page==="2"');second=photos(page)
            page.locator('.bixie-filter-form [name="texture"]').select_option('wavy');page.wait_for_function('()=>document.querySelector(".bixie-result-status").textContent.startsWith("7 ")');filtered=photos(page)
            for angle in ['side','back']:
                trigger=page.locator('.bixie-card-angle [data-angle="'+angle+'"]').first;trigger.click();page.wait_for_function('()=>document.querySelectorAll("dialog[open] .bixie-detail-photo").length===3')
                assert page.locator('dialog[open] .bixie-detail-photo img').first.get_attribute('src').endswith('-'+angle+'.png');page.keyboard.press('Escape');assert trigger.evaluate('e=>e===document.activeElement')
            assert not errors and not failures;assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
            report['viewports'][name]={'serverSevenLooksPhotos':len(initial),'pageTwoPhotos':len(second),'ajaxFacetPhotos':len(filtered),'eachOriginalAnglePaintedAndUncropped':True,'sideClickOpensSideFirst':True,'backClickOpensBackFirst':True,'escapeReturnsFocus':True,'consoleErrors':errors,'HTTPerrors':failures,'overflow':False};page.close()
        browser.close()
    report['status']='passed';(ROOT/'wp-collection-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))

if __name__=='__main__':main()
