#!/usr/bin/env python3
"""Decode a synthetic MP4 in Chromium with the production theme assets.

The moving test pattern is a QA fixture, never homepage photography or a
production film. This test neither authenticates to WordPress nor changes it.
"""
import asyncio
import hashlib
import json
import mimetypes
import subprocess
import threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from playwright.async_api import async_playwright

PACKAGE = Path(__file__).resolve().parents[1]
THEME = PACKAGE / "theme" / "bixie-editorial"
FIXTURE = Path("/workspace/wp-test/fixtures/theme-autoplay-test.mp4")
REPORT = Path(__file__).with_name("theme-real-video-report.json")
CHROMIUM = "/usr/bin/chromium"

SCENARIOS = {
    "default": {"motionEnabled": True, "motionSpeed": 15, "videoAutoplay": True},
    "owner_disabled": {"motionEnabled": False, "motionSpeed": 15, "videoAutoplay": False},
    "owner_video_disabled": {"motionEnabled": True, "motionSpeed": 15, "videoAutoplay": False},
    "owner_motion_disabled": {"motionEnabled": False, "motionSpeed": 15, "videoAutoplay": True},
}

HTML = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Synthetic video — theme QA only</title>
<link rel="stylesheet" href="/theme/assets/css/editorial.css">
<script>window.BixieEditorialSettings=__SETTINGS__;</script>
<script src="/theme/assets/js/editorial.js" defer></script>
</head><body>
<main class="bixie-home">
<section class="wp-block-group bixie-section bixie-film-section is-ink" id="bixie-film">
<p class="bixie-eyebrow">Synthetic moving pattern · QA fixture only</p>
<figure class="wp-block-video bixie-film">
<video id="test-movie" src="/fixture/theme-autoplay-test.mp4"
 width="480" height="270" autoplay muted loop playsinline controls preload="auto"></video>
</figure>
<div class="wp-block-group bixie-motion-controls">
<div class="wp-block-buttons"><div class="wp-block-button bixie-video-motion-toggle">
<a class="wp-block-button__link wp-element-button" href="#bixie-film">Play test film</a>
</div></div>
<p class="bixie-caption">No hairstyle imagery. No audio. Test fixture only.</p>
</div></section>
<div aria-hidden="true" style="height:2000px"></div>
<section id="away" class="bixie-section"><p>Offscreen observation target.</p></section>
</main></body></html>"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/":
            scenario = parse_qs(parsed.query).get("scenario", ["default"])[0]
            settings = dict(SCENARIOS.get(scenario, SCENARIOS["default"]))
            settings["filmPauseLabel"] = "Pause test film"
            payload = HTML.replace("__SETTINGS__", json.dumps(settings)).encode()
            content_type = "text/html; charset=utf-8"
        elif parsed.path == "/fixture/theme-autoplay-test.mp4":
            payload = FIXTURE.read_bytes()
            content_type = "video/mp4"
        elif parsed.path.startswith("/theme/"):
            target = (THEME / unquote(parsed.path[len("/theme/"):])).resolve()
            if not target.is_relative_to(THEME.resolve()) or not target.is_file():
                self.send_error(404)
                return
            payload = target.read_bytes()
            content_type = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        elif parsed.path == "/favicon.ico":
            self.send_response(204)
            self.end_headers()
            return
        else:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(payload)


STATE_JS = """() => {
const v=document.querySelector('#test-movie');
const q=v.getVideoPlaybackQuality ? v.getVideoPlaybackQuality() : null;
return {currentTime:v.currentTime, duration:v.duration, paused:v.paused,
ended:v.ended, muted:v.muted, playsInline:v.playsInline, controls:v.controls,
autoplay:v.autoplay, readyState:v.readyState, networkState:v.networkState,
videoWidth:v.videoWidth, videoHeight:v.videoHeight,
decodedFrames:q ? q.totalVideoFrames : (v.webkitDecodedFrameCount || null),
error:v.error ? {code:v.error.code,message:v.error.message} : null,
nativeVideoFocused:document.activeElement===v,
controlLabel:document.querySelector('.bixie-video-motion-toggle a').textContent};
}"""


async def state(page):
    return await page.evaluate(STATE_JS)


async def loaded(page):
    await page.wait_for_function("""() => {
const v=document.querySelector('#test-movie');
return v.readyState>=2 && v.videoWidth===480 && v.videoHeight===270 &&
document.querySelector('.bixie-video-motion-toggle a[data-bixie-video-toggle]');
}""", timeout=12000)


async def playing(page):
    await page.wait_for_function("""() => {
const v=document.querySelector('#test-movie');
return !v.paused && !v.ended && v.readyState>=2;
}""", timeout=8000)


async def paused(page):
    await page.wait_for_function("() => document.querySelector('#test-movie').paused", timeout=5000)


async def sample(page, milliseconds=550):
    before = await state(page)
    await page.wait_for_timeout(milliseconds)
    after = await state(page)
    advance = (after["currentTime"] - before["currentTime"]) % after["duration"]
    return {"before": before, "after": after, "observedMilliseconds": milliseconds,
            "timelineAdvanceSeconds": advance,
            "timeAdvanced": advance > .15 and not after["paused"],
            "timeStopped": abs(after["currentTime"] - before["currentTime"]) < .08 and after["paused"]}


async def run_checks(report, base_url):
    errors = []
    report["javascriptErrors"] = errors
    checks = report["checks"]
    observations = report["observations"]
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(executable_path=CHROMIUM, args=["--no-sandbox"])

        async def new_page(scenario="default", reduced=False):
            context = await browser.new_context(viewport={"width": 1280, "height": 1100},
                                                reduced_motion="reduce" if reduced else "no-preference")
            page = await context.new_page()
            page.on("pageerror", lambda error: errors.append({"scenario": scenario, "message": str(error)}))
            await page.goto(base_url + "/?scenario=" + scenario, wait_until="networkidle")
            await loaded(page)
            return page

        page = await new_page()
        await playing(page)
        observations["visibleAutoplay"] = await sample(page)
        initial = observations["visibleAutoplay"]["after"]
        checks["actualH264DecodedAt480x270"] = initial["videoWidth"] == 480 and initial["videoHeight"] == 270 and initial["decodedFrames"] > 0
        checks["visibleAutoplayTimeAdvances"] = observations["visibleAutoplay"]["timeAdvanced"]
        checks["mutedInlineWithNativeControls"] = initial["muted"] and initial["playsInline"] and initial["controls"]

        control = page.locator(".bixie-video-motion-toggle a")
        await control.click()
        await paused(page)
        observations["manualButtonPause"] = await sample(page, 350)
        checks["manualButtonPauseStopsTimeline"] = observations["manualButtonPause"]["timeStopped"]
        await control.click()
        await playing(page)
        observations["manualButtonPlay"] = await sample(page, 350)
        checks["manualButtonPlayAdvancesTimeline"] = observations["manualButtonPlay"]["timeAdvanced"]

        # Focus and Space operate Chromium's actual native video control.
        await page.locator("#test-movie").focus()
        await page.keyboard.press("Space")
        await paused(page)
        observations["nativeKeyboardPause"] = await state(page)
        checks["nativeControlKeyboardPause"] = observations["nativeKeyboardPause"]["paused"] and observations["nativeKeyboardPause"]["nativeVideoFocused"]
        await page.locator("#away").scroll_into_view_if_needed()
        await page.wait_for_timeout(150)
        await page.locator("#test-movie").scroll_into_view_if_needed()
        await page.wait_for_timeout(200)
        observations["nativePauseAfterReturn"] = await sample(page, 350)
        checks["nativePausePersistsAfterLeavingAndReturning"] = observations["nativePauseAfterReturn"]["timeStopped"]

        await control.click()
        await playing(page)
        await page.locator("#away").scroll_into_view_if_needed()
        await paused(page)
        observations["offscreenPause"] = await sample(page, 350)
        checks["offscreenAutoplayPauses"] = observations["offscreenPause"]["timeStopped"]
        await page.locator("#test-movie").scroll_into_view_if_needed()
        await playing(page)
        observations["returnAutoplay"] = await sample(page, 350)
        checks["returnAutoplayResumes"] = observations["returnAutoplay"]["timeAdvanced"]

        reduced = await new_page(reduced=True)
        await paused(reduced)
        observations["reducedMotionStartup"] = await sample(reduced)
        checks["reducedMotionStartupNoAutoplay"] = observations["reducedMotionStartup"]["timeStopped"] and not observations["reducedMotionStartup"]["after"]["autoplay"]
        await reduced.locator(".bixie-video-motion-toggle a").click()
        await playing(reduced)
        observations["reducedMotionVisitorPlay"] = await sample(reduced, 350)
        checks["reducedMotionExplicitVisitorPlayWorks"] = observations["reducedMotionVisitorPlay"]["timeAdvanced"]

        for scenario in ("owner_disabled", "owner_video_disabled", "owner_motion_disabled"):
            owner = await new_page(scenario)
            await paused(owner)
            observations[scenario + "Startup"] = await sample(owner)
            checks[scenario + "NoAutoplay"] = observations[scenario + "Startup"]["timeStopped"] and not observations[scenario + "Startup"]["after"]["autoplay"]
            await owner.locator(".bixie-video-motion-toggle a").click()
            await playing(owner)
            observations[scenario + "VisitorPlay"] = await sample(owner, 350)
            checks[scenario + "ExplicitVisitorPlayWorks"] = observations[scenario + "VisitorPlay"]["timeAdvanced"]

        await browser.close()
    checks["noJavaScriptErrors"] = not errors


def main():
    FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    ffmpeg = ["/usr/bin/ffmpeg", "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-i",
              "testsrc2=size=480x270:rate=24", "-t", "4", "-an", "-c:v", "libx264", "-preset",
              "veryfast", "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-y", str(FIXTURE)]
    subprocess.run(ffmpeg, check=True)
    probe = subprocess.run(["/usr/bin/ffprobe", "-v", "error", "-show_streams", "-show_format",
                            "-of", "json", str(FIXTURE)], check=True, capture_output=True, text=True)
    report = {
        "generatedAtUTC": datetime.now(timezone.utc).isoformat(),
        "scope": "Actual Chromium decoding of a clean synthetic moving-pattern MP4 using current theme CSS/JS; no WordPress authentication or production film verification.",
        "syntheticFixtureOnly": True, "productionFilmCreatedOrVerified": False,
        "mediaMethodsMocked": False,
        "fixture": {"path": str(FIXTURE), "bytes": FIXTURE.stat().st_size,
                    "sha256": hashlib.sha256(FIXTURE.read_bytes()).hexdigest(),
                    "generationCommand": ffmpeg, "ffprobe": json.loads(probe.stdout)},
        "themeAssetSHA256": {str(path.relative_to(THEME)): hashlib.sha256(path.read_bytes()).hexdigest()
                             for path in (THEME / "assets/css/editorial.css", THEME / "assets/js/editorial.js")},
        "checks": {}, "observations": {},
    }
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    try:
        asyncio.run(run_checks(report, "http://127.0.0.1:" + str(server.server_port)))
    except Exception as error:
        report["fatalError"] = str(error)
    finally:
        server.shutdown()
        server.server_close()
    report["passed"] = not report.get("fatalError") and bool(report["checks"]) and all(report["checks"].values())
    report["passedChecks"] = sum(value is True for value in report["checks"].values())
    report["totalChecks"] = len(report["checks"])
    REPORT.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"passed": report["passed"], "passedChecks": report["passedChecks"],
                      "totalChecks": report["totalChecks"], "report": str(REPORT),
                      "fatalError": report.get("fatalError")}, indent=2))
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
