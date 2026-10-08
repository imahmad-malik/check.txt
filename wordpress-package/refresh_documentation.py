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
    passed = data.get('passed') is True or data.get('status') == 'passed'
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
    state = 'All planned photographic content is assembled; assess final runtime evidence below.' if complete else 'Production is incomplete; this is a saved engineering checkpoint, not the finished launch.'
    date = datetime.now(ZoneInfo('Asia/Karachi')).strftime('%Y-%m-%d %H:%M PKT')
    archive = 'Bixie-WordPress-Package.zip' if complete else 'Bixie-WordPress-Engineering-Package.zip'
    table = '\n'.join('| [' + name + '](tests/' + name + ') | ' + result(name) + ' |' for name in [
        'wp-production-home-film-report.json', 'wp-live-pilot-report.json',
        'wp-permalink-report.json', 'wp-final-environment-report.json',
        'wp-final-integration-report.json', 'wp-final-acceptance-report.json',
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
primary collection. The Home design has22sections and targets77 unique displayed
photos; each completed collection has7looks/21actual separate photographs.
Contact and Privacy await genuine owner details/policy review rather than
invented information.

The accepted sources are generator-native, normally1122×1402 pixels, with actual
dimensions recorded individually. No enlargement or native8K claim is made.
Lossless native WebP sources are verified pixel-for-pixel against retained
generator PNG originals. Source encoding, optimized display files, responsive
derivatives and inspection copies count as one photograph, not separate images.
Visual reviews retain composition/coherence evidence; small review copies are
described honestly. A useful side-facing three-quarter reference is labelled a
side angle rather than falsely described as an exact90-degree profile.

[Actual pixel/hash audit](tests/production-media-report.json),
[content checks](content/validation-report.json) and
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
77-photo Home/22collection browser acceptance must be assessed from the final
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
   verify parts; after all parts verify, choose Start or resume import.
5. Read completion diagnostics: all154looks/22collections/Home/seven guides
   should qualify with the final complete media. Missing or unreviewed sources
   keep affected pages in draft. Part upload progress is not content completion.
6. If you left configuration unchecked, choose Home in Settings → Reading as
   the static front page. Plain and custom permalinks are supported; confirm
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
- [ ] Final actual ZIP/core install and complete real-media import pass on the separate fresh site.
- [ ] Finished Home77uniquephotos/22sections and all collection/detail/guide/tool routes pass final browser checks.
- [ ] Final native owner edit/save/reload, preserved repeated import and accessible motion/saved/compare/print pass.
- [ ] Final part manifests, trusted download index, archive CRC/SHA and pinned HTTPS downloads verify.
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
    print(json.dumps({'status': 'documentation_refreshed_from_actual_catalog', 'actual_looks': looks, 'actual_gallery_photographs': views, 'actual_home_photographs': home, 'complete_collections': collections, 'assembled_complete_content': complete}, indent=2))


if __name__ == '__main__':
    main()
