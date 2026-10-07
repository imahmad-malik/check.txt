#!/usr/bin/env python3
"""Actual reviewed Home sources and photographic film in isolated WordPress.

Uploads immutable production parts through authenticated owner GUI, preserves
ordinary owner content, and cleans only its own draft page. Private login state
and the WordPress runtime stay outside the release package.
"""
import hashlib
import base64
import io
import json
import subprocess
import traceback
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageChops, ImageStat
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
TESTS = ROOT / 'tests'
RUNTIME = Path('/workspace/wp-test/wordpress')
PHP = '/workspace/wp-test/php'
SITE = 'http://127.0.0.1:8766'
PARTS = sorted(Path('/workspace/check.txt/wordpress-home-release').glob('bixie-production-home-*.zip'))
REPORT = TESTS / 'wp-production-home-film-report.json'
EXPECTATIONS = Path('/workspace/wp-test/artifacts/home-qa-expectations.json')
HELPER = TESTS / 'wp-production-home-film-state.php'
VIDEO = '#bixie-film video'
CONTROL = '.bixie-video-motion-toggle a'


def inspect(mode):
    result = subprocess.run([PHP, str(HELPER), str(RUNTIME / 'wp-load.php'), mode, str(EXPECTATIONS)], capture_output=True, text=True, check=True)
    return json.loads(result.stdout)


def state(page):
    return page.locator(VIDEO).evaluate('''v=>{
const q=v.getVideoPlaybackQuality?.();return {currentTime:v.currentTime,duration:v.duration,paused:v.paused,muted:v.muted,playsInline:v.playsInline,controls:v.controls,autoplay:v.autoplay,readyState:v.readyState,videoWidth:v.videoWidth,videoHeight:v.videoHeight,decodedFrames:q?.totalVideoFrames||v.webkitDecodedFrameCount||0,error:v.error?{code:v.error.code,message:v.error.message}:null,nativeVideoFocused:document.activeElement===v};}''')


def sample(page, milliseconds=450):
    before = state(page)
    page.wait_for_timeout(milliseconds)
    after = state(page)
    advance = (after['currentTime'] - before['currentTime']) % after['duration']
    return {'before': before, 'after': after, 'timelineAdvanceSeconds': advance,
            'timeAdvanced': advance > .15 and not after['paused'],
            'timeStopped': abs(after['currentTime'] - before['currentTime']) < .08 and after['paused']}


def wait_playing(page):
    page.wait_for_function("()=>{const v=document.querySelector('#bixie-film video');return v&&!v.paused&&v.readyState>=2}", timeout=10000)


def wait_paused(page):
    page.wait_for_function("()=>document.querySelector('#bixie-film video').paused", timeout=5000)


def paint_stats(payload):
    image = Image.open(io.BytesIO(payload)).convert('RGB')
    stat = ImageStat.Stat(image)
    return {'pixels': [image.width, image.height], 'channelVariance': stat.var,
            'nonFlatPixels': max(stat.var) > 100}


def edge_comparison(screenshot_payload, original_payload, full_frame_box=None):
    """Compare actual screenshot edge bands with the selected decoded source."""
    painted = Image.open(io.BytesIO(screenshot_payload)).convert('RGB')
    if full_frame_box:
        width, height = full_frame_box
        left = (painted.width - width) / 2
        top = (painted.height - height) / 2
        painted = painted.crop((round(left), round(top), round(left + width), round(top + height)))
    original = Image.open(io.BytesIO(original_payload)).convert('RGB').resize(painted.size, Image.Resampling.BILINEAR)
    result = {}
    for label, y0, y1 in [('top', .015, .065), ('bottom', .935, .985)]:
        box = (round(painted.width * .10), round(painted.height * y0), round(painted.width * .90), round(painted.height * y1))
        difference = ImageChops.difference(painted.crop(box), original.crop(box))
        result[label + 'MeanAbsoluteRGBDifference'] = ImageStat.Stat(difference).mean
    result['fullSourceEdgesPainted'] = all(max(value) < 25 for value in result.values())
    return result


def ordinary_poster_check(browser, errors):
    ordinary = inspect('create-ordinary-preview')
    assert ordinary['status'] == 'draft'
    context = browser.new_context(storage_state='/workspace/wp-test/qa-auth-state.json', viewport={'width': 1440, 'height': 1100})
    page = context.new_page()
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.goto(ordinary['previewURL'], wait_until='networkidle')
    video = page.locator('main .wp-block-video video')
    # Owner inline dimensions must remain usable; leave the production fit rule.
    video.evaluate("v=>{v.style.width='720px';v.style.maxWidth='100%';v.style.height='360px';}")
    video.scroll_into_view_if_needed()
    video.focus()
    page.keyboard.press('Space')
    page.wait_for_function("()=>{const v=document.querySelector('main .wp-block-video video');return !v.paused&&v.readyState>=2}")
    page.wait_for_timeout(250)
    page.keyboard.press('Space')
    page.wait_for_function("()=>document.querySelector('main .wp-block-video video').paused")
    geometry = video.evaluate('''v=>{const r=v.getBoundingClientRect(),s=getComputedStyle(v),scale=Math.min(r.width/v.videoWidth,r.height/v.videoHeight);return {element:[r.width,r.height],native:[v.videoWidth,v.videoHeight],paintedFullFrame:[v.videoWidth*scale,v.videoHeight*scale],objectFit:s.objectFit,controls:v.controls,poster:v.poster};}''')
    assert all(abs(actual - expected) < .1 for actual, expected in zip(geometry['element'], [720, 360])), geometry
    assert geometry['native'] == [1122, 1402] and geometry['objectFit'] == 'contain' and geometry['controls'], geometry
    frame = video.evaluate('''v=>{const c=document.createElement('canvas');c.width=v.videoWidth;c.height=v.videoHeight;c.getContext('2d').drawImage(v,0,0);return c.toDataURL('image/png').split(',')[1];}''')
    edges = edge_comparison(video.screenshot(style='video::-webkit-media-controls{display:none!important}'), base64.b64decode(frame), geometry['paintedFullFrame'])
    assert edges['fullSourceEdgesPainted'], edges
    edges['nativeControlsSuppressedOnlyDuringPixelScreenshot'] = True
    result = {'actualDraftPreview': ordinary, 'constraintFixture': 'Owner inline width720px/max-width100%/height360px are applied to exercise the normal native video selector under a constrained owner layout. The production object-fit rule and core poster CSS remain unchanged.', 'geometry': geometry, 'actualDecodedFrameEdgeComparison': edges}
    context.close()
    return result


def main():
    records = []
    archives = []
    for path in PARTS:
        with zipfile.ZipFile(path) as archive:
            manifest = json.loads(archive.read('manifest.json'))
        records.extend(manifest['records'])
        archives.append({'bundleID': manifest['bundle_id'], 'bytes': path.stat().st_size,
                         'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    assert len(PARTS) == 3 and len(records) == 26
    EXPECTATIONS.parent.mkdir(parents=True, exist_ok=True)
    EXPECTATIONS.write_text(json.dumps(records))
    report = {'generatedAtUTC': datetime.now(timezone.utc).isoformat(), 'scope': 'Actual isolated WordPress owner GUI import, production theme assets, native Gutenberg SAVE and real photographic film playback. Production counts exclude the fourteen synthetic owner fixtures. The film is a silent photographic sequence, not filmed salon footage.', 'productionFilmVerified': False, 'remoteWordPressHTTPSFetchVerified': False, 'checks': {}, 'observations': {}, 'parts': archives, 'passed': False}
    report['themeAssetSHA256'] = {str(path.relative_to(ROOT / 'theme/bixie-editorial')): hashlib.sha256(path.read_bytes()).hexdigest() for path in (ROOT / 'theme/bixie-editorial/assets/css/editorial.css', ROOT / 'theme/bixie-editorial/assets/js/editorial.js')}
    report['regression'] = {'actualWordPressCoreRule': '.wp-block-video [poster] { object-fit: cover }', 'before': {'computedObjectFit': 'cover', 'nativeVideoDimensions': [1122, 1402], 'desktopElementDimensions': [1110.40625, 935], 'result': 'Portrait playing frame cropped by native poster CSS specificity.'}, 'correction': 'Theme native video contain rule explicitly retains the full playing frame and poster. No image aspect-ratio reset or publication gate change.'}
    preview_active = False
    try:
        before = inspect('inspect')
        assert len(before['fixtures']) == 14
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox'])
            admin = browser.new_context(storage_state='/workspace/wp-test/qa-auth-state.json')
            page = admin.new_page()
            errors = []
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.goto(SITE + '/wp-admin/tools.php?page=bixie-setup', wait_until='networkidle')
            assert page.locator('#adminmenu').count() == 1
            assert not page.locator('#bixie-overwrite').is_checked()
            page.locator('#bixie-bundle-files').set_input_files([str(path) for path in PARTS])
            page.locator('#bixie-bundle-upload').click()
            page.wait_for_function("()=>document.querySelector('#bixie-bundle-status').textContent.startsWith('3 of 3 selected part(s) verified')", timeout=120000)
            page.locator('#bixie-import-start').click()
            page.wait_for_function("()=>document.querySelector('#bixie-import-message').textContent.startsWith('Import finished.')", timeout=180000)
            print('phase: owner GUI import completed', flush=True)
            after = inspect('inspect')
            assert before['fixtures'] == after['fixtures'] and before['pilot'] == after['pilot']
            assert before['settings'] == after['settings']
            report['checks']['ownerFixturesPilotAndSettingsPreserved'] = True
            report['observations']['importCounts'] = after['import']['counts']
            report['observations']['expectedMissingCatalogSources'] = 'Additional catalog media outside these supplied Home parts and the earlier four-look pilot remain absent; import diagnostics and Home publication gates remain enabled.'
            import_errors = [entry for entry in after['import'].get('log', []) if entry.get('level') == 'error']
            assert not any(entry.get('key') in {record['key'] for record in records} for entry in import_errors), import_errors
            report['observations']['separateOutsideHomeCatalogDiagnostics'] = import_errors
            media = {}
            for record in records:
                actual = after['media'][record['key']]
                assert actual['id'] and actual['sourceExists'] and actual['sourceSHA256'] == record['sha256'], (record['key'], actual)
                assert actual['approved'] and actual['nativeVerified'] and actual['qualified'], (record['key'], actual)
                if record['key'] != 'home-motion-film':
                    assert actual['nativeSize'] == [record['width'], record['height']]
                native = admin.request.get(actual['nativeURL'])
                assert native.status == 200 and hashlib.sha256(native.body()).hexdigest() == record['sha256']
                media[record['key']] = actual
            film = media['home-motion-film']
            assert set(film['filmSourceKeys']) == {'home-angle-front', 'home-angle-side', 'home-angle-back'}
            report['checks']['all25HomePhotosNativeSourceChecksumsDimensionsAndReviewGates'] = True
            report['checks']['actualFilmAndThreeDistinctReviewedNativeSourcesQualify'] = True
            print('phase: all production Home sources and film gates verified', flush=True)
            report['observations']['productionMedia'] = media
            for part in archives:
                assert after['parts'][part['bundleID']]['archive_sha256'] == part['sha256']
            report['checks']['actualGuiMultipartArchivesVerifiedAndImported'] = True
            assert after['home'] and all(home['status'] == 'draft' and not home['gate']['complete'] for home in after['home'])
            report['checks']['incompleteHomeRemainsDraft'] = True
            report['observations']['existingHomeDraftGates'] = after['home']
            preview = inspect('create-preview')
            preview_active = True
            assert preview['status'] == 'draft' and not preview['fullHomeGate']['complete']
            assert preview['nativeFilmIDs'] == [film['id']]
            report['observations']['temporaryDraftPreview'] = preview
            # Actual Gutenberg parser and SAVE in the native post editor.
            page.goto(preview['editURL'], wait_until='networkidle')
            page.wait_for_function("()=>window.wp?.data?.select('core/block-editor')?.getBlocks()?.length>0", timeout=60000)
            validation = page.evaluate('''()=>{const flatten=(bs)=>bs.flatMap(b=>[b,...flatten(b.innerBlocks||[])]);const blocks=wp.data.select('core/block-editor').getBlocks();const all=flatten(blocks);const roundtrip=flatten(wp.blocks.parse(wp.blocks.serialize(blocks)));return {total:all.length,invalid:all.filter(b=>b.isValid===false).map(b=>({name:b.name,attrs:b.attributes})),roundtripInvalid:roundtrip.filter(b=>b.isValid===false).map(b=>({name:b.name,attrs:b.attributes})),imageIDs:all.filter(b=>b.name==='core/image').map(b=>b.attributes.id),videos:all.filter(b=>b.name==='core/video').map(b=>({id:b.attributes.id,src:b.attributes.src,poster:b.attributes.poster}))};}''')
            assert not validation['invalid'] and not validation['roundtripInvalid'], validation
            assert validation['videos'][0]['id'] == film['id'] and validation['videos'][0]['src'] == film['displayURL']
            page.evaluate("async()=>{await wp.data.dispatch('core/editor').savePost();}")
            page.wait_for_function("()=>!wp.data.select('core/editor').isSavingPost()&&!wp.data.select('core/editor').isEditedPostDirty()", timeout=60000)
            saved = inspect('preview-inspect')
            assert saved['status'] == 'draft' and saved['nativeFilmIDs'] == [film['id']] and not saved['fullHomeGate']['complete']
            report['checks']['actualGutenbergSaveAndRoundtripNoInvalidNativePhotoVideoBlocks'] = True
            report['observations']['nativeBlockValidation'] = validation
            print('phase: native Gutenberg SAVE validation completed', flush=True)
            # Full native Home pattern in a private draft preview. No fake public Home.
            photo_observations = {}
            for name, width, height in [('desktop', 1440, 1100), ('tablet', 768, 1024), ('phone', 390, 844), ('small-phone', 320, 720)]:
                context = browser.new_context(storage_state='/workspace/wp-test/qa-auth-state.json', viewport={'width': width, 'height': height}, reduced_motion='reduce')
                view = context.new_page()
                view.on('pageerror', lambda error: errors.append(str(error)))
                view.goto(preview['previewURL'], wait_until='networkidle')
                view.wait_for_function("()=>document.querySelector('#bixie-film video')&&document.querySelector('.bixie-video-motion-toggle a[data-bixie-video-toggle]')", timeout=15000)
                painted = {}
                for key, actual in media.items():
                    if key in ('home-motion-film', 'home-motion-poster'):
                        continue
                    element = view.locator('img.wp-image-' + str(actual['id']))
                    assert element.count() == 1, (name, key, element.count())
                    element.scroll_into_view_if_needed()
                    element.evaluate('async e=>{await e.decode();}')
                    geometry = element.evaluate('''e=>{const r=e.getBoundingClientRect(),s=getComputedStyle(e);return {width:r.width,height:r.height,natural:[e.naturalWidth,e.naturalHeight],currentSource:e.currentSrc||e.src,objectFit:s.objectFit,aspectRatio:s.aspectRatio,opacity:s.opacity,visibility:s.visibility,transform:s.transform,containIntrinsicSize:s.containIntrinsicSize};}''')
                    assert geometry['width'] > 0 and geometry['height'] > 0 and geometry['opacity'] == '1' and geometry['visibility'] == 'visible', (key, geometry)
                    assert abs(geometry['width'] / geometry['height'] - record_ratio(actual)) < .015, (key, geometry)
                    assert geometry['objectFit'] == 'contain' and geometry['transform'] == 'none', (key, geometry)
                    screenshot = element.screenshot()
                    pixels = paint_stats(screenshot)
                    assert pixels['nonFlatPixels'], (key, pixels)
                    geometry['paint'] = pixels
                    selected_source = context.request.get(geometry['currentSource'])
                    assert selected_source.status == 200
                    geometry['sourceEdgeComparison'] = edge_comparison(screenshot, selected_source.body())
                    assert geometry['sourceEdgeComparison']['fullSourceEdgesPainted'], (name, key, geometry['sourceEdgeComparison'])
                    painted[key] = geometry
                assert len(painted) == 24
                # The 25th Home source is the native video poster, not a duplicate img.
                assert view.locator(VIDEO).get_attribute('poster') == media['home-motion-poster']['displayURL']
                assert view.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
                photo_observations[name] = {'actualImageElements': painted, 'actualPosterURL': media['home-motion-poster']['displayURL'], 'horizontalOverflow': False}
                print('phase: real Home images painted at ' + name, flush=True)
                context.close()
            report['checks']['24UniqueHomeNativeImageElementsPaintFullAspectAtFourWidths'] = True
            report['checks']['25thHomeSourceUsedAsNativeMoviePoster'] = True
            report['observations']['homePhotosAtFourWidths'] = photo_observations
            film_observations = {}
            for name, width, height in [('desktop', 1440, 1100), ('phone', 390, 844)]:
                context = browser.new_context(storage_state='/workspace/wp-test/qa-auth-state.json', viewport={'width': width, 'height': height})
                view = context.new_page()
                view.on('pageerror', lambda error: errors.append(str(error)))
                view.goto(preview['previewURL'], wait_until='networkidle')
                view.locator(VIDEO).scroll_into_view_if_needed()
                wait_playing(view)
                autoplay = sample(view)
                film_observations[name] = {'visibleAutoplayWithoutClick': autoplay}
                report['observations']['actualProductionFilmBrowser'] = film_observations
                assert autoplay['timeAdvanced'] and autoplay['after']['decodedFrames'] > 0 and autoplay['after']['videoWidth'] == 1122 and autoplay['after']['videoHeight'] == 1402, autoplay
                assert autoplay['after']['muted'] and autoplay['after']['playsInline'] and autoplay['after']['controls']
                geometry = view.locator(VIDEO).evaluate('''v=>{const r=v.getBoundingClientRect(),s=getComputedStyle(v);const scale=Math.min(r.width/v.videoWidth,r.height/v.videoHeight);return {element:[r.width,r.height],native:[v.videoWidth,v.videoHeight],paintedFullFrame:[v.videoWidth*scale,v.videoHeight*scale],objectFit:s.objectFit,objectPosition:s.objectPosition,transform:s.transform,opacity:s.opacity,visibility:s.visibility};}''')
                film_observations[name]['geometry'] = geometry
                assert geometry['objectFit'] == 'contain' and geometry['transform'] == 'none' and geometry['opacity'] == '1' and geometry['visibility'] == 'visible', geometry
                assert abs(geometry['paintedFullFrame'][0] / geometry['paintedFullFrame'][1] - 1122 / 1402) < .001
                assert max(geometry['paintedFullFrame'][i] - geometry['element'][i] for i in [0, 1]) < .01
                decoded_paint = paint_stats(view.locator(VIDEO).screenshot())
                assert decoded_paint['nonFlatPixels']
                view.locator(VIDEO).focus()
                view.keyboard.press('Space')
                wait_paused(view)
                keyboard_pause = sample(view)
                assert keyboard_pause['timeStopped'] and keyboard_pause['after']['nativeVideoFocused']
                # Capture the actual paused decoded frame; suppress only the native
                # control overlay during this screenshot, with controls still enabled.
                decoded_frame = view.locator(VIDEO).evaluate('''v=>{const c=document.createElement('canvas');c.width=v.videoWidth;c.height=v.videoHeight;c.getContext('2d').drawImage(v,0,0);return c.toDataURL('image/png').split(',')[1];}''')
                frame_screenshot = view.locator(VIDEO).screenshot(style='video::-webkit-media-controls{display:none!important}')
                movie_edges = edge_comparison(frame_screenshot, base64.b64decode(decoded_frame), geometry['paintedFullFrame'])
                assert movie_edges['fullSourceEdgesPainted'], (name, movie_edges)
                movie_edges['nativeControlsSuppressedOnlyDuringPixelScreenshot'] = True
                view.locator('.bixie-hero').scroll_into_view_if_needed()
                view.wait_for_timeout(150)
                view.locator(VIDEO).scroll_into_view_if_needed()
                view.wait_for_timeout(200)
                persistent_pause = sample(view)
                assert persistent_pause['timeStopped']
                view.locator(CONTROL).click()
                wait_playing(view)
                view.locator('.bixie-hero').scroll_into_view_if_needed()
                wait_paused(view)
                offscreen = sample(view)
                assert offscreen['timeStopped']
                view.locator(VIDEO).scroll_into_view_if_needed()
                wait_playing(view)
                resumed = sample(view)
                assert resumed['timeAdvanced']
                control = view.locator(CONTROL)
                assert control.get_attribute('role') == 'button' and control.get_attribute('aria-controls') == view.locator(VIDEO).get_attribute('id')
                assert view.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
                film_observations[name] = {'visibleAutoplayWithoutClick': autoplay, 'geometry': geometry, 'decodedPaint': decoded_paint, 'actualDecodedFrameEdgeComparison': movie_edges, 'nativeKeyboardSpacePause': keyboard_pause, 'nativePauseAfterLeavingAndReturning': persistent_pause, 'offscreenAutoplayPause': offscreen, 'returnAutoplayResumes': resumed}
                print('phase: actual production film verified at ' + name, flush=True)
                context.close()
            reduced = browser.new_context(storage_state='/workspace/wp-test/qa-auth-state.json', viewport={'width': 390, 'height': 844}, reduced_motion='reduce')
            view = reduced.new_page()
            view.on('pageerror', lambda error: errors.append(str(error)))
            view.goto(preview['previewURL'], wait_until='networkidle')
            view.locator(VIDEO).scroll_into_view_if_needed()
            view.wait_for_function("()=>document.querySelector('#bixie-film video').readyState>=1")
            wait_paused(view)
            startup = sample(view)
            assert startup['timeStopped'] and not startup['after']['autoplay']
            view.locator(CONTROL).click()
            wait_playing(view)
            manual_play = sample(view)
            assert manual_play['timeAdvanced']
            film_observations['reducedMotion'] = {'startup': startup, 'manualPlay': manual_play}
            reduced.close()
            report['observations']['actualProductionFilmBrowser'] = film_observations
            report['checks']['realNativePortraitFilmDecodedAutoplayMutedInlineFullFrameDesktopPhone'] = True
            report['checks']['nativeSpacePausePersistsAndOffscreenAutoplayPausesResumes'] = True
            report['checks']['reducedMotionNoAutoplayAndExplicitPlayWorks'] = True
            ordinary_observation = ordinary_poster_check(browser, errors)
            report['checks']['ordinaryNativePosterVideoRetainsFullFrameInConstrainedOwnerLayout'] = True
            report['observations']['ordinaryNativePosterVideo'] = ordinary_observation
            report['productionFilmVerified'] = True
            report['pageErrors'] = errors
            assert not errors
            report['checks']['noJavaScriptErrors'] = True
            admin.close()
            browser.close()
        report['passed'] = True
    except Exception as error:
        report['failure'] = str(error)
        report['traceback'] = traceback.format_exc()
        raise
    finally:
        if preview_active:
            report['cleanup'] = inspect('cleanup')
            final = inspect('inspect')
            assert report['cleanup']['exactTemporaryPagesRemoved'] and before['fixtures'] == final['fixtures'] and before['pilot'] == final['pilot'] and before['settings'] == final['settings']
            report['cleanup']['all26ProductionHomeAttachmentsPreserved'] = all(final['media'][key]['id'] == actual['id'] and final['media'][key]['qualified'] for key, actual in after['media'].items())
            assert report['cleanup']['all26ProductionHomeAttachmentsPreserved']
        REPORT.write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps({'passed': report['passed'], 'productionFilmVerified': report['productionFilmVerified'], 'checks': len(report['checks']), 'report': str(REPORT), 'failure': report.get('failure')}, indent=2))


def record_ratio(actual):
    return actual['nativeSize'][0] / actual['nativeSize'][1]


if __name__ == '__main__':
    main()
