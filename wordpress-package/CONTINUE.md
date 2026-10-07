# Continue the Bixie Haircut WordPress project

This is a saved development checkpoint, **not the finished launch package**.
Resume the authorized full-site work; do not return another HTML demonstration.

## User decisions that remain in force

- Build the actual installable WordPress block theme, companion plugin, complete
  photo collections, supporting content, importable media and documentation.
- Main subject is **bixie haircut**. Supplied Semrush exports have already been
  reviewed and mapped; preserve canonical intent groups rather than publishing
  thin pages for every spelling. Seven short guides support the photo library;
  ordinary/sponsored posts are secondary and stay off the homepage feed.
- **The user explicitly accepted available generator-native resolution and no
  8K claim. Do not ask this question again.** Minimum native long edge is 1,024;
  current new photographs are commonly 1,122 × 1,402. No upscaling or false labels.
- Every person must wear loose fully opaque high-neck clothing: no cleavage,
  exposed neckline, chest lines, chest contour, sleeveless or torso emphasis.
  Preserve the complete head and hair silhouette. Reject blur and cut-off hair.
- Create separate original front, side and back photographs of the same fictional
  adult and haircut. Crops/renditions are not different views or different looks.
- Target 22 collections, seven complete looks / 21 separate photographs per
  collection: **154 complete looks / 462 view photographs**, plus **25 separate
  homepage photographs**. The extra-long Home targets **77 unique visible photos**
  in 22 sections, with real automatic photo flows and accessible pause controls.
- All 21 collection photographs must be visible on collection pages, rather than
  showing only seven covers. Clicking a view must expose its other real angles.
- Text, media, alignment, navigation, templates and styles must be editable with
  native WordPress controls. Owner edits must survive repeated data imports.
- Finish and provide real downloadable ZIPs. Identify every missing asset and
  unverified check accurately. No guaranteed rankings, indexing or perfect audit.
- The user requested saved progress because a usage limit may arrive, then
  reiterated **continue from this point and deliver the final ZIP**.

## Durable source and media

The repository development branch is `bixie-wordpress-project`.
The project lives in `wordpress-package/`. Existing `main` and the earlier HTML
download branch must be preserved. Do not overwrite unrelated user work.

`media/generation-plan.json` and `content/production-briefs.json` contain exact
stable keys and prompts. Actual native PNGs live in `source-media/`; optimized
WebP images live in `media/`. Individual checkpoints are `media/records/*.json`.
`media/manifest.json` is the aggregate manifest. It separates the diagnostic probe
from approved production photographs and coherent complete look declarations.
Keep PNG originals; lossless native WebP source conversion is permitted only when
decoded pixels match, with separate accurate hashes/provenance. A PNG/WebP pair
still counts as one source photograph.

Use save_checkpoint.py to publish authorized project checkpoints without changing main, the checkout HEAD or the normal Git index. It saves only the package and explicitly named safe delivery files. Check actual files, dimensions and SHA-256 before resuming. **Never regenerate an
already approved existing record simply because an agent/session disappeared.**
Partial fronts/sides are real progress, but a look is incomplete until all three
views pass matching-person/haircut review. See the current media progress files;
no planned count is a delivered count.

The first 12-look pilot is assigned as follows:

- Main producer: classic-01, short-01, long-01, layered-01, choppy-01, curly-01.
- Worker: feathered-01, wavy-01, fine-hair-01, thick-hair-01, over-50-01,
  natural-grey-01.

Generate front first, directly inspect it, then reference its local original for
separate side/back generations. Inspect every result at native size. Bounded
parallel independent calls are authorized; checkpoint after each image/batch.
After the coherent 36-image pilot, continue reviewed batches across the remaining
launch-target keys. Do not stop at the pilot or substitute old rejected photographs.

All25 Home roles are now genuinely generated and reviewed, with final native-lossless source hashes; see media/HOME-PROGRESS.md. The front/side/back Home roles form a reviewed coherent set. build_photo_film.py produces the actual11.625-second1122×1402 silent H.264 sequence without crop/upscale. Its manifest record is media/records/home-motion-film.json, source_asset_keys names all3actual sources; actual WordPress decoded/autoplay check remains. This is truthfully photographic sequence content, not filmed salon footage. Never reuse the old rejected film.

Additional disjoint production assignments: media producer cohort_classic owns classic-02..07 and short-02..07; Home worker now owns long-02..07 and layered-02..07. Do not regenerate their saved partial/approved originals. Coordinator may assign remaining collection ranges while retaining durable individual records and coherent declarations.

## Engineering completed and remaining

Theme: `theme/bixie-editorial/`. Plugin: `plugin/bixie-library/`.
Native templates/blocks, browsing, filters, pagination, saved/compare/print/zoom,
owner settings and the safe tracked importer are implemented. All native blocks
passed actual authenticated WordPress/Gutenberg serialization. A real decoded
synthetic MP4 passed autoplay, pause, reduced-motion and offscreen checks; that
test movie is not a delivered hairstyle film.

The image display bug was reproduced: WordPress auto-size containment plus a
forced `aspect-ratio:auto!important` created 1,500-pixel blank frames. Root removed
that forced theme property; plugin image containment was scoped correctly.
Actual portrait geometry/pixel checks now pass. Preserve that fix.

Multipart media upload is implemented in Tools → Bixie package setup. Actual owner GUI upload, persisted part-list, idempotence, authenticated denial and no-JavaScript fallback passed. ZIP parts
have root `manifest.json` containing `bundle_id`, `records`, and optional actual
`looks`, with relative `source-media/`, `media/` and `video/` paths. Maximum part
size is 25 MiB; authenticated nonce/capability checks, path/hash restrictions,
idempotence and bounded extraction must remain. A catalog-path variable overwrite
found by the GUI import test was fixed and the actual regression passed.

The plugin implements genuine source zoom, optimized responsive display, same-attachment replacement/review invalidation, all-angle collection cards, guide dependency gates and scoped SEO-provider hooks. MP4 GUI review and front/side/back source selectors are available. A trusted embedded remote media index supports streamed bounded HTTPS downloads with exact size/SHA checks and authenticated resumable owner import. The real four-look integration part has been published and independently downloaded successfully; actual WordPress remote download/import remains an affected integration check. Final-source video-block replacement and project-only attachment redirects are receiving focused follow-up tests.

## Reproduce and finish

1. Use the existing checkout; no worktree is needed. Preserve user changes.
2. Validate existing media and resume the reviewed production batches above.
3. Run `python3 content/sync_reviewed_media.py` after complete coherent declarations
   are available, then `python3 content/validate_content.py`. Refresh the plugin's
   embedded catalog with the canonical catalog. Do not invent complete records.
4. Build media parts with `python3 build_media_bundles.py`. Verify actual file
   hashes/dimensions and each archive's size. Media source and display files count
   once, not twice. Keep bulk assets separate from small theme/plugin ZIPs.
5. Run `build_release.py` and `verify_release.py`; the builder now derives actual nonzero catalog counts, separates incomplete engineering from final launch state, verifies canonical/embedded catalog identity, and the archive verifier passed24 meaningful checks. Refresh final counts and required runtime evidence before declaring launch complete. Bulk media remains separate from the code/docs archive; publish parts first and pin the final plugin release-index.json to their real commit so no GitHub file exceeds100MiB.
6. Run real WordPress install/import/editor/media/schema/browser tests against the
   actual final ZIPs and actual photo library, not only synthetic fixtures.
7. Refresh OWNER-GUIDE, INSTALL, VALIDATION-REPORT and LAUNCH-CHECKLIST with precise
   real counts, passed/failed/unverified results. Verify archives and downloads.
8. Publish authorized downloadable delivery ZIPs to the selected GitHub repository
   and test HTTPS response plus downloaded SHA-256. Local chat file links failed
   for this user. Do not send localhost preview links or deploy a live site.

Actual QA runtime is isolated WordPress 7.1.3 / PHP 8.4.26 / MariaDB 11.8.6 with
official verified WP-CLI 2.12.0. Retained local helpers are under `/workspace/wp-test`;
start/status: `python3 /workspace/wp-test/start-test-services.py --status`.
Use `/workspace/wp-test/php` for PHP tests. If unavailable in a new environment,
follow the reproducibility/setup evidence, retaining TLS/signature/checksum trust.
Never print or package QA credentials, cookies, wp-config, environment variables,
database/runtime files or synthetic test media. Disposable secrets were rotated;
keep any replacement configuration local and private.

Actual named SEO-plugin coexistence remains unverified because WordPress.org
distribution requests were blocked. Label any provider-stub tests as simulations.
Production hosting/HTTPS/contact/policy details, live cache/CDN behavior, real-user
Core Web Vitals, indexing and rankings cannot be claimed from local tests.
Cloud startup instructions were saved as an environment draft; user Environment
settings **Save and Publish** is still needed for snapshot publication. This does
not block completing and saving the project code/media in the repository.
