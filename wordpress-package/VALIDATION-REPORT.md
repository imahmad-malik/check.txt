# Bixie Haircut — validation report

## Release status and evidence boundary

This is an actual WordPress engineering package with a growing reviewed original library, not a completed 154-look launch. Theme/plugin installation and real database import were exercised on isolated local WordPress. Most code QA uses clearly labeled synthetic fixtures; those do not count as approved hairstyle media. Real photo/film production and actual remote-original import verification are tracked separately.

The owner accepted available original source resolution: minimum original long edge 1,024 pixels, no upscaling and no native-8K claim. Production continues toward 22 collections, 154 looks, 462 gallery views and 25 Home originals: **487 photos**. Home targets 77 unique images by combining its role originals with canonical fronts. Seven short image-led guides reuse 24 canonical view references, without adding 24 new originals.

Current assembly snapshot, read from the actual manifests/catalog:

| Item | Reviewed master inventory | Canonical content inventory / completion |
|---|---:|---|
| Required Home originals | 25 approved | 25 available; full 77-image Home still depends on gallery completion |
| Complete three-angle looks | 10 | Six included in the current canonical catalog; final refresh required |
| Approved views in complete looks | 30 | 18 included in the current canonical catalog |
| Approved production photos overall | 63 | Includes eight approved individual photos in incomplete sets; not extra complete looks |
| Finished primary collections | 0 of 22 | Seven complete allocated looks/21 views per collection still needed |
| Photo-sequence film | One approved | Actual production import/playback still to verify |

These are a changing production snapshot, not the final delivered archive inventory or a claim of a live public site. The final catalog, plugin media manifest, release index, part manifests and real source/display files must be synchronized and independently counted before final packaging.

The probe measured 1,312 × 1,199. Its PNG and full-aspect WebP are recorded in [media/manifest.json](media/manifest.json); it is nonpublic and skipped by import. Native 8K was not produced or verified. [media/old-source-audit.json](media/old-source-audit.json) records why earlier hairstyle sources fail new covered-clothing/framing requirements. Rejected sources do not fill the new site.

## Executed environment and installation

| Item | Actual check or boundary |
|---|---|
| Runtime | WordPress 7.1.3, PHP 8.4.26, MariaDB 11.8.6; isolated local noindex staging |
| Installation | Actual `Theme_Upgrader` / `Plugin_Upgrader` ZIP install and activation completed |
| Dependency trust | Signed Debian indexes, artifact hashes and official WP-CLI SHA-512 verified; TLS verification retained |
| WP-CLI | Official 2.12.0 build and actual `bixie status` exercised |
| Declared compatibility | WordPress 6.6; theme PHP 8.1, plugin PHP 8.0. Minima not separately tested; use PHP ≥8.1 together |
| Deployment | Not performed; production domain, hosting, HTTPS and owner access not verified |

[tests/wp-runtime-report.json](tests/wp-runtime-report.json) consolidates independent passed code checks and identifies production-media/final-archive checks still open. Executed sources are [tests/wp-install-package.php](tests/wp-install-package.php) and [tests/wp-import-test.php](tests/wp-import-test.php). The runtime report records tested PHP extensions. Credentials, process-environment dumps and test-site configuration do not belong in release archives.

## Import and content validation

The initial media-empty engineering import resumed from cursor 2 in a separate PHP request and completed at 66, creating 42 page records/22 collections without errors and skipping one nonpublic diagnostic probe. That historical test had no imported looks/media; it is not the current production-asset count. Home remained draft with 25 required role keys and film key.

Repeated import created zero duplicate keys and preserved an owner-edited title, body and description. Nonstale concurrent batch locking was exercised and rejected. Replacement was disabled for preservation checks; this does not claim all host interruptions/errors self-heal.

The real WP-CLI import completed 22 batches without errors. [tests/wp-service-restart-report.json](tests/wp-service-restart-report.json) verifies owned-process restart retained database content, image relationships, settings and requirements. [tests/wp-activation-cycle-report.json](tests/wp-activation-cycle-report.json) verifies actual separate-request deactivation (REST route unavailable) and restored activation without changing content/image relationships. Temporary portrait/upload/subscriber/collection fixtures were removed; the original 14 synthetic code looks remain for final plugin checks and must be cleaned before final inventory.

[content/content-validation.json](content/content-validation.json) records 28 passed static catalog checks: route/key uniqueness, 22 collections/seven guides, explicit planning-only briefs, 154 launch set requirements, no fabricated completed media, headings/blocks/links, keyword disposition and guide allocation. Its 440-look/1,320-view expansion is future planning. Its “not verified” list describes the content validator's own scope; assess runtime evidence separately.

[content/guide-photo-allocation.json](content/guide-photo-allocation.json) tracks 24 guide references, including two distinct three-view sets for fine versus thin. The current canonical validator counts three available guide photo references; the remaining allocation needs complete approved records. Unready guides/directories remain drafts. Privacy and Contact await real owner review/details.

[tests/wp-publication-report.json](tests/wp-publication-report.json) records 19 actual WordPress code checks using synthetic media, including guide native galleries, preserved owner edits, revocation/cache invalidation, canonical replacements, cross-primary duplicate-source rejection and ordinary owner-page publication. These tests do not approve current real photos.

## Native blocks and motion

[tests/theme-native-block-report.json](tests/theme-native-block-report.json) reports zero invalid blocks in six serialization cases: empty Home, image-filled fixture, Gallery, Video, header and footer. Home contains one H1 and 22 named sections. The latest harness loads the authenticated core editor package and records no page errors or failed responses. These checks validate markup; they are separate from actual editor save/reload round trips, photographic approval and final-film playback.

[tests/theme-native-controls-fixture-report.json](tests/theme-native-controls-fixture-report.json) and [tests/theme-photo-shelves-fixture-report.json](tests/theme-photo-shelves-fixture-report.json) exercise movement/pause/resume, reduced-motion manual navigation, owner disable/speed/labels, native-button keyboard activation and fixture-video controls. At widths 320, 375, 520, 768, 1,024 and 1,440 pixels, these cases recorded no horizontal page overflow. They do not review the finished 77-photo home or production film.

[tests/plugin-wordpress-editor-report.json](tests/plugin-wordpress-editor-report.json) verifies actual authenticated Gutenberg image replacement, Media Library choice, captions, removal/reinsertion, REST save and all five companion server previews using synthetic sources. The report records no page errors in its successful final flows and notes earlier external admin-resource connection failures separately. Full finished Home/media/navigation/style/revision acceptance still needs final-content review.

The real production film is **11.625 seconds, 1,122 × 1,402, silent H.264**, using approved separate `home-angle-front`, `home-angle-side` and `home-angle-back` originals without cropping, enlargement or a salon-footage claim. Its record in [media/manifest.json](media/manifest.json) documents source review and actual stream/decode checks; actual WordPress production-film playback remains pending. [tests/theme-real-video-report.json](tests/theme-real-video-report.json) is real decoding of a separate synthetic moving-pattern fixture, not this production movie.

[tests/wp-attachment-film-report.json](tests/wp-attachment-film-report.json) records 18 actual WordPress checks of attachment controls, reviewed video/angle links, selected local video replacement, stale IDs/changed bytes and source-review invalidation, with explicitly synthetic photos/movie. This is film/attachment software acceptance, not approval of every production view.

## Browser checks using synthetic records

[tests/wp-browser-report.json](tests/wp-browser-report.json) records browser flows against 14 synthetic looks and 42 labeled test canvases. The original 8K/angle gates stayed active during those earlier checks; the subsequently accepted source requirement is now 1,024 pixels on the original long edge. Canvases exercise dimensions/code behavior rather than generated hairstyle quality. Fixture media/data stay outside installable theme/plugin ZIPs.

Reported flows passed: server gallery/facets, REST filtering/search, pagination, saved reload persistence/Saved page, three-angle detail, two-look compare, three consultation sheets containing nine angle images, and Escape/focus restoration. Desktop/tablet/phone/small-phone cases recorded no page overflow, failed HTTP responses or JavaScript errors. Scoped gallery/detail/saved/compare/print/Saved-page axe scans recorded zero violations. This is automated coverage of those states, not a full accessibility certification or “100% audit.”

Fixture evidence includes [desktop library](tests/wp-screenshots/desktop-synthetic-library.jpg), [phone detail](tests/wp-screenshots/phone-synthetic-detail.jpg), [desktop comparison](tests/wp-screenshots/desktop-synthetic-comparison.jpg) and [synthetic consultation PDF](tests/wp-screenshots/synthetic-consultation.pdf). The PDF demonstrates print rendering with test data, not an approved hairstyle-reference deliverable.

[tests/wp-collection-report.json](tests/wp-collection-report.json) verifies desktop/phone SSR, page-two and AJAX collection results with seven cards/21 painted full-angle photos, matching side/back initial lightbox views and Escape focus. Those are synthetic code images. [tests/wp-navigation-report.json](tests/wp-navigation-report.json) records HTTP 200 for eight native header/footer targets and suppression of draft Privacy/Contact links.

## Media transfer checks

Manual ZIP-part upload/import is implemented. [tests/wp-admin-upload-report.json](tests/wp-admin-upload-report.json) covers authenticated administrator upload, GUI import, no-JavaScript form and authorization with unapproved synthetic media. [tests/wp-bundle-security-report.json](tests/wp-bundle-security-report.json) has 26 actual WordPress adversarial archive/source checks. Both retain a clear fixture boundary.

Trusted HTTPS downloading is implemented with scoped project hosts, retained TLS verification, manifest/part SHA and byte checks, bounded parts and resumable one-part jobs. [tests/wp-download-orchestration-report.json](tests/wp-download-orchestration-report.json) checks the real controller/state/verifier through an explicitly simulated HTTP transport; it is not a live download test.

The first immutable real-media pilot contains four complete looks/12 originals and is about 21.28 MB. HTTPS retrieval at pinned commit `bd79f783…` returned HTTP 200 with matching SHA in the external delivery check. Actual authenticated WordPress download/import of that original-photo pilot is being verified separately; final production index/all-part integration remains open. An empty or older embedded `release-index.json` must be refreshed before the dashboard can offer the intended final downloads.

## SEO and research boundary

Provider detection, accessible source URLs/schema, filter/tool robots handling, pagination canonical coordination and collection-route redirects are implemented engineering provisions, not evidence of indexing or rankings.

Actual HTTP checks recorded in the runtime report verify staging privacy directives as `noindex,nofollow` without contradictory `follow`, and remove draft Privacy/Contact footer links while retaining published destinations. Other final SEO/source tests remain separately scoped.

**Actual named SEO-plugin coexistence is not verified.** WordPress.org API/distribution requests returned HTTP 403 here. Any separately reported detection/provider-hook simulation is not an installation/test of Yoast, Rank Math, AIOSEO or SEOPress. Chosen-plugin source metadata/schema/sitemap behavior remains a target-host check.

[tests/wp-seo-report.json](tests/wp-seo-report.json) verifies real WordPress HTTP schema/canonical/robots and admin schema-setting behavior. External provider signals for Yoast, Rank Math, AIOSEO, SEOPress and the filter hook are explicitly **simulated**; named-plugin installation is still unverified.

Seven Semrush files are partial exports. Estimates, organic positions, feature slots and dates are preserved separately in [content/research/coverage-plan.md](content/research/coverage-plan.md). They establish no current full Google US/Images audit, backlinks, live traffic or universal ranking outcome.

## Preliminary archive verification

[tests/release-archive-report.json](tests/release-archive-report.json) records 23 passed checks for the preliminary ZIP build: checksums/CRC, safe unique paths, one install root per theme/plugin, exclusion of private runtime files and diagnostic/synthetic media from installable ZIPs, honest empty launch counts, and resolving relative documentation links in the source bundle. The full source bundle preserves the canonical theme/plugin/content/tests/media/source-media folders; its single covered resolution probe remains diagnostic. Synthetic screenshots/PDF are evidence only.

This preliminary result is scoped to that build. The final archive check must be rerun after code, documentation and QA evidence settle. [build_release.py](build_release.py) and [verify_release.py](verify_release.py) are included release-source tools; archive checks do not substitute for WordPress behavior or photographic acceptance.

## Outstanding required work

- Complete approved-resolution production/review of all 487 photos. Synthetic tests and approval checkboxes cannot supply photographic completion; native 8K must not be claimed.
- Verify identity/cut/color/fringe/nape consistency, loose fully opaque high-neck clothing, no cleavage/chest lines, full head framing and genuine dimensions across every launch record.
- Synchronize the master/canonical inventories, plugin media manifest, trusted immutable index, matching parts and source/display files. Recount actual approved views/complete looks and verify all file hashes before final release assembly.
- Populate/review the full 77-photo Home, 22 collections, 154 looks and seven guides; verify the existing real photographic film/poster in final WordPress import/playback and browser controls.
- Run finished-content Home/template/navigation/style/revision acceptance and final ZIP installation after assembly. Editor/activation code checks above have passed within their fixture scopes.
- Run actual chosen-SEO-plugin coexistence, metadata/robots/canonical/schema, XML/image sitemap, attachment-page and target-host cache/CDN checks.
- Measure finished-media lab performance and production accessibility, including manual/screen-reader/native-mobile review. No PageSpeed score, field LCP/INP/CLS or blanket security guarantee is claimed.
- Supply genuine owner contact/policy details and verify production domain/HTTPS/hosting; retain deployment authorization before going live.
- Verify final archive inventory/integrity and fixture/secret exclusion when final ZIPs are built; test sources alone do not prove a newly repackaged ZIP matches the tested one.
- Finish real original-photo HTTPS → authenticated dashboard download/import verification, then all-part production integration, resume/owner-edit preservation and final removal of remaining synthetic fixtures without deleting real media.

Software checks and content completion are separate acceptance gates. This report does not claim the full site is finished, all possible issues are absent, indexing is fast or rankings are guaranteed.
