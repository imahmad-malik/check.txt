<?php
/** Read-only acceptance state for the separate final actual-source QA site. */
if (PHP_SAPI !== 'cli' || empty($argv[1])) { exit(2); }
$_SERVER['HTTP_HOST'] = '127.0.0.1:8767';
$_SERVER['SERVER_NAME'] = '127.0.0.1';
$_SERVER['REQUEST_URI'] = '/';
require $argv[1];
if (wp_get_environment_type() !== 'local' || (int) get_option('blog_public') !== 0 || untrailingslashit(home_url('/')) !== 'http://127.0.0.1:8767') { exit(2); }
// Gate inspection may compute source fingerprints; avoid writing that cache.
add_filter('update_post_metadata', static function($check, $id, $key) { return $key === '_bixie_source_identity' ? true : $check; }, 10, 3);
function final_qa_blocks(array $blocks): array {
    $all = [];
    foreach ($blocks as $block) { if ($block['blockName']) { $all[] = $block; } $all = array_merge($all, final_qa_blocks($block['innerBlocks'] ?? [])); }
    return $all;
}
function final_qa_post(WP_Post $post): array {
    $blocks = final_qa_blocks(parse_blocks($post->post_content)); $types = [];
    foreach ($blocks as $block) { $types[$block['blockName']] = ($types[$block['blockName']] ?? 0) + 1; }
    ksort($types);
    return ['id' => $post->ID, 'status' => $post->post_status, 'title' => $post->post_title, 'url' => get_permalink($post), 'editURL' => admin_url('post.php?post=' . $post->ID . '&action=edit'), 'parent' => $post->post_parent, 'contentSHA256' => hash('sha256', $post->post_content), 'nativeBlockTypes' => $types, 'blockCount' => count($blocks), 'unresolvedTokens' => str_contains($post->post_content, '{{media_')];
}
$catalog = Bixie_Importer::load();
$state = ['scope' => 'Separate actual-source local noindex WordPress acceptance; no fixture look or media is imported by this inspector.', 'expectedFinal' => ['looks' => 154, 'photos' => 487, 'films' => 1, 'collections' => 22, 'pages' => 42, 'guides' => 7, 'guideReferences' => 24, 'uniqueHomeImageElements' => 77, 'distinctHomeFilmPoster' => 1, 'visibleUniqueHomePhotosIncludingPoster' => 78], 'catalogCounts' => ['looks' => count($catalog['looks']), 'pages' => count($catalog['pages']), 'collections' => count($catalog['collections']), 'media' => count($catalog['_media'])], 'looks' => [], 'collections' => [], 'attachments' => [], 'pages' => [], 'guides' => [], 'home' => [], 'settings' => [], 'parts' => [], 'duplicateImportKeys' => [], 'preservation' => ['posts' => [], 'settings' => []]];
$expected = [];
foreach ($catalog['_media'] as $record) { $expected[$record['key']] = $record; }
$package_attachments = get_posts(['post_type' => 'attachment', 'post_status' => 'inherit', 'posts_per_page' => -1, 'orderby' => 'ID', 'order' => 'ASC', 'meta_key' => '_bixie_asset_key']);
$photo_count = 0; $film_count = 0; $source_hashes = [];
foreach ($package_attachments as $post) {
    $id = $post->ID; $key = (string) get_post_meta($id, '_bixie_asset_key', true); $source = bixie_original_source_path($id); $display = (string) get_attached_file($id); $film = get_post_mime_type($id) === 'video/mp4';
    $size = !$film && $source && is_file($source) ? wp_getimagesize($source) : false;
    $hash = $source && is_file($source) ? hash_file('sha256', $source) : '';
    $source_hashes[$key] = $hash;
    $state['attachments'][$key] = ['id' => $id, 'parent' => $post->post_parent, 'mime' => get_post_mime_type($id), 'sourceExists' => $source && is_file($source), 'displayExists' => $display && is_file($display), 'nativeSize' => $size ? [$size[0], $size[1]] : null, 'recordedSize' => [(int) get_post_meta($id, '_bixie_source_width', true), (int) get_post_meta($id, '_bixie_source_height', true)], 'sourceSHA256' => $hash, 'expectedSHA256' => $expected[$key]['sha256'] ?? '', 'nativeURL' => bixie_original_source_url($id), 'displayURL' => wp_get_attachment_url($id), 'approved' => (bool) get_post_meta($id, '_bixie_review_approved', true), 'nativeVerified' => (bool) get_post_meta($id, '_bixie_native_verified', true), 'qualified' => $film ? bixie_check_film($id) : (bool) bixie_check_look(0, [['id' => $id, 'angle' => 'reference']])['ids'], 'filmSourceKeys' => $film ? bixie_array_meta($id, '_bixie_film_source_keys') : []];
    if ($film) { $film_count++; } else { $photo_count++; }
}
$posts = get_posts(['post_type' => ['bixie_look', 'page'], 'post_status' => ['publish', 'draft', 'private', 'pending'], 'posts_per_page' => -1, 'orderby' => 'ID', 'order' => 'ASC', 'meta_key' => '_bixie_import_key']);
$seen = []; $published_looks = 0; $published_pages = 0;
foreach ($posts as $post) {
    $key = (string) get_post_meta($post->ID, '_bixie_import_key', true);
    if (isset($seen[$post->post_type . ':' . $key])) { $state['duplicateImportKeys'][] = $post->post_type . ':' . $key; }
    $seen[$post->post_type . ':' . $key] = true;
    $entry = final_qa_post($post);
    $meta = [];
    foreach (['_bixie_import_key', 'bixie_images', 'bixie_primary_collection', '_bixie_content_type', '_bixie_directory_kind', '_bixie_page_photo_sets', '_bixie_minimum_page_photos', '_bixie_collection_slug', '_bixie_is_front_page', '_wp_page_template', '_bixie_indexability', '_bixie_meta_description', '_bixie_seo_title'] as $field) { $meta[$field] = get_post_meta($post->ID, $field, true); }
    $terms = $post->post_type === 'bixie_look' ? wp_get_object_terms($post->ID, 'bixie_collection', ['fields' => 'ids']) : [];
    if (is_wp_error($terms)) { $terms = []; } sort($terms);
    $state['preservation']['posts'][$post->post_type . ':' . $key] = ['id' => $post->ID, 'status' => $post->post_status, 'contentSHA256' => $entry['contentSHA256'], 'metadataSHA256' => hash('sha256', wp_json_encode($meta)), 'terms' => $terms, 'parent' => $post->post_parent];
    if ($post->post_type === 'bixie_look') {
        $entry['primaryCollection'] = $meta['bixie_primary_collection'];
        $entry['images'] = bixie_get_look_images($post->ID);
        $entry['gate'] = bixie_check_look($post->ID);
        $state['looks'][$key] = $entry;
        if ($post->post_status === 'publish') { $published_looks++; }
    } else {
        $entry['type'] = $meta['_bixie_content_type']; $entry['collectionSlug'] = $meta['_bixie_collection_slug'];
        $entry['nativePhotoIDs'] = bixie_native_photo_ids(parse_blocks($post->post_content));
        $state['pages'][$key] = $entry;
        if ($post->post_status === 'publish') { $published_pages++; }
        if ($entry['type'] === 'guide') {
            $entry['referenceSets'] = $meta['_bixie_page_photo_sets']; $entry['minimumPhotos'] = (int) $meta['_bixie_minimum_page_photos']; $entry['gate'] = bixie_check_page_photos($post->ID);
            $state['guides'][$key] = $entry;
        }
        if ($meta['_bixie_is_front_page']) {
            $entry['gate'] = bixie_check_home($post->ID); $entry['photoIDs'] = bixie_home_photo_ids(parse_blocks($post->post_content)); $entry['uniquePhotoIDs'] = array_values(array_unique($entry['photoIDs'])); $entry['filmIDs'] = bixie_home_film_ids(parse_blocks($post->post_content));
            $entry['posterIDs'] = []; $entry['sectionCount'] = 0;
            foreach (final_qa_blocks(parse_blocks($post->post_content)) as $block) {
                if (($block['attrs']['tagName'] ?? '') === 'section' && str_contains($block['attrs']['className'] ?? '', 'bixie-section')) { $entry['sectionCount']++; }
                if ($block['blockName'] === 'core/video') {
                    $tags = new WP_HTML_Tag_Processor($block['innerHTML'] ?? '');
                    if ($tags->next_tag('VIDEO') && $tags->get_attribute('poster')) { $entry['posterIDs'][] = attachment_url_to_postid(html_entity_decode((string) $tags->get_attribute('poster'), ENT_QUOTES | ENT_HTML5, 'UTF-8')); }
                }
            }
            $entry['visiblePhotoIDs'] = array_values(array_unique(array_merge($entry['uniquePhotoIDs'], $entry['posterIDs'])));
            $state['home'] = $entry;
        }
    }
}
foreach ($catalog['collections'] as $collection) {
    $slug = $collection['slug'] ?? $collection['key']; $term = get_term_by('slug', $slug, 'bixie_collection');
    $state['collections'][$slug] = ['gate' => bixie_check_collection($slug), 'pageID' => $term ? (int) get_term_meta($term->term_id, 'bixie_page_id', true) : 0, 'url' => $term ? bixie_get_collection_url($term) : ''];
}
foreach (['blog_public', 'blogname', 'blogdescription', 'show_on_front', 'page_on_front', 'permalink_structure', 'wp_attachment_pages_enabled', 'bixie_motion_enabled', 'bixie_video_autoplay', 'bixie_schema_disabled'] as $key) { $state['settings'][$key] = get_option($key, null); }
$state['preservation']['settings'] = $state['settings'];
foreach ((array) get_option('bixie_media_bundle_parts', []) as $id => $part) { $state['parts'][$id] = ['archive_sha256' => $part['archive_sha256'] ?? '', 'media_count' => $part['media_count'] ?? 0, 'looks_count' => $part['looks_count'] ?? 0, 'status' => $part['status'] ?? '']; }
$state['databaseCounts'] = ['looks' => count($state['looks']), 'publishedLooks' => $published_looks, 'photos' => $photo_count, 'films' => $film_count, 'uniqueSourceSHA256' => count(array_unique($source_hashes)), 'pages' => count($state['pages']), 'publishedPages' => $published_pages, 'collections' => count(array_filter($state['collections'], static fn($c) => $c['pageID'] > 0)), 'readyCollections' => count(array_filter($state['collections'], static fn($c) => $c['gate']['complete'])), 'guides' => count($state['guides']), 'readyGuides' => count(array_filter($state['guides'], static fn($g) => $g['gate']['complete']))];
$state['import'] = Bixie_Importer::status();
echo wp_json_encode($state, JSON_UNESCAPED_SLASHES) . "\n";
