<?php
/** Exact-ID, local-only production Home QA preview helper; never approves media. */
if (PHP_SAPI !== 'cli' || empty($argv[1]) || empty($argv[2])) { exit(2); }
$_SERVER['HTTP_HOST'] = '127.0.0.1:8766';
$_SERVER['SERVER_NAME'] = '127.0.0.1';
$_SERVER['REQUEST_URI'] = '/';
require $argv[1];
if (wp_get_environment_type() !== 'local' || (int) get_option('blog_public') !== 0) { exit(2); }
$mode = $argv[2]; $data = [];
if ($mode === 'inspect') {
    $records = json_decode(file_get_contents($argv[3]), true);
    $data = ['media' => [], 'fixtures' => [], 'pilot' => [], 'home' => [], 'settings' => []];
    foreach ($records as $record) {
        $key = $record['key']; $id = bixie_get_package_attachment($key); $path = $id ? bixie_original_source_path($id) : ''; $video = $id && get_post_mime_type($id) === 'video/mp4';
        $size = $path && is_file($path) && !$video ? wp_getimagesize($path) : false;
        $data['media'][$key] = ['id' => $id, 'sourceExists' => $path && is_file($path), 'sourceSHA256' => $path && is_file($path) ? hash_file('sha256', $path) : '', 'nativeSize' => $size ? [$size[0], $size[1]] : null, 'nativeURL' => $id ? bixie_original_source_url($id) : '', 'displayURL' => $id ? wp_get_attachment_url($id) : '', 'approved' => $id ? (bool) get_post_meta($id, '_bixie_review_approved', true) : false, 'nativeVerified' => $id ? (bool) get_post_meta($id, '_bixie_native_verified', true) : false, 'qualified' => $video ? bixie_check_film($id) : ($id && !empty(bixie_check_look(0, [['id' => $id, 'angle' => 'reference']])['ids'])), 'filmSourceKeys' => $video ? bixie_array_meta($id, '_bixie_film_source_keys') : []];
    }
    $fixture = get_option('bixie_qa_fixture_state', []);
    foreach ($fixture['looks'] ?? [] as $id) { $data['fixtures'][] = ['id' => $id, 'status' => get_post_status($id), 'contentSHA256' => hash('sha256', (string) get_post_field('post_content', $id)), 'images' => bixie_array_meta($id, 'bixie_images')]; }
    foreach (['classic-01', 'short-01', 'long-01', 'layered-01'] as $key) { $id = bixie_find_imported_look($key); $data['pilot'][$key] = ['id' => $id, 'status' => $id ? get_post_status($id) : '', 'contentSHA256' => $id ? hash('sha256', (string) get_post_field('post_content', $id)) : '', 'images' => $id ? bixie_array_meta($id, 'bixie_images') : []]; }
    foreach (get_posts(['post_type' => 'page', 'post_status' => ['draft', 'publish', 'private', 'pending'], 'posts_per_page' => -1, 'meta_key' => '_bixie_is_front_page', 'meta_value' => '1']) as $home) { $data['home'][] = ['id' => $home->ID, 'status' => $home->post_status, 'contentSHA256' => hash('sha256', $home->post_content), 'gate' => bixie_check_home($home->ID)]; }
    foreach (['show_on_front', 'page_on_front', 'blog_public', 'wp_attachment_pages_enabled', 'bixie_motion_enabled', 'bixie_video_autoplay'] as $key) { $data['settings'][$key] = get_option($key, null); }
    $data['parts'] = array_map(static fn($part) => ['bundle_id' => $part['bundle_id'] ?? '', 'archive_sha256' => $part['archive_sha256'] ?? ''], (array) get_option('bixie_media_bundle_parts', []));
    $data['import'] = Bixie_Importer::status();
} elseif ($mode === 'create-preview') {
    if (get_option('bixie_qa_production_home_film_state')) { throw new RuntimeException('Existing exact-ID production QA page needs cleanup first.'); }
    $content = bixie_editorial_home_pattern();
    $id = wp_insert_post(wp_slash(['post_type' => 'page', 'post_status' => 'draft', 'post_title' => 'Isolated production Home and film QA preview', 'post_name' => 'isolated-production-home-film-qa-' . wp_generate_uuid4(), 'post_content' => $content, 'meta_input' => ['_bixie_production_home_film_qa' => 1]]), true);
    if (is_wp_error($id)) { throw new RuntimeException($id->get_error_message()); }
    update_option('bixie_qa_production_home_film_state', ['id' => $id], false);
    $data = ['id' => $id, 'previewURL' => add_query_arg(['page_id' => $id, 'preview' => 'true'], home_url('/')), 'editURL' => admin_url('post.php?post=' . $id . '&action=edit'), 'status' => get_post_status($id), 'nativePhotoIDs' => bixie_home_photo_ids(parse_blocks($content)), 'nativeFilmIDs' => bixie_home_film_ids(parse_blocks($content)), 'fullHomeGate' => bixie_check_home(0, $content)];
} elseif ($mode === 'create-ordinary-preview') {
    $state = get_option('bixie_qa_production_home_film_state', []);
    if (empty($state['id']) || !empty($state['ordinary_id'])) { exit(2); }
    $video = bixie_get_package_attachment('home-motion-film'); $poster = wp_get_attachment_url(bixie_get_package_attachment('home-motion-poster'));
    $content = bixie_editorial_block('video', ['id' => $video, 'controls' => true, 'muted' => true, 'playsInline' => true, 'poster' => $poster, 'preload' => 'metadata'], '<figure class="wp-block-video"><video controls muted poster="' . esc_url($poster) . '" src="' . esc_url(wp_get_attachment_url($video)) . '" playsinline></video></figure>');
    $id = wp_insert_post(wp_slash(['post_type' => 'page', 'post_status' => 'draft', 'post_title' => 'Isolated ordinary native poster video QA', 'post_name' => 'isolated-native-poster-video-qa-' . wp_generate_uuid4(), 'post_content' => $content, 'meta_input' => ['_bixie_production_home_film_qa' => 1]]), true);
    if (is_wp_error($id)) { throw new RuntimeException($id->get_error_message()); }
    $state['ordinary_id'] = $id; update_option('bixie_qa_production_home_film_state', $state, false);
    $data = ['id' => $id, 'status' => get_post_status($id), 'previewURL' => add_query_arg(['page_id' => $id, 'preview' => 'true'], home_url('/'))];
} elseif ($mode === 'preview-inspect') {
    $id = absint(get_option('bixie_qa_production_home_film_state', [])['id'] ?? 0);
    if (!$id || !get_post_meta($id, '_bixie_production_home_film_qa', true)) { exit(2); }
    $content = (string) get_post_field('post_content', $id);
    $data = ['id' => $id, 'status' => get_post_status($id), 'nativePhotoIDs' => bixie_home_photo_ids(parse_blocks($content)), 'nativeFilmIDs' => bixie_home_film_ids(parse_blocks($content)), 'fullHomeGate' => bixie_check_home(0, $content)];
} elseif ($mode === 'cleanup') {
    $state = get_option('bixie_qa_production_home_film_state', []); $removed = [];
    foreach (['id', 'ordinary_id'] as $key) { $id = absint($state[$key] ?? 0); if ($id && get_post_meta($id, '_bixie_production_home_film_qa', true)) { wp_delete_post($id, true); } $removed[$key] = !$id || !get_post($id); }
    delete_option('bixie_qa_production_home_film_state'); $data = ['exactTemporaryPagesRemoved' => !in_array(false, $removed, true), 'removedOwnIDs' => $removed];
} else { exit(2); }
echo wp_json_encode($data, JSON_UNESCAPED_SLASHES) . "\n";
