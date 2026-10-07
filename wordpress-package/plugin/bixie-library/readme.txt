=== Bixie Library ===
Requires at least: 6.6
Tested up to: 7.1.3
Requires PHP: 8.0
Stable tag: 1.0.0
License: GPL-2.0-or-later
License URI: https://www.gnu.org/licenses/gpl-2.0.html

Editable photo-led look records, collection galleries, saved references, comparison, salon sheets and a resumable WordPress package importer.

== Installation ==

1. Upload and activate bixie-library.zip in Plugins > Add New. Install the companion Bixie Editorial theme ZIP in Appearance > Themes.
2. Open Tools > Bixie package setup. When the final code package contains its trusted release index, press Download media and import package. Downloads are streamed and verified one part per request and resume safely. They do not run on activation.
3. For local/offline parts, choose the supplied media ZIP files under Upload original media parts. Parts are verified individually; upload all source parts before any final look-definition part. Then press Start or resume import.
4. Keep Replace existing package-owned copy unchecked to preserve owner edits. Set site title/description and static home only by selecting its explicit option. The importer never silently enables search visibility or replaces contact details.
5. Review the readiness log. Incomplete or unreviewed looks, collection pages, reference guides and the homepage remain drafts. Genuine source dimensions are retained; available generator-original resolution is accepted with a 1024-pixel minimum long edge and no upscaling. There is no native-8K claim.

PHP ZIP is required for validated media parts. WordPress must have a working image editor with WebP support and a writable uploads directory. Local parts are limited to the smaller of the hosting upload limit and 25 MiB. Trusted remote parts are streamed up to 25 MiB; each archive expands to at most 64 MiB. TLS verification remains enabled.

== Native editing ==

Bixie looks use the ordinary block editor plus a Look details sidebar. Replace front, side and back with the actual Media Library images. Named native Image blocks and canonical view relationships synchronize in both directions. Changing a file under the same attachment, including a crop/replacement, clears its previous review/provenance and original-source linkage; re-review before republishing.

Pages and reference galleries use native WordPress blocks. The Photo library block has collection, page-size and Show front, side and back photographs controls. Collection libraries initially display all three matching views; global/home libraries initially display one front cover. Side/back references open the matching selected angle.

Media Library source fields provide review/provenance checks, unique homepage media roles, and a reviewed MP4's three corresponding source selectors. Native resolution is read from the genuine original file. Optimized responsive WebP images are used for normal display; explicit source zoom links to the retained native PNG or equivalent original source. Source pixels, display derivatives and repeated selected-reference views count as one original asset.

Tools > Bixie package setup also provides genuine contact email, motion enabled/speed, video autoplay and alternate motion-control labels. Visitors' reduced-motion preferences are respected.

== Publication and SEO ==

A public look needs separate approved front, side and back originals. Default primary collections require seven complete looks and at least twenty distinct approved original photographs. The homepage also requires its specified covers, current collection coverage, a reviewed genuine multiview film and at least seventy-five distinct photographs without repetition. Reference guides require their current complete look sets. Exact original-file hashes prevent duplicate uploads from inflating photo counts or being reused across different primary collections.

Bixie supplies truthful conditional WebSite, Article, CreativeWork, ImageGallery and Breadcrumb structured data. It uses the actual site brand and WordPress dates, with no invented person credentials, reviews or ratings. Own schema/title/description output is suppressed for detected Yoast, Rank Math, AIOSEO or SEOPress; an admin disable switch supports another provider. Scoped robots/canonical hooks and HTTP noindex headers protect facets, saved tools, search and project attachment pages. Project taxonomy archives redirect to published canonical collection pages; project attachment pages redirect to their published look or actual file. Unrelated owner attachments are untouched.

Known provider filter logic and actual core WordPress output are tested separately. Full real third-party SEO plugin activation/version compatibility remains unverified; review final production output with the chosen provider. WordPress search visibility and core sitemaps do not guarantee indexing or rankings.

== Privacy and retention ==

Saved looks and salon notes stay in the visitor's browser. No tracking, account, email submission or external analytics is added. If persistent browser storage is unavailable, the shortlist lasts only for the visit.

Deactivation/deletion retains owner content, media, original source parts, settings and importer state. Only project cache/temporary locks are removed. Back up the site and retained source directory before changing hosting or deleting media.

== Command-line administration ==

wp bixie import
wp bixie import --configure
wp bixie import --overwrite
wp bixie status

The optional --manifest parameter reads a trusted catalog path for administrator-controlled imports. HTTP controls do not accept arbitrary filesystem paths or download URLs. Ordinary editing and installation require no shortcode or code authoring.

== Media-part format ==

Each ZIP contains root manifest.json with bundle_id, actual records, and optional actual complete looks. Files use listed relative source-media/, media/ or video/ paths; every source/derivative has its SHA-256. Safe original image formats and readable MP4 only. A changed part ID/content or conflicting asset key cannot overwrite existing owner files. Probes, planning briefs, scripts, links, traversal paths, unlisted files and expansion bombs are rejected.

The trusted embedded release-index.json lists only known HTTPS GitHub repository URLs, exact archive sizes and SHA-256 checksums. Empty indexes expose no invented download. Manual media uploads remain the fallback.

== Validation ==

Actual isolated WordPress 7.1.3/PHP 8.4.26/MariaDB 11.8.6 checks exercise installation, native editing, importer preservation, authentication, publication gates and media integrity. Synthetic CODE canvases are explicitly isolated and never included in production media or launch counts. Parent package documentation identifies actual release readiness and any remaining production checks.
