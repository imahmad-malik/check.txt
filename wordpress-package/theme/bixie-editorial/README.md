# Bixie Editorial

This is a WordPress block theme. Install `bixie-editorial.zip` through Appearance → Themes → Add New → Upload Theme, then activate it. The companion Bixie Library plugin supplies the look records, photo-library filters, saved looks, comparison and printable references.

## Edit the site without code

- **Home:** Pages → Home → Edit. List View exposes 22 named sections, with native collection photo shelves. Headings, paragraphs, buttons, photographs, the collection shelves, three-angle gallery and the video are ordinary WordPress blocks. Move a section in List View or change its alignment and spacing in the block settings.
- **Photographs:** select an Image block → Replace → Media Library or Upload. Edit its alt text and caption in the normal controls. Keep the source aspect ratio and crop disabled. Collection covers link to actual photo-collection pages; the three-angle Gallery uses native image enlargement.
- **Video:** select the Video block → Replace. Retain muted playback, inline playback and visible controls when using autoplay. A browser may require a play gesture. The original package film must be identified as a photographic motion study, not recorded salon footage.
- **Navigation and footer:** Appearance → Editor → Design → Patterns → Template parts. The header and footer use native blocks. Change navigation links in the Navigation block.
- **Colours and typography:** Appearance → Editor → Styles. The linen, ink, moss, copper, chalk and stone colours and local font families are available as theme presets. Select individual blocks when you want to adjust just one section.
- **Collections and guides:** Pages → select the page → Edit. The explanatory content is native blocks; the photo-library block retrieves real approved look records. Choose the Photo collection or Hair guide page template as appropriate.
- **Look galleries:** open a Hairstyle Look in the dashboard. Replace its native gallery images and keep the companion record's front, side and back attachment references in sync. The companion plugin documentation explains that workflow.

## Motion and accessibility

The opening photo rail and nine native collection shelves each use one instance of every selected image and slowly move back and forth. They do not clone photographs to fake an endless loop. Each shelf with multiple photos has its own editable pause control. Reduced-motion preferences disable automatic movement and provide manual navigation; offscreen shelves stop moving. Keyboard focus and pointer interaction temporarily stop movement. The galleries return to a complete grid for printing. Native gallery enlargement, video controls, focus indicators and the WordPress responsive navigation remain available.

## Photography and publication

The homepage targets 77 unique image elements and one distinct movie poster, 78 displayed photographic sources: 25 role photographs, 45 canonical look fronts in native photo shelves, and eight further filtered library covers. Selected look IDs are excluded from the interactive library so filters do not repeat a shelf photograph. The homepage expects 25 distinct `home-*` attachment keys from the companion content import. Missing photographs remain empty native Image blocks in the editor; the theme never substitutes rejected legacy images or fabricated public placeholders. The companion publication gate must keep Home in draft until its required approved media and required film are available.

Theme-bundled `assets/images/{key}.webp` files can be used for approved homepage media before import; imported attachment IDs take precedence. A fresh import regenerates the homepage from native block content after the media is imported. Edit the existing Home page after installation; a later explicit content re-import may replace imported page content, so back up owner edits before re-importing.

Motion control labels are native Button blocks. Edit their text in the page editor. Alternate-state labels, global motion, rail speed and automatic video playback are available in the companion plugin settings. To change an Image to a Video, use the block inserter to add a Video block at the same position, select its media, then remove the old Image block in List View. WordPress does not transform every Image directly to Video.

No theme font, script, image or stylesheet requires a third-party CDN. DM Sans, Instrument Serif and Noto Sans Symbols are included under their original OFL licences in `assets/fonts/`.

## Developer integration

- `bixie_editorial_home_pattern()` returns native block content for the imported Home page.
- `bixie_get_package_attachment($key)` resolves imported media when the companion plugin is active.
- `bixie_import_page_content` regenerates Home after the companion importer processes media.
- `bixie/library`, `bixie/finder`, `bixie/saved-looks` and `bixie/look-meta` are companion blocks. The remaining homepage layout, images, text and navigation are native WordPress blocks.
- `templates/front-page.html` renders the Home page's actual post content. It does not hide the homepage inside a shortcode or a fixed PHP template.

The theme itself does not supply a ranking guarantee, invent salon-client records, or treat unavailable native-resolution media as finished work.
