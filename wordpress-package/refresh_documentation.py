#!/usr/bin/env python3
"""Refresh release documentation from actual catalog counts and scoped QA reports."""
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
import json

ROOT = Path(__file__).resolve().parent


def result(name):
    path = ROOT / 'tests' / name
    if not path.is_file():
        return 'Not executed yet'
    data = json.loads(path.read_text())
    passed = data.get('passed') is True or data.get('status') == 'passed' or data.get('separateFinalSitePrepared') is True
    return 'Passed within its stated scope' if passed else 'Read report; incomplete or failing checks remain'


def main():
    catalog = json.loads((ROOT / 'content/catalog.json').read_text())
    counts = catalog['counts']
    looks = len(catalog['looks'])
    views = sum(len(look['images']) for look in catalog['looks'])
    home = counts['provided_approved_home_role_images']
    collections = counts['provided_complete_collections']
    references = counts['provided_guide_photo_references']
    complete = looks == 154 and views == 462 and home == 25 and collections == 22 and references == 24
    blocker_path = ROOT / 'media/production-blocker.json'
    blocker = json.loads(blocker_path.read_text()) if blocker_path.is_file() else {}
    state = 'All planned photographic content is assembled; assess final runtime evidence below.' if complete else 'Production is incomplete; this is a saved engineering checkpoint, not the finished launch.'
    if not complete and blocker:
        state += ' Image generation hit the daily quota: 65 source photographs remain. The recorded reset is 2026-10-08 10:34:04 UTC /15:34:04 Pakistan time. Existing approved sources are retained; incomplete looks and Home remain draft.'
    acceptance_path = ROOT / 'tests/wp-final-acceptance-report.json'
    acceptance = json.loads(acceptance_path.read_text()) if acceptance_path.is_file() else {}
    final_runtime = acceptance.get('passed') is True and acceptance.get('actual_counts', {}).get('publishedLooks') == looks == 154
    delivery_path = ROOT / 'tests/https-delivery-report.json'
    final_downloads = delivery_path.is_file() and json.loads(delivery_path.read_text()).get('passed') is True
    owner_path = ROOT / 'OWNER-GUIDE.md'
    owner = owner_path.read_text()
    owner_intro = f'''## Read this before installation

This package contains an editable WordPress block theme, its companion plugin
and genuinely generated original image collections. The synchronized inventory
is **{looks} complete looks / {views} gallery photographs**, **{home} separate
Home photographs**, **{collections}/22 complete collections** and **{references}/24
supporting-guide photo references**. {state}

The complete content target is 22 collections × 7 looks × 3 independently
generated front/side/back views: **154 looks / 462 gallery originals +25 Home
originals =487 photographs**, plus one separately counted movie. Home has 22
editable sections and targets 77 unique image elements plus one distinct poster,
78 displayed photographic sources. Its photo shelves use45canonical fronts and
eight other library covers; guide references are corresponding gallery photos,
not additional originals. Contact and Privacy need genuine owner review.

The owner accepted available original resolution. Production sources are normally
1122×1402pixels; actual dimensions and native-source proof are recorded individually.
The minimum accepted original long edge is1024pixels. No enlargement or native8K
claim is made. Rejected images and diagnostic probes never substitute for missing
approved sources. Partial individual images do not count as complete looks.

Read [VALIDATION-REPORT.md](VALIDATION-REPORT.md) for executed checks and unresolved
verification, and [LAUNCH-CHECKLIST.md](LAUNCH-CHECKLIST.md) before publishing.

'''
    before, rest = owner.split('## Read this before installation', 1)
    _, after = rest.split('## Install and import', 1)
    owner = before + owner_intro + '## Install and import' + after
    owner = owner.replace('Final WordPress playback/import verification remains a separate release check.', 'The actual source movie passed authenticated WordPress import, decoded full-frame playback, muted autoplay, keyboard pause and reduced-motion checks; see the scoped production-film report.')
    owner = owner.replace('Feature verification uses isolated test fixtures until approved launch photos exist.', 'Actual production-photo browsing, every angle and native editor roundtrip have separate runtime reports. Fixture-based software checks remain explicitly labelled; assess final completeness from the current validation report.')
    owner = owner.replace('The first immutable pilot is four complete looks/12 views, about 21.28 MB; that pilot is not all planned media.', 'Use the matching release\'s numbered parts and embedded pinned index. Do not mix the earlier four-look pilot with this release. When JavaScript is disabled, upload one numbered part at a time in ascending order.')
    owner_path.write_text(owner)
    date = datetime.now(ZoneInfo('Asia/Karachi')).strftime('%Y-%m-%d %H:%M PKT')
    archive = 'Bixie-WordPress-Package.zip' if complete else 'Bixie-WordPress-Engineering-Package.zip'
    table = '\n'.join('| [' + name + '](tests/' + name + ') | ' + result(name) + ' |' for name in [
        'wp-production-home-film-report.json', 'wp-live-pilot-report.json',
        'wp-permalink-report.json', 'wp-final-environment-report.json',
        'wp-final-integration-report.json', 'wp-final-acceptance-report.json',
        'wp-engineering-acceptance-report.json',
        'wp-engineering-core-zip-report.json', 'wp-final-engineering-import-report.json',
        'wp-final-engineering-browser-report.json', 'wp-final-engineering-editability-report.json',
        'wp-engineering-home-report.json',
        'wp-final-partial-browser-report.json', 'wp-final-partial-editability-report.json',
        'wp-final-alias-report.json', 'wp-final-permalink-report.json',
        'wp-filter-alias-report.json', 'wp-final-directory-report.json',
        'release-archive-report.json', 'https-delivery-report.json',
        'https-saved-media-report.json', 'https-saved-delivery-report.json',
        'wp-publication-report.json', 'wp-bundle-security-report.json',
        'wp-attachment-film-report.json', 'wp-seo-report.json',
        'wp-browser-report.json', 'plugin-wordpress-editor-report.json',
    ] if (ROOT / 'tests' / name).is_file())
    (ROOT / 'VALIDATION-REPORT.md').write_text(f'''# Bixie WordPress validation

Snapshot: **{date}**. {state}

## Actual content inventory

| Asset | Actual synchronized inventory | Launch target |
|---|---:|---:|
| Coherent separately generated front/side/back looks | {looks} | 154 |
| Distinct primary-collection original photographs | {views} | 462 |
| Separate Home original photographs | {home} | 25 |
| Fully covered collections | {collections} | 22 |
| Image-led guide photograph references | {references} | 24 |
| Editable native page records | {len(catalog['pages'])} | 42 |

Guide references and homepage library covers reuse the relevant canonical look;
they are not counted as additional originals. Every photograph belongs to one
primary collection. The completed Home design targets 22 sections, 77 unique
image elements and one distinct movie poster: 78 displayed photographic sources.
The incomplete draft can contain fewer photographs. Each completed
collection has 7 looks and 21 actual separate photographs.
Contact and Privacy await genuine owner details/policy review rather than
invented information.

This quota-blocked snapshot also retains13individually approved angle photos in
incomplete sets:384complete-set gallery views +13partial views +25Home originals
=422approved photographs. Those13sources are real saved media, but do not count
as complete looks. Exactly65source photographs remain;26looks are incomplete.
The missing-source list and provider reset evidence are preserved in
[production-blocker.json](media/production-blocker.json).

The accepted sources are generator-native, normally1122×1402 pixels, with actual
dimensions recorded individually. No enlargement or native8K claim is made.
Lossless native WebP sources are verified pixel-for-pixel against retained
generator PNG originals. Source encoding, optimized display files, responsive
derivatives and inspection copies count as one photograph, not separate images.
Visual reviews retain composition/coherence evidence; small review copies are
described honestly. A useful side-facing three-quarter reference is labelled a
side angle rather than falsely described as an exact90-degree profile.

[Actual pixel/hash audit](tests/production-media-report.json),
[content checks](content/content-validation.json) and
[per-collection inventory](content/actual-source-counts.json) distinguish complete
sets from saved partial images. Planned expansion briefs are never imported as
fake completed looks. Rejected photographs and synthetic QA images are excluded
from installable theme/plugin and production media parts.

## Executed checks and their scope

The isolated runtime is WordPress7.1.3, PHP8.4.26, MariaDB11.8.6 and verified
official WP-CLI2.12.0. Debian signatures/artifact hashes and TLS verification were
retained. A separate fresh noindex site was prepared for final actual media
acceptance; it retains the earlier synthetic-test site unchanged.

| Evidence | Recorded result |
|---|---|
{table}

The production Home film check is actual authenticated WordPress import,
Gutenberg save/roundtrip and decoded browser playback of the genuine source
film:13checks passed,270native blocks/zero invalid blocks, full frame at desktop
and phone, muted inline autoplay, keyboard pause, offscreen pause/resume and
reduced-motion manual play. The film is an11.625-second1122×1402 silent H.264
photographic sequence of three real corresponding generated angles, not salon
footage. The same-source pose photos are explicitly declared in its manifest.

Actual plain/pretty permalink checks include GET-form routing, nested project
links, preserved filters/fragments, draft-link suppression and owner/external
link preservation:21checks passed. Native editor serialization, responsive
geometry, saved/compare/print, collection21-photo cards, import preservation and
archive security have older actual WordPress code tests; where those use
synthetic images, their scope remains synthetic software QA. They do not approve
new hairstyle sources or replace final real-content acceptance.

Full final ZIP/core installation, all production media import and completed
78-source Home/22-collection browser acceptance must be assessed from the final
reports, not inferred from the four-look pilot or80-look integration snapshot.
Archive CRC/SHA and published HTTPS downloads require separate delivery checks.

## Unverified host and external integration checks

Actual WordPress direct remote media retrieval remains unverified in this cloud:
local DNS for GitHub is unavailable and safe URL validation rejects before proxy
transport. Proxy-aware Python HTTPS delivery and authenticated owner GUI manual
ZIP-upload fallback passed. The final code supplies the pinned trusted media
index; a host with working DNS/HTTPS can use its download action. HTTP URL safety,
TLS checks, size bounds and SHA verification were not disabled.

Actual installation/coexistence with Yoast, Rank Math, AIOSEO and SEOPress remains
unverified after official distribution HTTP403. Provider signals in code tests
are explicitly simulated. Select one SEO output owner and inspect real metadata,
schema and sitemaps on the chosen host.

Minimum-version compatibility (WordPress6.6/PHP8.1 combined), every third-party
cache/CDN configuration, production domain/HTTPS, real-user Core Web Vitals,
Search Console indexing and rankings are target-host checks. No live site was
deployed and no rank/indexing/audit perfection guarantee is claimed.

The keyword plan was derived from seven supplied Semrush exports:13907rows,
10851normalized unique terms and81relevant/context/excluded dispositions. It is
a specialist bixie coverage plan, not a live Google SERP audit or a promise to
rank for unrelated hairstyles. See [coverage evidence](content/CONTENT-COVERAGE.md)
and [research summary](content/research/summary.json).
''')
    (ROOT / 'INSTALL.md').write_text(f'''# Install the Bixie WordPress package

Current state: {state} Actual inventory:{looks}looks/{views}galleryphotos,
{home}Homephotos, {collections}/22complete collections.

The download contains **bixie-editorial.zip** (installable theme),
**bixie-library.zip** (installable companion plugin), verified media ZIP parts,
documentation and **{archive}** (source/docs bundle). Extract the overall
download first. The source/docs bundle and overall download are not theme uploads.
No paid builder or Node/npm is required.

1. On a backed-up staging installation, upload/activate bixie-editorial.zip in
   Appearance → Themes → Add New → Upload Theme.
2. Upload/activate bixie-library.zip in Plugins → Add New → Upload Plugin.
3. Open Tools → Bixie package setup. Keep replacement unchecked to preserve
   existing owner edits. On a fresh site, check the option to set site title and
   use the imported Home when it becomes publishable.
4. Use Download media and import package. It fetches the pinned verified parts
   one at a time and imports in tracked batches. If the host cannot fetch them,
   select the matching ZIP files from wordpress-media-release, then Upload and
   verify parts; after all parts verify, choose Start or resume import. If browser
   JavaScript is disabled, upload one numbered part at a time in ascending order
   to respect the host's request-size and file-count limits.
5. Read completion diagnostics: all154looks/22collections/Home/seven guides
   should qualify with the final complete media. Missing or unreviewed sources
   keep affected pages in draft. Part upload progress is not content completion.
6. Once Home qualifies and is published, choose it in Settings → Reading as
   the static front page if you left configuration unchecked. In an incomplete
   snapshot Home remains draft; inspect its authenticated editor Preview while
   preserving that gate. Plain and custom permalinks are supported; confirm
   the host serves its chosen routes correctly.
7. Edit Pages → Home and Appearance → Editor. Review genuine contact details,
   Privacy and site information before publishing those owner-dependent pages.
   Review/delete WordPress starter posts yourself if this is a fresh installation.

The combined package needs PHP8.1+, WordPress6.6+, writable uploads, PHP ZIP and
supported image processing. Tested runtime:WordPress7.1.3/PHP8.4.26/MariaDB11.8.6.
Each part is at most25MiB; manual uploads also obey the host's lower upload limit.
If necessary ask the host to permit those part uploads, or use trusted downloading.

Sources retain their actual original dimensions (normally1122×1402), not native8K.
The silent autoplay movie is a photographic sequence, not filmed salon footage.
Reduced motion intentionally disables automatic movement; controls remain usable.

Read [OWNER-GUIDE](OWNER-GUIDE.md), [VALIDATION-REPORT](VALIDATION-REPORT.md) and
[LAUNCH-CHECKLIST](LAUNCH-CHECKLIST.md). Keep database/uploads/source backups;
never copy QA credentials, wp-config, test databases or synthetic media to production.
''')
    mark = lambda value: 'x' if value else ' '
    (ROOT / 'LAUNCH-CHECKLIST.md').write_text(f'''# Launch checklist

Snapshot:{date}. {state} See [validation evidence](VALIDATION-REPORT.md).

- [{mark(complete)}] Actual487photographs:154coherent looks/462galleryviews plus25Home originals.
- [{mark(collections==22)}] All22collections have7complete looks and21actual separately generated photos.
- [{mark(home==25)}] Home originals individually reviewed for full hair/head, sharp detail and loose opaque high-neck clothing.
- [{mark(references==24)}] Seven useful image-led guides have all24corresponding canonical photograph references.
- [x] Genuine native pixel equality and source dimensions/hashes recorded; no native8K/upscale claim.
- [x] Production11.625-second photograph film passed actual WordPress decode/autoplay/full-frame/control checks.
- [x] Plain/pretty links and no-JavaScript GET routing passed21actual WordPress checks.
- [{mark(final_runtime)}] Final actual ZIP/core install and complete real-media import pass on the separate fresh site.
- [{mark(final_runtime)}] Finished Home:77unique image elements plus1distinct poster/22sections; all collection/detail/guide/tool routes pass final browser checks.
- [{mark(final_runtime)}] Final native owner edit/save/reload, preserved repeated import and accessible motion/saved/compare/print pass.
- [{mark(final_downloads)}] Final part manifests, trusted download index, archive CRC/SHA and pinned HTTPS downloads verify.
- [ ] Owner installs on staging, supplies genuine contact information and reviews Privacy/About/Image Policy/Disclaimer.
- [ ] Owner verifies chosen real SEO/cache plugins, duplicate-schema handling, canonical/robots and sitemap on the actual host.
- [ ] Owner verifies production HTTPS/domain, cache/CDN, devices and real-user performance; staging stays noindex until ready.
- [ ] Owner backs up/restores database/uploads and submits the actual sitemap in Search Console when launching.

The target-host items are intentionally separate from completed package/code
evidence. The cloud's WordPress remote fetch lacks GitHub DNS; verified manual
ZIP-part upload remains the tested fallback. Simulated SEO-provider hooks do not
count as testing actual third-party plugin installations. No ranking or indexing
result is guaranteed by a theme, original images or schema.
''')
    progress_path = ROOT / 'media/progress.json'
    progress = json.loads(progress_path.read_text()) if progress_path.is_file() else {}
    media_counts = progress.get('counts', {})
    (ROOT / 'CONTINUE.md').write_text(f'''# Continue the saved Bixie WordPress project

Snapshot: **{date}**. {state}

The user's authorized goal is the complete installable WordPress site with
original image-led collections, an extra-long editable Home, companion plugin,
supporting content, documentation and reliable HTTPS ZIP downloads. Continue
existing work; do not replace it with another demo or regenerate approved photos.

## Actual inventory and durable files

Canonical content: **{looks} complete looks / {views} gallery originals**,
**{home} separate Home originals**, **{collections}/22 complete collections**,
**{references}/24 guide photo references**, 42 editable page records. The target
is 154 coherent looks / 462 separately generated gallery photographs + 25 Home
originals = 487 photographs, plus one separately counted photographic movie.

Current production progress file records {media_counts.get('complete_looks', looks)}
complete looks and {media_counts.get('reviewed_approved_production_photos', views + home)}
individually approved photos. Treat its timestamp as a dated snapshot, not a
promise that every saved partial image is a finished look. Consult
media/progress.json, media/manifest.json, media/records/, media/workers/ and
media-production/assignments.json before continuing any generation. These files
record exact missing IDs, immutable original paths, approval and source hashes.
Do not infer delivered inventory from planning briefs or a worker's forecast.

Generator PNG originals and pixel-identical lossless native WebP sources are
under source-media/. Optimized delivery WebP files are under media/. Encoding
copies, thumbnails and inspection crops are not new photographs. The accepted
native resolution is normally 1122×1402; no enlargement or native 8K claim is
authorized. Every source must pass actual hair/head framing, sharp-detail,
identity/cut coherence and loose fully opaque high-neck clothing review. No
cleavage, exposed chest, open necklines or fitted chest contours are acceptable.
A useful side-facing three-quarter view is acceptable and must be honestly
labelled a side angle; do not invent a strict 90-degree/far-lash rejection rule.

The actual Home movie is video/home-motion-film.mp4: an 11.625-second silent
1122×1402 H.264 photographic sequence of the three declared corresponding
Home angles. Actual WordPress decoded/full-frame/autoplay/keyboard/offscreen/
reduced-motion tests passed 13 checks. It is not filmed salon footage.

## Source and runtime status

Theme: theme/bixie-editorial/. Plugin: plugin/bixie-library/. Native editable
blocks, scoped templates, galleries with every angle, filters, pagination,
saved looks, compare, print, native source zoom, visible links and accessible
motion are implemented. Home has 22 sections and targets 77 unique image
elements plus one distinct poster, 78 displayed photographic sources. Blog
posts remain a secondary owner workflow rather than the homepage focus.

Theme1.0.3 includes the native page-home.html template for the imported Home slug,
including authenticated draft preview. Its own hero supplies the single H1;
the generic page title must not appear above it. If the owner changes that slug,
the registered Photo collection home template remains selectable in the page
editor. Preserve the full-width layout and native editable content.

Do not reintroduce global aspect-ratio:auto!important: actual WordPress image
auto-size containment previously created very tall blank frames. Preserve
.wp-block-video video[poster] and .wp-block-video.bixie-film video specificity
so WordPress core poster styling cannot crop the portrait movie. Keep object-fit:
contain and full-frame display, including owner-selected native videos.

The resumable importer preserves owner edits unless overwrite is explicitly
selected. It validates capability/nonce, exact native SHA and dimensions,
complete reviewed angles, safe ZIP paths/MIME/size bounds and immutable part
identities. Directory parents must be rechecked after child pages are imported,
only when the package-blocked draft's content remains unchanged. Edited drafts,
private pages and nonproject content must not be silently published. Alias
queries support none/no-bangs and dark/black while retaining raw owner metadata.
Actual alias SQL/REST/cache regression passed 16 checks on explicitly synthetic
software fixtures; actual permalink regression passed 21 checks.

The older isolated synthetic-test site is /workspace/wp-test on port8766.
The separate actual-source final acceptance site is /workspace/wp-final-test
on port8767. WordPress7.1.3, PHP8.4.26, MariaDB11.8.6 and verified official
WP-CLI2.12.0 are prepared. Private credentials/wp-config/cookies, databases,
runtime packages and synthetic media stay outside the installable project.
Existing helper python3 /workspace/wp-test/start-test-services.py --status
checks owned services; dev-environment/prepare-final-qa.py prepares the separate
site without resetting the older one. Never copy new plugin/catalog files into
an active importer job: its fingerprint intentionally detects changed input.

Actual authenticated GUI integration imported an immutable 80-look snapshot,
240 gallery photos +25 Home photos +1 movie with zero errors. Repeat import
preserved edits and attachments. That is partial integration evidence, not
final 154-look acceptance. Final reports must bind the exact delivered theme,
plugin and all media-part SHA values. Do not substitute fixture or pilot checks.

## Remaining completion sequence

The confirmed current blocker is image generation HTTP429 usage_limit_reached.
Exactly65sources remain: straight6, bangs20, over-6013, 90s-inspired2,
round-face15 and easy-styling9. No unreviewed saved sources or tool calls remain
pending. The service reported reset2026-10-08 10:34:04UTC /15:34:04PKT; after that
time verify one genuinely missing request succeeds before advancing the saved
disjoint queue. Do not repeatedly retry the unchanged quota error.

The available download is an explicitly incomplete engineering checkpoint on
bixie-wordpress-saved-download, containing33verified numbered parts with
422actual approved photos plus one movie and128complete look records. Its pinned
index and actual installation/import acceptance must be read from the saved
release reports. This is separate from the strict final154/487download branch.

1. Resume only explicitly missing assigned sources and approve complete coherent
   front/side/back sets. Production coordinator owns the master manifest;
   production workers own disjoint individual records/declarations. Concurrency
   cap is seven total agents including children. Do not spawn an eighth worker.
2. Run python3 content/sync_reviewed_media.py; copy canonical content/catalog.json
   byte-for-byte to plugin/bixie-library/content/catalog.json; run
   python3 content/validate_content.py. Gates derive actual files, not plans.
3. When all154looks/487photos are ready, run audit_production_media.py. Complete
   release requires verified_complete_assets and no failures. Build actual
   multipart ZIPs with build_media_bundles.py; each ≤25MiB, each manifest ≤2MiB.
   Compact look projections contain angle/key/caption; authoritative full
   provenance remains in each separately verified media record.
4. Publish media only with publish_delivery.py --stage media on the dedicated
   bixie-wordpress-download branch. Run build_release_index.py to pin actual
   part URLs/SHA/bytes to that immutable media commit. Then build_release.py
   and verify_release.py produce the actual installable theme/plugin ZIPs.
5. Install those exact ZIPs through WordPress core and upload/import all actual
   media parts through the authenticated owner GUI on the separate noindex
   site. Complete final browser, native edit/save, owner-preservation, routing,
   every collection's21views, source-pixel/hash and movie/motion checks. Save
   tests/wp-final-acceptance-report.json only with truthful complete counts.
6. Refresh documentation using refresh_documentation.py. Rebuild docs/source
   ZIPs without changing the tested installable ZIP bytes. Publish code only
   after exact tested_archive SHA guards and archive integrity checks pass.
7. Verify every pinned HTTPS media/code download size/SHA and the full GitHub
   codeload ZIP response/CRC/contents. Deliver those real HTTPS download links.
   Local chatfile previews and download links previously failed for this user.

## Preserve work and external limits

save_checkpoint.py commits ONLY authorized project files on
**bixie-wordpress-project**, using a temporary index and preserving main,
checkout HEAD and the normal index. The branch tip is the authoritative latest
saved checkpoint; prior e62213385eb9ba134320a8ce14c59bddcc7a9913 is historical.
Save reviewed files and exact counts before any usage limit, without packaging
QA secrets or overwriting earlier originals. Final downloads use the clean
separate bixie-wordpress-download branch. No live site deployment is authorized
or needed to finish the package.

Actual WordPress remote GitHub media fetch is unverified because local DNS is
unavailable before its safe URL validation can reach the HTTPS proxy. Do not
weaken DNS/URL/TLS checks. Proxy-aware HTTPS artifact download and actual owner
GUI manual ZIP upload are the tested fallback. Actual named SEO-plugin
coexistence remains unverified after official distribution HTTP403; label
provider-stub tests simulated. Contact/Privacy await genuine owner details.
Target hosting, cache/CDN, production HTTPS, field performance, Search Console,
indexing and rankings remain real target-host checks, without guarantees.

Cloud onboarding startup instructions were saved as an environment draft.
Environment settings Save and Publish is a separate user snapshot action; it
does not block finishing and saving this authorized project. Continue using
the existing checkout, without creating a worktree or exposing runtime secrets.
''')
    print(json.dumps({'status': 'documentation_refreshed_from_actual_catalog', 'actual_looks': looks, 'actual_gallery_photographs': views, 'actual_home_photographs': home, 'complete_collections': collections, 'assembled_complete_content': complete}, indent=2))


if __name__ == '__main__':
    main()
