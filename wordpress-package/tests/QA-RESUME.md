# Actual WordPress QA handoff

The isolated retained runtime is `/workspace/wp-test`; the package is
`/workspace/check.txt/wordpress-package`. WordPress 7.1.3, PHP 8.4.26, MariaDB
11.8.6 and official checksum-verified WP-CLI 2.12.0 were exercised. No fixture
image is a launch photograph. Runtime credentials/authentication state remain
private outside the package; never print or copy them into the release.

Start retained services and check real readiness:

```sh
python /workspace/wp-test/start-test-services.py
python /workspace/wp-test/start-test-services.py --status
```

This helper preserves the DB and stops only its exact owned processes when
`--restart` is requested. `wp-service-restart-report.json` verifies post-import
content/image relationships/settings survived restart and repeat startup.

Completed reports, all relative to this directory:

- `wp-runtime-report.json`: consolidated environment, integrity, core ZIP install,
  actual import/resume/idempotence/owner-edit preservation and explicit limits.
- `wp-browser-report.json`: actual library/filter/pagination/saved/detail/compare/
  print flows at 1440, 768, 390 and 320; scoped axe checks, no overflow/JS errors.
- `wp-image-display-report.json`: actual native lazy/auto-size image geometry and
  screenshot pixel tests at all four widths. A real 1500px intrinsic-containment
  regression was fixed. Separate 1048×1310 portrait canvases and the original
  7680×512 panoramic canvases preserve their full original aspect, with painted
  top/bottom edges. The temporary portrait look was removed.
- `wp-admin-upload-report.json`: actual owner GUI multipart uploads, part-list
  persistence, idempotence, nonce403, subscriber403, anonymous denial, separate
  GUI import and native no-JavaScript form fallback. Three explicitly unapproved
  synthetic sources imported; no launch media was created. A catalog-path
  shadowing bug found by this test was fixed.
- `wp-bundle-security-report.json`: plugin agent's 25 actual verifier/import/
  optimized WebP/native PNG/source-edit invalidation and malicious ZIP checks.
- `plugin-wordpress-editor-report.json`: authenticated native Gutenberg/REST
  saves and actual SSR, distinct from static API-contract fixtures.
- `theme-native-block-report.json`: authenticated WordPress block-library SAVE
  validation, six cases with zero invalid blocks/page errors/failed responses.
- `wp-activation-cycle-report.json`: actual deactivation across separate requests
  yields REST404, then reactivation preserves post/image data and restores14
  fixture records. This is not an uninstall data-deletion check.
- `wp-navigation-report.json`: all8 native header/footer targets HTTP200, imported
  draft Privacy/Contact links absent on public render.
- `wp-seo-report.json`: actual HTTP schema/card/angle and pagination canonical
  alignment, facet robots/owner privacy, actual admin schema disable setting.
  Yoast/Rank Math/AIOSEO/SEOPress provider signals were **simulated**; verified
  distributions could not be obtained because official endpoints returned403.

Reproduce the completed focused collection test with `wp-collection-fixture.php create`:

```sh
/workspace/wp-test/php /workspace/check.txt/wordpress-package/tests/wp-collection-fixture.php /workspace/wp-test/wordpress/wp-load.php create
python /workspace/check.txt/wordpress-package/tests/wp-collection-qa.py
```

It checks seven records/21 real image elements on server render, page two and
AJAX facets, original aspect plus painted pixels, side/back-angle initial dialog
selection and Escape focus restoration on desktop/phone. Its first run exposed
a new-page publication bug: missing guide-photo metadata was cast from an empty
string to `['']`, interpreted as an empty referenced look. The plugin owner fixed normalization; ordinary native page publication and
the collection test now pass. Gates remained enabled throughout.
`wp-collection-report.json` records21 server/AJAX images, painted original angles
and correct initial side/back dialog selection on desktop/phone.

The original 14 code looks/42 generated panoramic canvases remain for remaining
agents. The extra portrait/collection page, three unapproved multipart attachments,
verified test part and generated subscriber/private subscriber state have been
removed. Only the original14 fixtures remain. Cleanup commands are safe to
repeat and select only isolated QA data:

```sh
/workspace/wp-test/php /workspace/check.txt/wordpress-package/tests/wp-collection-fixture.php /workspace/wp-test/wordpress/wp-load.php cleanup
/workspace/wp-test/php /workspace/check.txt/wordpress-package/tests/wp-upload-fixtures.php /workspace/wp-test/wordpress/wp-load.php cleanup
/workspace/wp-test/php /workspace/check.txt/wordpress-package/tests/wp-fixtures.php /workspace/wp-test/wordpress/wp-load.php cleanup
```

The upload cleanup removes only `isolated-qa-browser-upload` and its three
`isolated-qa-upload-*` keys, plus its generated subscriber. General fixture
cleanup selects only `_bixie_qa_fixture=1`. Preserve actual production data.

After final source and approved production media changes, rebuild using the
parent-owned `build_release.py`, then test the **actual delivered** theme/plugin
archives via WordPress core:

```sh
/workspace/wp-test/php /workspace/check.txt/wordpress-package/tests/wp-install-package.php /workspace/wp-test/wordpress/wp-load.php /workspace/check.txt/wordpress-release/bixie-editorial.zip /workspace/check.txt/wordpress-release/bixie-library.zip
WP_CLI_CACHE_DIR=/workspace/wp-test/wp-cli-cache /workspace/wp-test/php /workspace/wp-test/wp-cli.phar --allow-root --path=/workspace/wp-test/wordpress bixie import
```

Record final archive hashes/source consistency and refresh appropriate affected
tests. The user accepted actual original resolution (minimum1024 long edge,
no upscaling and no8K claim); strict review/attire/full-hair and three-angle
requirements remain. Actual production picture coverage/import, all487 approved
sources, complete looks/collections, at least75 homepage photos and genuine
motion-source verification remain separate from synthetic code tests. The
homepage must stay draft until its real requirements pass. Final ZIP smoke and
actual photography/film audit cannot be claimed complete yet. No live ranking,
deployed hosting, search indexing or Core Web Vitals check was performed.

## Actual production Home photographs and photographic film

`wp-production-home-film-report.json` is separate from all synthetic film and
owner fixtures. Three immutable parts in `/workspace/check.txt/wordpress-home-release`
were uploaded through the authenticated native WordPress owner GUI. All25 real
Home source photographs and the actual silent11.625-second1122×1402 photographic
sequence qualify independently, with matching original SHA-256/native dimensions
and the film's three distinct reviewed corresponding front/side/back sources.
The movie is a photographic sequence, not filmed salon footage.

Reproduce only while these three immutable Home parts and private retained
authentication state are available; neither private runtime nor cookies belongs
in the release:

```sh
python /workspace/check.txt/wordpress-package/tests/wp-production-home-film-qa.py
```

The test preserves all14 synthetic owner fixtures, the four real pilot looks and
settings. Repeated GUI import uses default preserve mode. Catalog-source missing
diagnostics outside these supplied parts remain separate from the real Home
checks. The current saved Home stays draft; it is not a completed public Home.
Exact temporary ordinary draft preview pages are removed in `finally`, while
all26 imported production attachments are retained.

Actual Gutenberg SAVE/roundtrip validates270 native blocks with no invalid photo
or video blocks, including the film attachment ID. The private native Home-pattern
preview has24 distinct Home image elements and the25th source as native movie
poster. Each of those24 images paints its full source aspect, with top/bottom
screenshot pixels compared against the actual selected source, at1440,768,390
and320 widths. Production movie checks decode actual1122×1402 frames, measure
time advance with muted inline visible autoplay, retain native Space pause after
leaving and returning, pause/resume offscreen autoplay, and honor reduced motion
while allowing explicit play.

The real WordPress run caught core `.wp-block-video [poster]` overriding the
theme's weaker `object-fit:contain` rule and cropping the playing portrait film.
The theme now gives native poster videos sufficient selector specificity, plus
the scoped film selector, without resetting image aspect or overriding owner
inline styles. Actual decoded frame top/bottom pixels and full-frame geometry
pass on desktop and390 phone. A separate ordinary native poster video also
retains its complete frame in an actual720×360 owner inline layout. Native
controls remain enabled and keyboard-operable; only their overlay is suppressed
transiently during decoded-frame screenshot comparison.

This confirms the real Home subset and photographic film, not all487 planned
source photographs, complete collections,75+ actual unique Home photos, final
whole-library ZIP import or real WordPress HTTPS remote fetch. Those remain
separate launch checks. The previous cloud DNS/WordPress safe URL limitation is
unchanged; TLS and URL safety remain enabled.

## Engineering checkpoint QA continuation (2026-10-08)
Fresh runtime is retained at `/workspace/wp-final-test/wordpress`, local noindex port 8767. Do not rerun prepare-final-qa.py during an active import: it copies runtime source. Private credentials/auth/restore backups remain outside the package.

Actual authenticated GUI resumed persisted cursor 357/616 after interrupted browser; all 33 saved parts were already GUI verified and registry SHA checks passed. Active process session 83052 was last observed advancing through 567 with successful HTTP 200 AJAX batches. Report checkpoints are `wp-final-engineering-import-report.json` and contain no request nonces. No DB/source reset or media reupload occurred. Recheck actual report/process before resuming if interrupted again.

Final frozen core artifacts require theme SHA `680b9b95342ec4155dfaf5c0a0019bd2adaaf7d23a8d72138b02ea64c34cfab9` and plugin SHA `8c7953dce0473f03007a1c7311a9bf94c73054add4fcb85c6ee64b79dd97975c`. Do not accept older bdaf/36ec theme or 80e plugin proofs. After stable import/repeat, install current ZIPs through wp-final-install-package.php engineering mode, regenerate the unchanged blocked draft Home with actual default preserving GUI import, then run engineering browser/editor, native owner edit preservation, and wp-engineering-home-qa.py.

Engineering acceptance is strictly 128 looks, 422 photos, one film, 423 unique source identities, 16 ready collections, 42 native pages, seven guides with 24 real references. Home remains draft and incomplete. The 65 missing photos/26 missing looks must not be replaced with fixtures or declared complete. Both wp-engineering-acceptance-report.json and wp-saved-acceptance-report.json must match exact current core and all 33 saved archive SHA values. No full154 acceptance may pass.
