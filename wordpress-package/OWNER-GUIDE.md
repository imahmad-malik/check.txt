# Bixie Haircut — owner guide

## Read this before installation

This is an installable WordPress engineering package with an editable block theme, companion plugin, written page content and a planned photograph catalog. **The complete photographic site is unfinished: zero approved launch photographs and zero public launch looks are delivered.** Installing the software does not supply the missing images or make the homepage ready to publish.

The production plan is 22 image-led collections, seven complete looks per collection, three separate front/side/back photographs per look, and 25 additional homepage photographs: **154 looks, 462 gallery photographs and 25 homepage photographs, or 487 planned image requests**. The long homepage targets 77 distinct photos by combining its 25 role photos with 44 canonical fronts in photo shelves and eight other library covers. Seven concise image-led guides reference 24 planned gallery views; these references do not add 24 new originals. Planning numbers are separate from delivered assets.

The owner has accepted the available original source resolution, and **new photo production is in progress**. The configured minimum original long edge is now 1,024 pixels; record each source's actual dimensions. The generator's earlier **1,312 × 1,199** probe remains diagnostic and is skipped by import. Native 8K was not produced or verified and must not be claimed. Earlier rejected photos are not substituted. The 487-photo plan is not a claim that 487 photos are delivered.

Read [VALIDATION-REPORT.md](VALIDATION-REPORT.md) for executed checks and unresolved verification, and [LAUNCH-CHECKLIST.md](LAUNCH-CHECKLIST.md) before publishing.

## Install and import

Use a backed-up staging WordPress site. Tested runtime versions are WordPress 7.1.3, PHP 8.4.26 and MariaDB 11.8.6. The package declares WordPress 6.6 and PHP 8.1 for the theme; the plugin declares PHP 8.0. Use PHP 8.1 or newer for the pair. Those minimum versions were not separately verified by this release's runtime checks. Installation requires no Node/npm or paid page builder.

1. Upload **`bixie-editorial.zip`** in **Appearance → Themes → Add New → Upload Theme**, then activate **Bixie Editorial**.
2. Upload **`bixie-library.zip`** in **Plugins → Add New → Upload Plugin**, then activate **Bixie Library**. Keep the plugin active when changing themes: it owns the look records and browsing tools.
3. Open **Tools → Bixie package setup** as an administrator.
4. Leave **Replace existing package-owned page/look copy and metadata** unchecked to preserve existing edits. Leave the site-configuration checkbox unchecked unless you intend to set the site title/description and the imported publishable home.
5. Select **Start or resume import**. The interface runs small tracked batches; **Pause after this batch** stops after the current batch. Resume from the same screen.
6. Read the final log and diagnostics. “Complete” describes processed import jobs, not publication readiness. Home, unpopulated collections and image-led guides remain drafts while approved photographs are missing. Looks/Collections/Guides directories also require useful published content; Privacy and Contact need owner review.

A normal repeated import identifies existing package records and preserves owner edits. The explicit replacement checkbox permits replacement of package-owned copy/metadata and collection text; back up first. Existing imported media keys are skipped. The importer does not silently replace search visibility, genuine contact information or unrelated posts. When source files or the catalog change during a running import, start a fresh reconciliation after reviewing the change instead of forcing the stale batch.

The catalog contains 42 page records and 22 collection definitions. Its empty launch-look array is intentional while approved image sets are missing. The separate 440-look expansion briefs are planning material and are not imported as finished looks. Do not repeatedly import the empty catalog expecting it to generate photographs.

## Edit the homepage and site

Open **Pages → Home → Edit**. List View exposes 22 named sections. Ordinary headings, paragraphs, buttons, groups, columns, images, galleries and video are native WordPress blocks. Select a section in List View to move, duplicate or remove it. Edit spacing/alignment in block settings. Use undo and WordPress revisions when recovering an accidental edit.

Select an Image block and choose **Replace → Media Library** or Upload. Keep the full head, hair silhouette and nape visible; preserve the complete source aspect ratio and leave hard cropping off. Change alt text/caption to match the actual photograph. Duplicating a section also duplicates its photo, so replace repeated photographs before publication. The homepage gate detects repeated attachment IDs.

The native Video block accepts uploaded video and a poster; it cannot use an image URL as a movie. To replace an image with video, insert a Video block in that position, select its media and remove the old Image block. Keep visible playback controls. Muted inline autoplay is an owner setting and browsers may require a play gesture. The intended film must be reviewed and supported by distinct approved front/side/back source photographs. A photographic motion sequence is not recorded salon footage.

Edit the header, footer and navigation through **Appearance → Editor → Design → Patterns → Template parts**. Edit global colors and typography through **Appearance → Editor → Styles**. Licensed local fonts are included; the theme does not need an external font CDN. The front-page template renders Home's saved content rather than concealing it inside one large Custom HTML block.

For collections and guides, use **Pages → select the page → Edit**. The writing is native blocks. Where needed, select the **Photo collection** or **Hair guide** template in page settings. A **Bixie Look Library** block retrieves real records; its sidebar accepts a collection slug and looks-per-page setting. Its editor preview uses the last saved WordPress content. Home photo shelves are native image blocks; preserve their chosen look references when editing. Image-led guides need their current approved canonical angle references in the editable gallery before publication.

Regular WordPress posts remain available for additional articles or sponsored work. They do not become the main homepage feed. No newsletter service, invented social account or fake testimonial is supplied.

## Add or revise a look

Open **Bixie looks → Add hairstyle look**. Write a specific title, excerpt and useful notes. Assign a **Look collection** and open **Bixie look details** for texture, length, fringe, color, density, strand, finish, age/face references, primary collection slug, maintenance and styling. Use the same values as the library filters. Fine strand diameter and low density are different concepts.

Open **Bixie look photographs** and choose separate front, side and back attachments. Edit each caption. These angle controls maintain the named native Image blocks and recorded angle relationships; replacing a managed image block also synchronizes its record. Keep the `bixie-front`, `bixie-side` and `bixie-back` block names. Do not relabel a crop or repeated portrait as another angle.

Inspect each source in the Media Library and record **Bixie source review** only after composition/clothing/angle review passes. Record **Original-source provenance** only when verified as a native, non-upscaled original. Neither checkbox creates resolution or guarantees that a defect has been detected. The server also checks original files and dimensions.

Save, then inspect the card, detail, saved, comparison and print flows. Confirm the replacement and captions appear correctly. Removing an angle or withdrawing attachment approval can return the look and dependent image-led pages to draft. The gate requires three separate approved images, readable source files and configured native resolution/provenance.

The primary collection controls which launch allocation counts the photos. Each planned collection needs at least seven complete published looks and 20 distinct qualified photographs; seven complete three-angle sets yield 21. A canonical look may have secondary browsing relationships, but it does not supply a second primary collection's independent photo allocation.

## Required photograph review

Use fictional adults with **loose, fully opaque high-neck clothing**, no exposed neckline, cleavage, visible chest lines, fitted torso outline or torso emphasis. Show the complete head and haircut with breathing room. Reject clipped hair, blur, distorted anatomy, implausible strands, text/watermarks and inconsistent views. Preserve adult identity, cut structure, color, fringe, parting, crown, nape, lighting and background across each set.

Review the actual source, not only a thumbnail. The accepted production requirement uses an original long edge of at least 1,024 pixels. Record dimensions, native provenance and any processing honestly; never describe a lower-resolution or enlarged source as native 8K. Composition approval and coherent separate front/side/back views remain required. Preserve each record's true dimensions when importing or replacing media.

WordPress creates responsive derivatives for browsing. Keep originals for inspection and explicit zoom. Standard views preserve source framing; zoom is a user action and cannot create extra native detail. Source assets, web formats and responsive renditions are not additional looks.

New original media will be distributed in manageable ZIP parts. A capability/nonce-protected dashboard importer with bundle IDs, scoped paths, manifests and SHA verification is being added; use its final verified upload workflow when delivered. Do not assume the present empty content import can ingest arbitrary external ZIPs or that an unverified upload interface is finished. Keep media approval and publication checks separate from successful transfer.

## Motion settings and visitor tools

In **Tools → Bixie package setup**, use **Editorial motion and owner details** to set photograph motion, speed from 5–36 pixels/second, muted film autoplay and alternate-state button labels. Native button text can be edited on the page; settings supply play/next/pause labels when state changes. Reduced-motion preferences disable automatic movement, and offscreen/pointer/focus behavior limits distracting motion. Visitors retain manual controls.

Published complete looks support search, combined filters, reset, sorting, linked pagination and empty states. **Find your bixie** is a texture/length/fringe browsing helper, not a suitability guarantee. Saved looks are local to the visitor's browser; unavailable storage limits persistence and clearing storage removes the shortlist.

Saved/compare tools display two or three selected looks with corresponding angles. The salon sheet uses browser **Print / save as PDF** with the concept disclosure. It is not a separately generated PDF download service. Feature verification uses isolated test fixtures until approved launch photos exist.

## Contact, privacy and search

Set **Genuine owner contact email** in the setup screen and use **Bixie Contact Details** on Contact. The block shows a truthful notice while the address is missing. No address is invented and saving this setting sends no message.

Review Privacy and Disclaimer for the real host, cookies, browser-local saved looks and any later forms, analytics, advertising, embeds or sponsored work. Contact and Privacy begin as drafts. The package does not automatically install analytics or advertising.

Choose one SEO output owner. Bixie detects Yoast, Rank Math, AIOSEO or SEOPress and suppresses its overlapping structured-data and description output. For another schema provider, use **Disable Bixie structured data**. That switch only disables Bixie's schema; coordinate titles, descriptions, canonical/robots and sitemaps separately. Named third-party SEO-plugin coexistence is **not verified** here: distributions were blocked by HTTP 403. Simulated detection is a separate engineering check.

Keep staging noindex. Once the real site is ready, inspect rendered metadata/schema, pagination and actual sitemaps with the chosen SEO/cache plugins. Submit the final sitemap in Search Console. Original images, an exact-match domain and schema do not guarantee fast indexing or ranking above every competitor.

## Updates, backups and recovery

Back up database/uploads before updates or import replacement. Retain source photographs, generation/review manifests and build sources alongside a WordPress content export. Rehearse recovery on staging.

Deactivating or deleting Bixie Library does not delete its posts/media. Reactivation restores its tools; leaving it inactive removes plugin functionality even though content persists. If a route fails, save **Settings → Permalinks** once and check rewrite support. For a missing image, inspect attachment existence, angle assignment, source readability, review/provenance, dimensions and diagnostics before retrying.

For stale edits, check the changed post/attachment and host/plugin/CDN caches. The package cannot guarantee every third-party cache configuration. Use revisions/backups for recovery; rerun default import to reconcile records, or choose explicit replacement only to intentionally restore packaged copy. Do not delete unrelated site data.

Reusable cloud startup instructions may be saved as an environment draft. Review them in Environment settings and select **Save/Publish** there to reuse them for future tasks. That environment-settings step is separate from WordPress publication and does not supply a live site or credentials.
