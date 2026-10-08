#!/usr/bin/env python3
"""Public completed actual Home: 77 image elements + 1 distinct native film poster."""
import base64
import hashlib
import importlib.util
import json
import traceback
from datetime import datetime, timezone

from playwright.sync_api import sync_playwright
from wp_final_common import inspect, SITE, TESTS

spec = importlib.util.spec_from_file_location('production_film_utilities', TESTS / 'wp-production-home-film-qa.py')
utilities = importlib.util.module_from_spec(spec); spec.loader.exec_module(utilities)
spec = importlib.util.spec_from_file_location('actual_browser_utilities', TESTS / 'wp-final-browser-qa.py')
browser_utilities = importlib.util.module_from_spec(spec); spec.loader.exec_module(browser_utilities)


def main():
    destination = TESTS / 'wp-final-home-report.json'
    report = {'generatedAtUTC':datetime.now(timezone.utc).isoformat(),'scope':'Completed public actual-source Home on the separate local noindex WordPress site. The silent photographic sequence is not live-action salon footage. Every original image remains whole; edge screenshot comparisons use the actual selected source.','checks':{},'photosAtFourWidths':{},'film':{},'passed':False}
    def save(): destination.write_text(json.dumps(report,indent=2)+'\n')
    try:
        data = inspect(); home = data['home']; report['homeState'] = home; save()
        assert home['status'] == 'publish' and home['gate']['complete']
        assert home['sectionCount'] == 22 and len(home['uniquePhotoIDs']) == 77 and len(home['visiblePhotoIDs']) == 78
        film = data['attachments']['home-motion-film']; poster = data['attachments']['home-motion-poster']
        assert film['qualified'] and set(film['filmSourceKeys']) == {'home-angle-front','home-angle-side','home-angle-back'}
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
            errors = []; failures = []
            for name,width,height in [('desktop',1440,1100),('tablet',768,1024),('phone',390,844),('small-phone',320,720)]:
                context = browser.new_context(viewport={'width':width,'height':height},reduced_motion='reduce')
                page = context.new_page(); page.on('pageerror',lambda error:errors.append(str(error)))
                page.on('response',lambda response:failures.append({'status':response.status,'url':response.url}) if response.status>=400 else None)
                response = page.goto(SITE+'/',wait_until='networkidle'); assert response.status == 200
                assert page.locator('main .bixie-section').count() == 22
                photos = browser_utilities.painted_images(page,'main .bixie-home img',context,77,sample_edges=False)
                ids = [int(photo['attachmentID']) for photo in photos]; assert len(set(ids)) == 77 and set(ids) == set(home['uniquePhotoIDs'])
                for index, element in enumerate(page.locator('main .bixie-home img').all()):
                    element.scroll_into_view_if_needed()
                    source = context.request.get(photos[index]['source']); assert source.status == 200
                    photos[index]['actualEdgePixels'] = utilities.edge_comparison(element.screenshot(),source.body())
                    assert photos[index]['actualEdgePixels']['fullSourceEdgesPainted'], (name,index,photos[index])
                video = page.locator(utilities.VIDEO); assert video.get_attribute('poster') == poster['displayURL']
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
                report['photosAtFourWidths'][name] = {'actualImageElements':77,'uniqueImageAttachmentIDs':77,'nativeFilmPosterIs78thUniquePhoto':True,'images':photos,'horizontalOverflow':False}; save()
                context.close()
            report['checks']['all77ActualImagesPaintFullSourceEdgesAtFourWidths'] = True
            report['checks']['nativeFilmPosterCompletes78DistinctVisiblePhotographicSources'] = True
            for name,width,height in [('desktop',1440,1100),('phone',390,844)]:
                context = browser.new_context(viewport={'width':width,'height':height})
                page = context.new_page(); page.on('pageerror',lambda error:errors.append(str(error)))
                page.goto(SITE+'/',wait_until='networkidle'); video = page.locator(utilities.VIDEO)
                video.scroll_into_view_if_needed(); utilities.wait_playing(page)
                observation = {'visibleAutoplayWithoutClick':utilities.sample(page)}; report['film'][name] = observation; save()
                actual = observation['visibleAutoplayWithoutClick']; assert actual['timeAdvanced'] and actual['after']['decodedFrames'] > 0 and actual['after']['muted'] and actual['after']['playsInline'] and actual['after']['controls']
                assert [actual['after']['videoWidth'],actual['after']['videoHeight']] == [1122,1402]
                geometry = video.evaluate('''v=>{const r=v.getBoundingClientRect(),s=getComputedStyle(v),scale=Math.min(r.width/v.videoWidth,r.height/v.videoHeight);return {element:[r.width,r.height],native:[v.videoWidth,v.videoHeight],paintedFullFrame:[v.videoWidth*scale,v.videoHeight*scale],objectFit:s.objectFit,transform:s.transform,visibility:s.visibility};}'''); observation['geometry'] = geometry
                assert geometry['objectFit'] == 'contain' and geometry['transform'] == 'none' and geometry['visibility'] == 'visible'
                video.focus(); page.keyboard.press('Space'); utilities.wait_paused(page)
                frame = video.evaluate('''v=>{const c=document.createElement('canvas');c.width=v.videoWidth;c.height=v.videoHeight;c.getContext('2d').drawImage(v,0,0);return c.toDataURL('image/png').split(',')[1];}''')
                observation['decodedFrameEdgePixels'] = utilities.edge_comparison(video.screenshot(style='video::-webkit-media-controls{display:none!important}'),base64.b64decode(frame),geometry['paintedFullFrame'])
                assert observation['decodedFrameEdgePixels']['fullSourceEdgesPainted']; observation['nativeControlsSuppressedOnlyDuringPixelScreenshot'] = True
                page.evaluate('scrollTo(0,0)'); page.wait_for_timeout(250); video.scroll_into_view_if_needed(); page.wait_for_timeout(250)
                observation['manualNativeSpacePauseRetainedAfterVisibilityReturn'] = utilities.sample(page); assert observation['manualNativeSpacePauseRetainedAfterVisibilityReturn']['timeStopped']
                video.focus(); page.keyboard.press('Space'); utilities.wait_playing(page)
                page.evaluate('scrollTo(0,0)'); utilities.wait_paused(page); observation['offscreenAutoplayPaused'] = utilities.state(page)
                video.scroll_into_view_if_needed(); utilities.wait_playing(page); observation['visibleAutoplayResumed'] = utilities.sample(page); assert observation['visibleAutoplayResumed']['timeAdvanced']
                rail = page.locator('#photo-flow'); rail.scroll_into_view_if_needed(); page.wait_for_timeout(300)
                initial = rail.evaluate('e=>e.scrollLeft'); page.wait_for_timeout(600); advanced = rail.evaluate('e=>e.scrollLeft'); assert abs(advanced-initial) > 2, (name,initial,advanced)
                control = page.locator('[data-bixie-motion-toggle]').first; control.click(); page.wait_for_timeout(150); stopped = rail.evaluate('e=>e.scrollLeft'); page.wait_for_timeout(400); assert abs(rail.evaluate('e=>e.scrollLeft')-stopped) < 1
                observation['automaticPhotoFlowAndOwnerPause'] = {'before':initial,'after':advanced,'pausedPosition':stopped,'verified':True}; save(); context.close()
            context = browser.new_context(viewport={'width':390,'height':844},reduced_motion='reduce')
            page = context.new_page(); page.goto(SITE+'/',wait_until='networkidle'); video = page.locator(utilities.VIDEO); video.scroll_into_view_if_needed(); page.wait_for_timeout(400)
            assert utilities.state(page)['paused']; page.locator('[data-bixie-video-toggle]').click(); utilities.wait_playing(page); assert utilities.sample(page)['timeAdvanced']
            rail = page.locator('#photo-flow'); rail.scroll_into_view_if_needed(); initial = rail.evaluate('e=>e.scrollLeft'); page.wait_for_timeout(400); assert abs(rail.evaluate('e=>e.scrollLeft')-initial) < 1
            page.locator('[data-bixie-motion-toggle]').first.click(); page.wait_for_timeout(150); assert rail.evaluate('e=>e.scrollLeft') != initial
            report['checks']['reducedMotionStopsAutomaticFilmAndPhotoFlowButExplicitControlsWork'] = True
            report['checks']['actualFilmDecodedFramesFullFrameAutoplayMutedInlineAndNativeKeyboardControls'] = True
            report['checks']['automaticPhotoFlowAndOwnerPause'] = True
            report['pageErrors'] = errors; report['failedResponses'] = failures; assert not errors and not failures
            context.close(); browser.close()
        report['passed'] = True
    except Exception as error:
        report['failure'] = str(error); report['traceback'] = traceback.format_exc(); raise
    finally:
        save(); print(json.dumps({'passed':report['passed'],'report':str(destination),'checks':report['checks'],'failure':report.get('failure')},indent=2),flush=True)


if __name__ == '__main__': main()
