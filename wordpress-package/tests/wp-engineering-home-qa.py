#!/usr/bin/env python3
"""Actual authenticated incomplete Home preview; never publishes it."""
import base64
import importlib.util
import json
import traceback
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import sync_playwright
from wp_final_common import inspect, authenticate, SITE, TESTS

def load(name, filename):
    spec=importlib.util.spec_from_file_location(name,TESTS/filename)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

utilities=load('engineering_film_utilities','wp-production-home-film-qa.py')
browser_utilities=load('engineering_geometry_utilities','wp-final-browser-qa.py')
AUTH=Path('/workspace/wp-final-test/qa-auth-state.json')

def main():
    destination=TESTS/'wp-engineering-home-report.json'
    report={'generatedAtUTC':datetime.now(timezone.utc).isoformat(),'release_scope':'engineering_installable_media_incomplete','scope':'Actual authenticated draft Home on local noindex WordPress. This incomplete checkpoint does not publish Home or claim the 154-look target. Preview capability tokens and owner authentication are excluded.','checks':{},'geometry':{},'motion':{},'film':{},'screenshots':{},'passed':False}
    def save():destination.write_text(json.dumps(report,indent=2)+'\n')
    try:
        data=inspect();home=data['home'];before=data['preservation'];report['homeState']=home;save()
        assert home['status']=='draft' and not home['gate']['complete'] and home['sectionCount']==22
        expected=len(home['uniquePhotoIDs']);assert expected>50
        # This owner preview has no capability nonce in its URL. No private URL is recorded.
        preview=SITE+'/?page_id='+str(home['id'])+'&preview=true'
        screenshots=TESTS/'screenshots';screenshots.mkdir(exist_ok=True)
        errors=[];failures=[]
        with sync_playwright() as playwright:
            browser=playwright.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
            auth,page=authenticate(browser);auth.close()
            for name,width,height in [('desktop',1440,1100),('phone',390,844)]:
                context=browser.new_context(storage_state=str(AUTH),viewport={'width':width,'height':height},reduced_motion='reduce')
                page=context.new_page();page.on('pageerror',lambda error:errors.append(str(error)))
                page.on('response',lambda response:failures.append({'HTTP':response.status,'path':response.url.split('?')[0]}) if response.status>=400 else None)
                response=page.goto(preview,wait_until='networkidle');assert response.status==200
                assert page.locator('main .bixie-section').count()==22
                assert page.locator('main .bixie-moving-shelf').count()==9
                photos=browser_utilities.painted_images(page,'main .bixie-home img',context,expected,sample_edges=False)
                assert {int(photo['attachmentID']) for photo in photos}==set(home['uniquePhotoIDs'])
                for shelf in page.locator('main .bixie-moving-shelf').all():
                    # First and last original of every shelf exercise both ends of its horizontal flow.
                    for element in [shelf.locator('img').first,shelf.locator('img').last]:
                        element.scroll_into_view_if_needed();source=context.request.get(element.evaluate('e=>e.currentSrc||e.src'))
                        assert source.status==200
                        edge=utilities.edge_comparison(element.screenshot(),source.body());source.dispose()
                        assert edge['fullSourceEdgesPainted'],(name,edge)
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
                poster=data['attachments']['home-motion-poster'];assert page.locator(utilities.VIDEO).get_attribute('poster')==poster['displayURL']
                report['geometry'][name]={'actualImageElements':expected,'uniqueImageAttachmentIDs':expected,'distinctFilmPoster':len(set(home['posterIDs'])),'allNaturalPhotoGeometry':photos,'nineShelfFirstAndLastSourceEdgesPainted':True,'horizontalOverflow':False};save()
                page.locator('.bixie-photo-row').evaluate_all('es=>es.forEach(e=>e.scrollLeft=0)');page.evaluate('scrollTo(0,0)');page.wait_for_timeout(150)
                for shape,full in [('opening',False),('full-page',True)]:
                    path=screenshots/('engineering-home-'+name+'-'+shape+'.png')
                    page.screenshot(path=str(path),full_page=full,style='#wpadminbar{display:none!important}')
                    report['screenshots'][name+'-'+shape]=str(path.relative_to(TESTS));save()
                collection=next(record for record in data['collections'].values() if record['gate']['complete'])
                page.goto(collection['url'],wait_until='networkidle');assert page.locator('.bixie-results img').count()==21
                browser_utilities.painted_images(page,'.bixie-results img',context,21,sample_edges=False)
                page.evaluate('scrollTo(0,0)');path=screenshots/('engineering-real-21-view-collection-'+name+'.png')
                page.screenshot(path=str(path),full_page=True,style='#wpadminbar{display:none!important}');report['screenshots']['collection-'+name]=str(path.relative_to(TESTS));save();context.close()
            report['checks']['draftHomeActualImagesAndNineShelvesWholeSourceAtDesktopPhone']=True
            for name,width,height in [('desktop',1440,1100),('phone',390,844)]:
                context=browser.new_context(storage_state=str(AUTH),viewport={'width':width,'height':height})
                page=context.new_page();page.goto(preview,wait_until='networkidle')
                rails=page.locator('main .bixie-photo-row');assert rails.count()==10
                observations=[]
                for index,rail in enumerate(rails.all()):
                    rail.scroll_into_view_if_needed();page.wait_for_timeout(250)
                    rail_id=rail.get_attribute('id');assert rail_id
                    control=page.locator('[data-bixie-motion-toggle][aria-controls="'+rail_id+'"]');assert control.count()==1
                    travel=rail.evaluate('e=>e.scrollWidth-e.clientWidth');assert travel>1,(name,index,travel)
                    start=rail.evaluate('e=>e.scrollLeft');page.wait_for_timeout(650);advanced=rail.evaluate('e=>e.scrollLeft');assert abs(advanced-start)>2,(name,index,start,advanced)
                    control.click();rail.scroll_into_view_if_needed();page.wait_for_timeout(200);paused=rail.evaluate('e=>e.scrollLeft');page.wait_for_timeout(400)
                    assert abs(rail.evaluate('e=>e.scrollLeft')-paused)<1 and control.get_attribute('aria-pressed')=='true'
                    other_controls=page.locator('[data-bixie-motion-toggle]').evaluate_all('(es,id)=>es.filter(e=>e.getAttribute("aria-controls")!==id).map(e=>e.getAttribute("aria-pressed"))',rail_id)
                    assert all(value=='false' for value in other_controls),other_controls
                    control.click();rail.scroll_into_view_if_needed();page.wait_for_timeout(250);resumed=rail.evaluate('e=>e.scrollLeft');page.wait_for_timeout(450);assert abs(rail.evaluate('e=>e.scrollLeft')-resumed)>2
                    rail.evaluate('e=>window.scrollTo(0,e.getBoundingClientRect().top<1000?document.body.scrollHeight:0)');page.wait_for_timeout(250)
                    offscreen=rail.evaluate('e=>e.scrollLeft');page.wait_for_timeout(400);assert abs(rail.evaluate('e=>e.scrollLeft')-offscreen)<1
                    observations.append({'railID':rail_id,'actualPhotos':rail.locator('img').count(),'travel':travel,'start':start,'advanced':advanced,'scopedPause':True,'otherRailsUnpaused':True,'resumed':True,'offscreenStopped':True});report['motion'][name]=observations;save()
                video=page.locator(utilities.VIDEO);video.scroll_into_view_if_needed();utilities.wait_playing(page)
                film=utilities.sample(page);assert film['timeAdvanced'] and film['after']['muted'] and film['after']['playsInline'] and film['after']['controls'] and film['after']['decodedFrames']>0
                assert [film['after']['videoWidth'],film['after']['videoHeight']]==[1122,1402]
                geometry=video.evaluate('v=>{const r=v.getBoundingClientRect(),s=getComputedStyle(v),scale=Math.min(r.width/v.videoWidth,r.height/v.videoHeight);return {element:[r.width,r.height],native:[v.videoWidth,v.videoHeight],paintedFullFrame:[v.videoWidth*scale,v.videoHeight*scale],objectFit:s.objectFit,transform:s.transform};}')
                assert geometry['objectFit']=='contain' and geometry['transform']=='none'
                video.focus();page.keyboard.press('Space');utilities.wait_paused(page)
                frame=video.evaluate("v=>{const c=document.createElement('canvas');c.width=v.videoWidth;c.height=v.videoHeight;c.getContext('2d').drawImage(v,0,0);return c.toDataURL('image/png').split(',')[1];}")
                edge=utilities.edge_comparison(video.screenshot(style='video::-webkit-media-controls{display:none!important}'),base64.b64decode(frame),geometry['paintedFullFrame']);assert edge['fullSourceEdgesPainted']
                page.evaluate('scrollTo(0,0)');page.wait_for_timeout(200);video.scroll_into_view_if_needed();page.wait_for_timeout(250);assert utilities.sample(page)['timeStopped']
                video.focus();page.keyboard.press('Space');utilities.wait_playing(page);page.evaluate('scrollTo(0,0)');utilities.wait_paused(page)
                report['film'][name]={'visibleMutedInlineAutoplay':film,'geometry':geometry,'actualDecodedSourceEdges':edge,'nativeSpacePauseAndVisibilityReturnPreserved':True,'offscreenStopped':True};save();context.close()
            report['checks']['openingRailAndNineNativeShelvesMovePauseIndependentlyAndStopOffscreen']=True
            report['checks']['actualFilmAutoplayMutedInlineFullDecodedFrameNativeKeyboardPauseOffscreen']=True
            context=browser.new_context(storage_state=str(AUTH),viewport={'width':390,'height':844},reduced_motion='reduce')
            page=context.new_page();page.goto(preview,wait_until='networkidle');reduced=[]
            for rail in page.locator('main .bixie-photo-row').all():
                rail.scroll_into_view_if_needed();page.wait_for_timeout(200);initial=rail.evaluate('e=>e.scrollLeft');page.wait_for_timeout(400);assert abs(rail.evaluate('e=>e.scrollLeft')-initial)<1
                control=page.locator('[data-bixie-motion-toggle][aria-controls="'+rail.get_attribute('id')+'"]');assert control.get_attribute('data-bixie-reduced')=='true'
                control.click();advanced=rail.evaluate('e=>e.scrollLeft');assert abs(advanced-initial)>2
                reduced.append({'railID':rail.get_attribute('id'),'automaticStopped':True,'explicitNextAdvanced':True})
            video=page.locator(utilities.VIDEO);video.scroll_into_view_if_needed();page.wait_for_timeout(300);assert utilities.state(page)['paused']
            page.locator('[data-bixie-video-toggle]').click();utilities.wait_playing(page);assert utilities.sample(page)['timeAdvanced']
            report['reducedMotion']=reduced;report['checks']['reducedMotionAllTenRailsAndFilmStopAutomaticAndExplicitControlsWork']=True;save()
            page.emulate_media(media='print');printing=page.locator('.bixie-moving-shelf').evaluate_all('es=>es.map(e=>{const s=getComputedStyle(e);return {flow:s.gridAutoFlow,columns:s.gridTemplateColumns,overflow:s.overflow,photos:e.querySelectorAll("img").length};})')
            assert len(printing)==9 and all(row['flow']=='row' and row['overflow']=='visible' and len(row['columns'].split())==3 for row in printing),printing
            report['printNineShelves']=printing;report['checks']['printReturnsNineFullVisibleThreeColumnNativeGalleries']=True;save();context.close()
            admin,editor=authenticate(browser);editor.goto(data['pages']['home']['editURL'],wait_until='networkidle')
            editor.wait_for_function('()=>window.wp?.data?.select("core/block-editor")?.getBlocks()?.length>0',timeout=60000)
            canvas=next((frame for frame in editor.frames if frame.name=='editor-canvas'),editor.main_frame)
            canvas.wait_for_selector('.editor-styles-wrapper .bixie-moving-shelf',timeout=60000)
            gallery_editor=canvas.locator('.editor-styles-wrapper .bixie-moving-shelf').evaluate_all('es=>es.map(e=>{const s=getComputedStyle(e),r=e.getBoundingClientRect();return {display:s.display,overflow:s.overflow,width:r.width,images:e.querySelectorAll("img").length};})')
            assert len(gallery_editor)==9 and all(row['display']=='block' and row['overflow']=='visible' and row['width']>0 and row['images']>1 for row in gallery_editor),gallery_editor
            report['nativeOwnerEditorNineGalleries']=gallery_editor;report['checks']['nativeOwnerEditorNineGalleriesRemainStaticVisibleAndEditable']=True;save();admin.close();browser.close()
        after=inspect();assert before==after['preservation'] and after['home']['status']=='draft' and not after['home']['gate']['complete']
        report['checks']['readOnlyPreviewPreservesOwnerContentAndIncompleteHomeDraftGate']=True
        report['pageErrors']=errors;report['failedResponses']=failures;assert not errors and not failures
        report['passed']=True
    except Exception as error:
        report['failure']=str(error);report['traceback']=traceback.format_exc();raise
    finally:
        save();print(json.dumps({'passed':report['passed'],'report':str(destination),'checks':report['checks'],'failure':report.get('failure')},indent=2),flush=True)

if __name__=='__main__':main()
