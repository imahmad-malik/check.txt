# Bixie Haircut — validation report

## Release status and evidence boundary

This is an actual WordPress engineering package, not a completed photographic launch. Theme/plugin installation and real database import were exercised on isolated local WordPress. Browser checks use clearly labeled synthetic code fixtures. Those are not hairstyle photography, native-8K hairstyle evidence, approved launch content or release media.

**At this documentation update, approved launch photographs: 0; public launch looks: 0.** Planned scope is 22 collections, 154 complete looks, 462 gallery views and 25 separate homepage images: 487 image requests. Home targets 77 unique photos using those roles and canonical fronts. Seven drafted short image-led guides allocate 24 canonical view references without 24 extra originals. The owner has accepted available original source resolution; new approved photo production is now authorized and in progress. The configured minimum original long edge is 1,024 pixels. Update delivered counts only from reviewed actual records.

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

[tests/wp-runtime-report.json](tests/wp-runtime-report.json) consolidates the executed runtime/install/import/CLI evidence and explicitly lists final checks still in progress. Executed sources are [tests/wp-install-package.php](tests/wp-install-package.php) and [tests/wp-import-test.php](tests/wp-import-test.php). The runtime report records tested PHP extensions. Credentials, process-environment dumps and test-site configuration do not belong in release archives.

## Import and content validation

Import resumed from cursor 2 in a separate PHP request and completed at 66. It created 42 package page records and 22 collection definitions, with zero looks/media and zero errors; one nonpublic diagnostic probe was skipped. Home remained draft with 25 required role keys and required film key. These are readiness safeguards, not completed-image counts.

Repeated import created zero duplicate keys and preserved an owner-edited title, body and description. Nonstale concurrent batch locking was exercised and rejected. Replacement was disabled for preservation checks; this does not claim all host interruptions/errors self-heal.

The real WP-CLI `bixie import` command also completed 22 batches with zero errors. The owned service startup/restart/start sequence retained its database; post-import data-preservation restart and final fixture cleanup are separately pending in the current runtime report.

[content/content-validation.json](content/content-validation.json) records 28 passed static catalog checks: route/key uniqueness, 22 collections/seven guides, explicit planning-only briefs, 154 launch set requirements, no fabricated completed media, headings/blocks/links, keyword disposition and guide allocation. Its 440-look/1,320-view expansion is future planning. Its “not verified” list describes the content validator's own scope; assess runtime evidence separately.

[content/guide-photo-allocation.json](content/guide-photo-allocation.json) tracks 24 required guide references, including two distinct three-view sets for fine versus thin. Those approved photos are not delivered. Guides remain drafts; Looks/Collections/Guides directories also require usable published content. Privacy and Contact await real owner review/details.

## Native blocks and motion

[tests/theme-native-block-report.json](tests/theme-native-block-report.json) reports zero invalid blocks in six serialization cases: empty Home, image-filled fixture, Gallery, Video, header and footer. Home contains one H1 and 22 named sections. The latest harness loads the authenticated core editor package and records no page errors or failed responses. These checks validate markup; they are separate from actual editor save/reload round trips, photographic approval and final-film playback.

[tests/theme-native-controls-fixture-report.json](tests/theme-native-controls-fixture-report.json) and [tests/theme-photo-shelves-fixture-report.json](tests/theme-photo-shelves-fixture-report.json) exercise movement/pause/resume, reduced-motion manual navigation, owner disable/speed/labels, native-button keyboard activation and fixture-video controls. At widths 320, 375, 520, 768, 1,024 and 1,440 pixels, these cases recorded no horizontal page overflow. They do not review the finished 77-photo home or production film.

## Browser checks using synthetic records

[tests/wp-browser-report.json](tests/wp-browser-report.json) records browser flows against 14 synthetic looks and 42 labeled test canvases. The original 8K/angle gates stayed active during those earlier checks; the subsequently accepted source requirement is now 1,024 pixels on the original long edge. Canvases exercise dimensions/code behavior rather than generated hairstyle quality. Fixture media/data stay outside installable theme/plugin ZIPs.

Reported flows passed: server gallery/facets, REST filtering/search, pagination, saved reload persistence/Saved page, three-angle detail, two-look compare, three consultation sheets containing nine angle images, and Escape/focus restoration. Desktop/tablet/phone/small-phone cases recorded no page overflow, failed HTTP responses or JavaScript errors. Scoped gallery/detail/saved/compare/print/Saved-page axe scans recorded zero violations. This is automated coverage of those states, not a full accessibility certification or “100% audit.”

Fixture evidence includes [desktop library](tests/wp-screenshots/desktop-synthetic-library.jpg), [phone detail](tests/wp-screenshots/phone-synthetic-detail.jpg), [desktop comparison](tests/wp-screenshots/desktop-synthetic-comparison.jpg) and [synthetic consultation PDF](tests/wp-screenshots/synthetic-consultation.pdf). The PDF demonstrates print rendering with test data, not an approved hairstyle-reference deliverable.

## SEO and research boundary

Provider detection, accessible source URLs/schema, filter/tool robots handling, pagination canonical coordination and collection-route redirects are implemented engineering provisions, not evidence of indexing or rankings.

Actual HTTP checks recorded in the runtime report verify staging privacy directives as `noindex,nofollow` without contradictory `follow`, and remove draft Privacy/Contact footer links while retaining published destinations. Other final SEO/source tests remain separately scoped.

**Actual named SEO-plugin coexistence is not verified.** WordPress.org API/distribution requests returned HTTP 403 here. Any separately reported detection/provider-hook simulation is not an installation/test of Yoast, Rank Math, AIOSEO or SEOPress. Chosen-plugin source metadata/schema/sitemap behavior remains a target-host check.

Seven Semrush files are partial exports. Estimates, organic positions, feature slots and dates are preserved separately in [content/research/coverage-plan.md](content/research/coverage-plan.md). They establish no current full Google US/Images audit, backlinks, live traffic or universal ranking outcome.

## Preliminary archive verification

[tests/release-archive-report.json](tests/release-archive-report.json) records 23 passed checks for the preliminary ZIP build: checksums/CRC, safe unique paths, one install root per theme/plugin, exclusion of private runtime files and diagnostic/synthetic media from installable ZIPs, honest empty launch counts, and resolving relative documentation links in the source bundle. The full source bundle preserves the canonical theme/plugin/content/tests/media/source-media folders; its single covered resolution probe remains diagnostic. Synthetic screenshots/PDF are evidence only.

This preliminary result is scoped to that build. The final archive check must be rerun after code, documentation and QA evidence settle. [build_release.py](build_release.py) and [verify_release.py](verify_release.py) are included release-source tools; archive checks do not substitute for WordPress behavior or photographic acceptance.

## Outstanding required work

- Continue approved-resolution production and review of 487 real image assets. Synthetic tests and approval checkboxes cannot supply photographic completion; native 8K must not be claimed.
- Verify identity/cut/color/fringe/nape consistency, loose fully opaque high-neck clothing, no cleavage/chest lines, full head framing and genuine dimensions across every launch record.
- Populate/review the actual 77-photo Home, 22 collections, 154 looks and seven image-led guides; produce/verify the required multiview photographic film/poster.
- Complete authenticated WordPress editor-to-front-end text/media/metadata/revision/template/navigation/style tests and plugin deactivation/reactivation on the final bundle. These remain in progress until final evidence is recorded.
- Run actual chosen-SEO-plugin coexistence, metadata/robots/canonical/schema, XML/image sitemap, attachment-page and target-host cache/CDN checks.
- Measure finished-media lab performance and production accessibility, including manual/screen-reader/native-mobile review. No PageSpeed score, field LCP/INP/CLS or blanket security guarantee is claimed.
- Supply genuine owner contact/policy details and verify production domain/HTTPS/hosting; retain deployment authorization before going live.
- Verify final archive inventory/integrity and fixture/secret exclusion when final ZIPs are built; test sources alone do not prove a newly repackaged ZIP matches the tested one.
- Finish and test the administrator-only media ZIP-part workflow: capability/nonce checks, bundle/part manifests, SHA verification, safe scoped paths, size bounds and resumable imports. Implementation is in progress; no completed media-upload claim is made here.

Software checks and content completion are separate acceptance gates. This report does not claim the full site is finished, all possible issues are absent, indexing is fast or rankings are guaranteed.
