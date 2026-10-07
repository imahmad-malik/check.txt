# Installation

Install **`bixie-editorial.zip`** as the WordPress theme and **`bixie-library.zip`** as its companion plugin. **`Bixie-WordPress-Engineering-Package.zip`** is the source/documentation bundle; `content-plan.zip` contains planning/content material. Neither of those broader archives is a theme upload. No Node/npm or paid page builder is required.

1. Back up a staging WordPress database/uploads and keep staging noindex.
2. Use **Appearance → Themes → Add New → Upload Theme** to install/activate Bixie Editorial.
3. Use **Plugins → Add New → Upload Plugin** to install/activate Bixie Library.
4. Open **Tools → Bixie package setup** as an administrator. Keep replacement unchecked to preserve owner edits.
5. With a populated trusted release index, choose **Download media and import package**. It downloads/checks parts and imports in tracked batches. If the button is unavailable or the host cannot fetch the release, use **Upload original media parts → Upload and verify parts**, then **Start or resume import** after all matching parts verify.
6. Review logs/diagnostics. Current production has 25 approved homepage originals and a growing complete-look library; the master/canonical inventory is a partial assembly snapshot described in the validation report. Missing media still prevents a complete photographic launch.
7. Review Home in **Pages → Home → Edit** and templates/styles in **Appearance → Editor**. Do not publish an unfinished home or empty collection.

Tested versions are WordPress 7.1.3, PHP 8.4.26 and MariaDB 11.8.6. Declared WordPress minimum is 6.6; use PHP 8.1 or newer for the combined theme/plugin. Minimum-version and every-host compatibility have not been verified. Hosting needs writable uploads, supported rewrites, the PHP ZIP extension and image-processing capacity. Manual media parts are limited to the lower of 25 MiB and the host's upload limit; trusted HTTPS downloads also use a 25 MiB part bound.

The owner accepted original native dimensions, with a minimum long edge of 1,024 pixels and no upscaling/native-8K claim. The actual film is an 11.625-second 1,122 × 1,402 silent H.264 photo sequence, not salon footage. Before a final launch installation, the catalog, media manifests, download index and files must be synchronized and all required parts verified; a first four-look pilot is not the complete site.

Source folders are `theme/bixie-editorial/` and `plugin/bixie-library/`. Never copy local `wp-config.php`, credentials, QA databases or synthetic fixture media into production.

See [OWNER-GUIDE.md](OWNER-GUIDE.md), [VALIDATION-REPORT.md](VALIDATION-REPORT.md) and [LAUNCH-CHECKLIST.md](LAUNCH-CHECKLIST.md) for workflows, evidence and remaining launch work.
