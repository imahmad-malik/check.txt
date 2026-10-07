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
