# Installation

Install **`bixie-editorial.zip`** as the WordPress theme and **`bixie-library.zip`** as its companion plugin. **`Bixie-WordPress-Engineering-Package.zip`** is the source/documentation bundle; `content-plan.zip` contains planning/content material. Neither of those broader archives is a theme upload. No Node/npm or paid page builder is required.

1. Back up a staging WordPress database/uploads and keep staging noindex.
2. Use **Appearance → Themes → Add New → Upload Theme** to install/activate Bixie Editorial.
3. Use **Plugins → Add New → Upload Plugin** to install/activate Bixie Library.
4. Open **Tools → Bixie package setup** as an administrator and select **Start or resume import**. Keep replacement unchecked to preserve owner edits.
5. Review the log/diagnostics. Import supplies editable definitions; missing approved media keeps the photographic launch incomplete. This delivery contains zero approved launch photos/looks.
6. Review Home in **Pages → Home → Edit** and templates/styles in **Appearance → Editor**. Do not publish an unfinished photographic home or empty collection.

Tested versions are WordPress 7.1.3, PHP 8.4.26 and MariaDB 11.8.6. Declared WordPress minimum is 6.6; use PHP 8.1 or newer for the combined theme/plugin. Minimum-version and every-host compatibility have not been verified. Hosting needs writable uploads, supported rewrites and sufficient image-processing capacity for future large originals.

Source folders are `theme/bixie-editorial/` and `plugin/bixie-library/`. Never copy local `wp-config.php`, credentials, QA databases or synthetic fixture media into production.

See [OWNER-GUIDE.md](OWNER-GUIDE.md), [VALIDATION-REPORT.md](VALIDATION-REPORT.md) and [LAUNCH-CHECKLIST.md](LAUNCH-CHECKLIST.md) for workflows, evidence and remaining launch work.
