#!/usr/bin/env python3
"""Actual WordPress image layout/pixel checks using labeled synthetic canvases.

Requires wp-portrait-fixture.php create. No image is hairstyle photography or
approved launch media. Check both portrait and panoramic original ratios.
"""
import argparse,io,json
from pathlib import Path
from PIL import Image
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'wp-screenshots'

def sample(image,x,y):
    return list(image.getpixel((min(image.width-1,int(image.width*x)),min(image.height-1,int(image.height*y))))[:3])

def near(actual,expected):
    return max(abs(a-b) for a,b in zip(actual,expected))<=8

def inspect(page,query,expected,native):
    page.goto('http://127.0.0.1:8766/isolated-code-test-library/?q='+query,wait_until='networkidle')
    page.wait_for_function("()=>document.querySelectorAll('.bixie-card-photo img').length>=1")
    element=page.locator('.bixie-card-photo img').first;element.scroll_into_view_if_needed()
    page.wait_for_function("()=>document.querySelector('.bixie-card-photo img').complete&&document.querySelector('.bixie-card-photo img').naturalWidth>0")
    page.evaluate('()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(()=>requestAnimationFrame(r))))')
    state=element.evaluate("""e=>{const r=e.getBoundingClientRect(),c=getComputedStyle(e);return {width:r.width,height:r.height,natural:[e.naturalWidth,e.naturalHeight],aspectRatio:c.aspectRatio,fit:c.objectFit,opacity:c.opacity,visibility:c.visibility,display:c.display,contain:c.contain,containIntrinsicSize:c.containIntrinsicSize,sizes:e.sizes};}""")
    assert state['natural']==native,state
    assert state['width']>200 and state['height']>0,state
    assert abs((state['height']/state['width'])-(native[1]/native[0]))<.01,state
    assert state['height']<700,state
    assert state['fit']=='contain' and state['opacity']=='1' and state['visibility']=='visible',state
    assert state['containIntrinsicSize']=='none',state
    rendered=Image.open(io.BytesIO(element.screenshot())).convert('RGB')
    colors={name:sample(rendered,*coords) for name,coords,color in expected}
    for name,coords,color in expected:assert near(colors[name],color),(state,name,colors[name],color)
    state['paintedPixels']=colors;state['edgeColorsVisible']=True
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
    return state

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--report',default=str(ROOT/'wp-image-display-report.json'));args=parser.parse_args();OUT.mkdir(exist_ok=True)
    report={'purpose':'Isolated synthetic CODE canvases. Not approved hairstyle media or a production visual audit.','regression':'WordPress auto sizes intrinsic containment must preserve original image aspect and paint all image edges.','viewports':{}}
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
        for name,w,h in [('desktop',1440,1000),('tablet',768,1024),('phone',390,844),('small-phone',320,720)]:
            page=browser.new_page(viewport={'width':w,'height':h},reduced_motion='reduce')
            portrait=inspect(page,'PORTRAIT',[('top',(0.05,.02),(255,220,20)),('middle',(.05,.5),(30,100,150)),('bottom',(.05,.98),(230,50,50))],[1048,1310])
            page.evaluate('()=>{document.activeElement?.blur();scrollTo(0,0)}');page.screenshot(path=str(OUT/(name+'-synthetic-portrait-layout.jpg')),type='jpeg',quality=85,full_page=True)
            panoramic=inspect(page,'look%2001',[('background',(.05,.25),(183,150,146))],[7680,512])
            report['viewports'][name]={'portrait':portrait,'panoramic':panoramic,'overflow':False};page.close()
        browser.close()
    report['status']='passed';Path(args.report).write_text(json.dumps(report,indent=2))
    print(json.dumps({'status':'passed','viewports':{name:{'portraitPixels':[round(r['portrait']['width'],2),round(r['portrait']['height'],2)],'panoramicPixels':[round(r['panoramic']['width'],2),round(r['panoramic']['height'],2)],'paintedEdges':True} for name,r in report['viewports'].items()}},indent=2))

if __name__=='__main__':main()
