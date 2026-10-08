# Install the Bixie WordPress package

Current state: Production is incomplete; this is a saved engineering checkpoint, not the finished launch. Image generation hit the daily quota: 65 source photographs remain. The recorded reset is 2026-10-08 10:34:04 UTC /15:34:04 Pakistan time. Existing approved sources are retained; incomplete looks and Home remain draft. Actual inventory:128looks/384galleryphotos,
25Homephotos, 16/22complete collections.

The download contains **bixie-editorial.zip** (installable theme),
**bixie-library.zip** (installable companion plugin), verified media ZIP parts,
documentation and **Bixie-WordPress-Engineering-Package.zip** (source/docs bundle). Extract the overall
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
   verify parts; after all parts verify, choose Start or resume import. If browser
   JavaScript is disabled, upload one numbered part at a time in ascending order
   to respect the host's request-size and file-count limits.
5. Read completion diagnostics: all154looks/22collections/Home/seven guides
   should qualify with the final complete media. Missing or unreviewed sources
   keep affected pages in draft. Part upload progress is not content completion.
6. Once Home qualifies and is published, choose it in Settings → Reading as
   the static front page if you left configuration unchecked. In an incomplete
   snapshot Home remains draft; inspect its authenticated editor Preview while
   preserving that gate. Plain and custom permalinks are supported; confirm
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
