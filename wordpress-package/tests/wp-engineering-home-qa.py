#!/usr/bin/env python3
"""Actual authenticated incomplete Home preview; never publishes it."""
import argparse
import base64
import zipfile
import importlib.util
import hashlib
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

DARK_TEXT_SCRIPT='''es=>{
 const values=c=>(c.match(/[0-9.]+/g)||[]).map(Number);
 const paintedBackground=e=>{const layers=[];for(let n=e;n;n=n.parentElement){const c=values(getComputedStyle(n).backgroundColor);layers.push([c[0]||0,c[1]||0,c[2]||0,c.length>3?c[3]:1]);}let rgb=[255,255,255];for(const c of layers.reverse())rgb=rgb.map((x,i)=>c[i]*c[3]+x*(1-c[3]));return rgb;};
 const luminance=rgb=>rgb.slice(0,3).map(x=>{x/=255;return x<=.04045?x/12.92:((x+.055)/1.055)**2.4;}).reduce((s,x,i)=>s+x*[.2126,.7152,.0722][i],0);
 return es.map(section=>{const background=values(getComputedStyle(section).backgroundColor);return {palette:[...section.classList].find(c=>['is-moss','is-ink','is-copper'].includes(c)),background,text:[...section.querySelectorAll('p,figcaption')].map(e=>{const style=getComputedStyle(e),color=values(style.color),background=paintedBackground(e);let opacity=color.length>3?color[3]:1;for(let n=e;n&&n!==section;n=n.parentElement)opacity*=Number(getComputedStyle(n).opacity);const painted=color.slice(0,3).map((x,i)=>x*opacity+background[i]*(1-opacity));const a=luminance(painted),b=luminance(background);return {element:e.tagName,className:e.className,color:style.color,opacity,ratio:(Math.max(a,b)+.05)/(Math.min(a,b)+.05)};})};});
 }'''

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--finish-only',action='store_true');args=parser.parse_args()
    destination=TESTS/'wp-engineering-home-report.json'
    report={'generatedAtUTC':datetime.now(timezone.utc).isoformat(),'release_scope':'engineering_installable_media_incomplete','scope':'Actual authenticated draft Home on local noindex WordPress. This incomplete checkpoint does not publish Home or claim the 154-look target. Preview capability tokens and owner authentication are excluded.','checks':{},'geometry':{},'motion':{},'film':{},'screenshots':{},'passed':False}
    def save():destination.write_text(json.dumps(report,indent=2)+'\n')
    try:
        data=inspect();home=data['home'];before=data['preservation'];
        if args.finish_only:
            previous=json.loads(destination.read_text());assert previous['homeState']['contentSHA256']==home['contentSHA256']
            for check in ['draftHomeActualImagesAndAllNineNativeGalleriesWholeSourceAtDesktopPhone','openingRailAndSevenMultiplePhotoNativeShelvesMovePauseIndependentlyOneGenuineSinglePhotoShelfAndThreeAnglePlateStayStatic','actualFilmAutoplayMutedInlineFullDecodedFrameNativeKeyboardPauseOffscreen','reducedMotionEightOverflowingRailsAndFilmStopAutomaticAndExplicitControlsWorkSinglePhotoShelfStatic']:assert previous['checks'][check] is True,check
            release=Path('/workspace/check.txt/wordpress-release/bixie-editorial.zip');core=json.loads((TESTS/'wp-engineering-core-zip-report.json').read_text());assert hashlib.sha256(release.read_bytes()).hexdigest()==core['archives']['theme']['sha256']
            with zipfile.ZipFile(release) as archive:
                for member in archive.namelist():
                    if not member.endswith('/'):
                        installed=Path('/workspace/wp-final-test/wordpress/wp-content/themes')/member
                        assert installed.is_file() and hashlib.sha256(installed.read_bytes()).digest()==hashlib.sha256(archive.read(member)).digest(),member
            report=previous;report['passed']=False;report.pop('failure',None);report.pop('traceback',None);report['continuedAffectedVisualContrastPrintEditorOnly']=True;report['sameFrozenRuntimeThemeArchiveSHA256']=core['archives']['theme']['sha256']
        report['homeState']=home;report['actualStructure']={'nativeGalleries':9,'photoShelfGalleries':8,'multiplePhotoMovingShelfGalleries':7,'openingMovingRail':1,'overflowingMovingRails':8,'genuinelySinglePhotoShelf':1,'separateStaticFrontSideBackPlate':1};save()
        assert home['status']=='draft' and not home['gate']['complete'] and home['sectionCount']==22
        expected=len(home['uniquePhotoIDs']);assert expected>50
        # This owner preview has no capability nonce in its URL. No private URL is recorded.
        preview=SITE+'/?page_id='+str(home['id'])+'&preview=true'
        screenshots=TESTS/'screenshots';screenshots.mkdir(exist_ok=True)
        errors=[];failures=[]
        with sync_playwright() as playwright:
            browser=playwright.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
            auth,page=authenticate(browser);auth.close()
            anonymous=browser.new_context();public_home=anonymous.request.get(home['url'])
            assert public_home.status==404,public_home.status
            report['anonymousDraftHomeHTTP']=public_home.status;report['checks']['incompleteHomeIsUnavailableToAnonymousVisitors']=True
            public_home.dispose();anonymous.close();save()
            for name,width,height in [('desktop',1440,1100),('phone',390,844)]:
                context=browser.new_context(storage_state=str(AUTH),viewport={'width':width,'height':height},reduced_motion='reduce')
                page=context.new_page();page.on('pageerror',lambda error:errors.append(str(error)))
                page.on('response',lambda response:failures.append({'HTTP':response.status,'path':response.url.split('?')[0]}) if response.status>=400 else None)
                response=page.goto(preview,wait_until='networkidle');assert response.status==200
                assert page.locator('main h1').count()==1 and page.locator('main .wp-block-post-title').count()==0
                report['checks']['nativeHomeSlugDraftPreviewUsesSingleHeroHeadingWithoutDuplicatePostTitle']=True;save()
                assert page.locator('main .bixie-section').count()==22
                assert page.locator('main .bixie-moving-shelf').count()==8 and page.locator('main .bixie-home .wp-block-gallery').count()==9
                if args.finish_only:
                    photos=report['geometry'][name]['allNaturalPhotoGeometry'];assert len(photos)==expected
                    page.locator('main .bixie-home img').evaluate_all('async es=>{es.forEach(e=>e.loading="eager");await Promise.all(es.map(e=>e.decode()));}')
                else:
                    photos=browser_utilities.painted_images(page,'main .bixie-home img',context,expected,sample_edges=False,attachment_records=data['attachments'])
                    report['geometry'][name]={'actualImageElements':expected,'allNaturalPhotoGeometry':photos};save()
                    assert {int(photo['attachmentID']) for photo in photos}==set(home['uniquePhotoIDs'])
                    for shelf in page.locator('main .bixie-home .wp-block-gallery').all():
                        # First and last original of every shelf exercise both ends of its horizontal flow.
                        for element in [shelf.locator('img').first,shelf.locator('img').last]:
                            element.scroll_into_view_if_needed();selected=element.evaluate('e=>e.currentSrc||e.src')
                            original=next(record for record in data['attachments'].values() if selected in record['registeredImageVariantURLs'])
                            source=context.request.get(original['nativeURL'])
                            assert source.status==200
                            assert hashlib.sha256(source.body()).hexdigest()==original['sourceSHA256']
                            edge=utilities.edge_comparison(element.screenshot(),source.body());source.dispose()
                            assert edge['fullSourceEdgesPainted'],(name,edge)
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
                contrast=page.locator('main .bixie-section:is(.is-moss,.is-ink,.is-copper)').evaluate_all(DARK_TEXT_SCRIPT)
                report.setdefault('actualDarkSectionTextContrast',{})[name]=contrast;save()
                assert {row['palette'] for row in contrast}=={'is-moss','is-ink'}
                assert sum(len(row['text']) for row in contrast)>0 and all(all(text['ratio']>=4.5 for text in row['text']) for row in contrast),contrast
                section_classes=page.locator('main .bixie-section').evaluate_all('es=>es.map(e=>e.className)');palette_section=page.locator('main .bixie-section.is-moss').first.element_handle();original_classes=palette_section.get_attribute('class')
                try:
                    palette_section.evaluate('e=>{e.classList.remove("is-moss");e.classList.add("is-copper");}')
                    copper=page.locator('main .bixie-section.is-copper').evaluate_all(DARK_TEXT_SCRIPT)
                    assert len(copper)==1 and all(text['ratio']>=4.5 for text in copper[0]['text']),copper
                    report.setdefault('browserOnlyOwnerCopperPaletteVariant',{})[name]={'scope':'Only the class of an existing real section is temporarily changed in this authenticated browser to exercise the native owner palette option; original DOM classes are restored before screenshots. No content, source or database mutation. Actual Home uses moss and ink.','contrast':copper}
                finally:
                    palette_section.evaluate('(e,value)=>e.className=value',original_classes)
                assert page.locator('main .bixie-section').evaluate_all('es=>es.map(e=>e.className)')==section_classes
                report['checks']['browserOnlyPaletteVariantRestoresExactSameElementAndEveryNativeSectionClass']=True
                report['checks']['actualMossInkTextAndBrowserOnlyOwnerCopperPaletteVariantContrastAtLeast4point5']=True;save()
                poster=data['attachments']['home-motion-poster'];assert page.locator(utilities.VIDEO).get_attribute('poster')==poster['displayURL']
                report['geometry'][name]={'actualImageElements':expected,'uniqueImageAttachmentIDs':expected,'distinctFilmPoster':len(set(home['posterIDs'])),'allNaturalPhotoGeometry':photos,'allNineNativeGalleriesFirstAndLastSourceEdgesPainted':True,'horizontalOverflow':False};save()
                page.locator('.bixie-photo-row').evaluate_all('es=>es.forEach(e=>e.scrollLeft=0)');page.evaluate('scrollTo(0,0)');page.wait_for_timeout(150)
                for shape,full in [('opening',False),('full-page',True)]:
                    path=screenshots/('engineering-home-'+name+'-'+shape+'.png')
                    page.screenshot(path=str(path),full_page=full,style='#wpadminbar{display:none!important}')
                    report['screenshots'][name+'-'+shape]=str(path.relative_to(TESTS));save()
                page.locator('.bixie-shelf-flow').first.scroll_into_view_if_needed()
                path=screenshots/('engineering-home-'+name+'-shelf-controls.png')
                page.screenshot(path=str(path),style='#wpadminbar{display:none!important}')
                report['screenshots'][name+'-shelf-controls']=str(path.relative_to(TESTS));save()
                collection=next(record for record in data['collections'].values() if record['gate']['complete'])
                page.goto(collection['url'],wait_until='networkidle');assert page.locator('.bixie-results img').count()==21
                browser_utilities.painted_images(page,'.bixie-results img',context,21,sample_edges=False)
                page.evaluate('scrollTo(0,0)');path=screenshots/('engineering-real-21-view-collection-'+name+'.png')
                page.screenshot(path=str(path),full_page=True,style='#wpadminbar{display:none!important}');report['screenshots']['collection-'+name]=str(path.relative_to(TESTS));save()
                page.locator('.bixie-results .bixie-look-card').first.scroll_into_view_if_needed()
                path=screenshots/('engineering-real-three-view-card-'+name+'.png')
                page.screenshot(path=str(path),style='#wpadminbar{display:none!important}')
                report['screenshots']['three-view-card-'+name]=str(path.relative_to(TESTS));save();context.close()
            report['checks']['draftHomeActualImagesAndAllNineNativeGalleriesWholeSourceAtDesktopPhone']=True
            if not args.finish_only:
                for name,width,height in [('desktop',1440,1100),('phone',390,844)]:
                    context=browser.new_context(storage_state=str(AUTH),viewport={'width':width,'height':height})
                    page=context.new_page();page.goto(preview,wait_until='networkidle')
                    rails=page.locator('main .bixie-photo-row');assert rails.count()==9
                    observations=[]
                    for index,rail in enumerate(rails.all()):
                        rail.scroll_into_view_if_needed();page.wait_for_timeout(250)
                        travel=rail.evaluate('e=>e.scrollWidth-e.clientWidth');photo_count=rail.locator('img').count()
                        if photo_count==1:
                            static=rail.evaluate('e=>{const g=e.closest(".bixie-shelf-flow");return {wrapperAnchor:g?.id,controls:g?.querySelectorAll("[data-bixie-motion-toggle]").length||0};}')
                            assert travel<=1 and static['controls']==0,(name,index,travel,static)
                            observations.append({**static,'actualPhotos':1,'travel':travel,'genuinelyPartialSinglePhotoShelfStaticWithoutEmptyControl':True});report['motion'][name]=observations;save();continue
                        rail_id=rail.get_attribute('id');assert rail_id
                        control=page.locator('[data-bixie-motion-toggle][aria-controls="'+rail_id+'"]')
                        assert travel>1 and control.count()==1,(name,index,travel,control.count())
                        start=rail.evaluate('e=>e.scrollLeft');page.wait_for_timeout(650);advanced=rail.evaluate('e=>e.scrollLeft');assert abs(advanced-start)>2,(name,index,start,advanced)
                        control.click();rail.scroll_into_view_if_needed();page.wait_for_timeout(200);paused=rail.evaluate('e=>e.scrollLeft');page.wait_for_timeout(400)
                        assert abs(rail.evaluate('e=>e.scrollLeft')-paused)<1 and control.get_attribute('aria-pressed')=='true'
                        other_controls=page.locator('[data-bixie-motion-toggle]').evaluate_all('(es,id)=>es.filter(e=>e.getAttribute("aria-controls")!==id).map(e=>e.getAttribute("aria-pressed"))',rail_id)
                        assert all(value=='false' for value in other_controls),other_controls
                        control.click();rail.scroll_into_view_if_needed();page.wait_for_timeout(250);resumed=rail.evaluate('e=>e.scrollLeft');page.wait_for_timeout(650)
                        resumed_after=rail.evaluate('e=>e.scrollLeft')
                        report['motionResumeObservations']=report.get('motionResumeObservations',[])+[{'viewport':name,'railID':rail_id,'before':resumed,'after':resumed_after,'ariaPressed':control.get_attribute('aria-pressed'),'geometry':rail.evaluate('e=>{const r=e.getBoundingClientRect();return {top:r.top,bottom:r.bottom,height:r.height,viewport:innerHeight};}') }];save()
                        assert abs(resumed_after-resumed)>2,(name,rail_id,resumed,resumed_after,report['motionResumeObservations'][-1])
                        rail.evaluate('e=>window.scrollTo(0,e.getBoundingClientRect().top<1000?document.body.scrollHeight:0)');page.wait_for_timeout(250)
                        offscreen=rail.evaluate('e=>e.scrollLeft');page.wait_for_timeout(400);assert abs(rail.evaluate('e=>e.scrollLeft')-offscreen)<1
                        observations.append({'railID':rail_id,'actualPhotos':photo_count,'travel':travel,'start':start,'advanced':advanced,'scopedPause':True,'otherRailsUnpaused':True,'resumed':True,'offscreenStopped':True});report['motion'][name]=observations;save()
                    assert sum(row.get('scopedPause') is True for row in observations)==8 and sum(row.get('genuinelyPartialSinglePhotoShelfStaticWithoutEmptyControl') is True for row in observations)==1
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
                report['checks']['openingRailAndSevenMultiplePhotoNativeShelvesMovePauseIndependentlyOneGenuineSinglePhotoShelfAndThreeAnglePlateStayStatic']=True
                report['checks']['actualFilmAutoplayMutedInlineFullDecodedFrameNativeKeyboardPauseOffscreen']=True
                context=browser.new_context(storage_state=str(AUTH),viewport={'width':390,'height':844},reduced_motion='reduce')
                page=context.new_page();page.goto(preview,wait_until='networkidle');reduced=[]
                for rail in page.locator('main .bixie-photo-row').all():
                    rail.scroll_into_view_if_needed();page.wait_for_timeout(200);initial=rail.evaluate('e=>e.scrollLeft');page.wait_for_timeout(400);assert abs(rail.evaluate('e=>e.scrollLeft')-initial)<1
                    if rail.locator('img').count()==1:
                        static=rail.evaluate('e=>{const g=e.closest(".bixie-shelf-flow");return {wrapperAnchor:g?.id,controls:g?.querySelectorAll("[data-bixie-motion-toggle]").length||0};}')
                        assert static['controls']==0 and rail.evaluate('e=>e.scrollWidth-e.clientWidth')<=1
                        reduced.append({**static,'actualPhotos':1,'staticSinglePhotoWithoutEmptyControl':True});continue
                    control=page.locator('[data-bixie-motion-toggle][aria-controls="'+rail.get_attribute('id')+'"]')
                    assert control.count()==1 and control.get_attribute('data-bixie-reduced')=='true'
                    control.click();advanced=rail.evaluate('e=>e.scrollLeft');assert abs(advanced-initial)>2
                    reduced.append({'railID':rail.get_attribute('id'),'automaticStopped':True,'explicitNextAdvanced':True})
                video=page.locator(utilities.VIDEO);video.scroll_into_view_if_needed();page.wait_for_timeout(300);assert utilities.state(page)['paused']
                page.locator('[data-bixie-video-toggle]').click();utilities.wait_playing(page);assert utilities.sample(page)['timeAdvanced']
                assert len(reduced)==9 and sum(row.get('explicitNextAdvanced') is True for row in reduced)==8
                report['reducedMotion']=reduced;report['checks']['reducedMotionEightOverflowingRailsAndFilmStopAutomaticAndExplicitControlsWorkSinglePhotoShelfStatic']=True;save()
            else:
                context=browser.new_context(storage_state=str(AUTH),viewport={'width':390,'height':844},reduced_motion='reduce');page=context.new_page();page.goto(preview,wait_until='networkidle')
            page.emulate_media(media='print');printing=page.locator('.bixie-moving-shelf').evaluate_all('es=>es.map(e=>{const s=getComputedStyle(e);return {flow:s.gridAutoFlow,columns:s.gridTemplateColumns,overflow:s.overflow,photos:e.querySelectorAll("img").length};})')
            assert len(printing)==8 and all(row['flow']=='row' and row['overflow']=='visible' and len(row['columns'].split())==3 for row in printing),printing
            print_text=page.locator('main .bixie-section:is(.is-moss,.is-ink,.is-copper)').evaluate_all('''es=>{const values=c=>(c.match(/[0-9.]+/g)||[]).map(Number);const painted=e=>{const layers=[];for(let n=e;n;n=n.parentElement){const c=values(getComputedStyle(n).backgroundColor);layers.push([c[0]||0,c[1]||0,c[2]||0,c.length>3?c[3]:1]);}let rgb=[255,255,255];for(const c of layers.reverse())rgb=rgb.map((x,i)=>c[i]*c[3]+x*(1-c[3]));return rgb;};return es.map(e=>({background:getComputedStyle(e).backgroundColor,effectivePaintedBackground:painted(e),text:[...e.querySelectorAll('p,figcaption')].map(t=>getComputedStyle(t).color)}));}''')
            assert print_text and all(row['effectivePaintedBackground']==[255,255,255] and all(color=='rgb(0, 0, 0)' for color in row['text']) for row in print_text),print_text
            report['printDarkSectionText']=print_text;report['checks']['printDarkSectionsUseBlackCaptionAndIntroTextOnWhite']=True
            report['printEightShelves']=printing;report['checks']['printReturnsEightShelfGalleriesToFullVisibleThreeColumnGrids']=True;save();context.close()
            admin,editor=authenticate(browser);editor.goto(data['pages']['home']['editURL'],wait_until='networkidle')
            editor.wait_for_function('()=>window.wp?.data?.select("core/block-editor")?.getBlocks()?.length>0',timeout=60000)
            editor.wait_for_function('()=>!!document.querySelector(".bixie-moving-shelf")||[...document.querySelectorAll("iframe")].some(f=>f.contentDocument?.querySelector(".bixie-moving-shelf"))',timeout=60000)
            canvas=next(frame for frame in editor.frames if frame.locator('.bixie-moving-shelf').count()>0)
            report['actualNativeEditorFrames']=[{'name':frame.name,'movingShelfNodes':frame.locator('.bixie-moving-shelf').count(),'editorStyleWrapperNodes':frame.locator('.editor-styles-wrapper').count()} for frame in editor.frames];save()
            gallery_editor=canvas.locator('.editor-styles-wrapper .bixie-moving-shelf').evaluate_all('es=>es.map(e=>{const s=getComputedStyle(e),r=e.getBoundingClientRect();return {display:s.display,overflow:s.overflow,width:r.width,images:e.querySelectorAll("img").length};})')
            assert len(gallery_editor)==8 and all(row['display']=='block' and row['overflow']=='visible' and row['width']>0 and row['images']>=1 for row in gallery_editor) and sum(row['images']==1 for row in gallery_editor)==1,gallery_editor
            report['nativeOwnerEditorEightShelfGalleries']=gallery_editor;report['checks']['nativeOwnerEditorEightShelfGalleriesRemainStaticVisibleAndEditable']=True;save();admin.close();browser.close()
        after=inspect();assert before==after['preservation'] and after['home']['status']=='draft' and not after['home']['gate']['complete']
        report['checks']['readOnlyPreviewPreservesOwnerContentAndIncompleteHomeDraftGate']=True
        report['pageErrors']=errors;report['failedResponses']=failures;assert not errors and not failures
        report['passed']=True
    except Exception as error:
        report['failure']=str(error);report['traceback']=traceback.format_exc();raise
    finally:
        save();print(json.dumps({'passed':report['passed'],'report':str(destination),'checks':report['checks'],'failure':report.get('failure')},indent=2),flush=True)

if __name__=='__main__':main()
