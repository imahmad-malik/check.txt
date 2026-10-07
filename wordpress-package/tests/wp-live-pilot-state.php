<?php
/** Isolated actual production pilot inspector plus temporary attachment HTTP fixtures. */
if (PHP_SAPI !== 'cli' || empty($argv[1]) || empty($argv[2])) { exit(2); }
$_SERVER['HTTP_HOST'] = '127.0.0.1:8766'; $_SERVER['SERVER_NAME'] = '127.0.0.1'; $_SERVER['REQUEST_URI'] = '/'; require $argv[1];
if (wp_get_environment_type() !== 'local' || (int) get_option('blog_public') !== 0) { exit(2); }
$fixture = get_option('bixie_qa_fixture_state', []); $mode = $argv[2]; $data = [];
if ($mode === 'attachment-setup') {
    $look = absint($fixture['looks'][0] ?? 0); $source = bixie_array_meta($look, 'bixie_images')[0]['id'] ?? 0; if (!$source) { exit(2); }
    $folder = wp_upload_dir()['basedir'] . '/isolated-http-attachment-' . wp_generate_uuid4(); wp_mkdir_p($folder);
    $state = ['attachmentSetting' => get_option('wp_attachment_pages_enabled', null), 'folder' => $folder, 'ids' => []]; update_option('wp_attachment_pages_enabled', 1);
    foreach (['project-parent', 'project-native', 'owner', 'owner-import-marker'] as $kind) {
        $path = $folder . '/' . $kind . '.png'; copy(bixie_original_source_path($source), $path);
        $id = wp_insert_attachment(['post_title' => 'ISOLATED HTTP TEST ' . $kind, 'post_mime_type' => 'image/png', 'post_status' => 'inherit', 'meta_input' => ['_bixie_qa_fixture' => 1]], $path, $kind === 'project-parent' ? $look : 0); $state['ids'][] = $id;
        if (str_starts_with($kind, 'project-')) { update_post_meta($id, '_bixie_asset_key', 'isolated-http-' . $kind); }
        if ($kind === 'owner-import-marker') { update_post_meta($id, '_bixie_import_key', 'isolated-old-marker'); }
        $data[$kind] = ['id' => $id, 'url' => get_attachment_link($id), 'expected' => $kind === 'project-parent' ? get_permalink($look) : ($kind === 'project-native' ? bixie_original_source_url($id) : '')];
    }
    update_option('bixie_qa_http_attachment_state', $state, false);
} elseif ($mode === 'attachment-cleanup') {
    $state = get_option('bixie_qa_http_attachment_state', []); foreach ($state['ids'] ?? [] as $id) { wp_delete_attachment($id, true); }
    if (($state['attachmentSetting'] ?? null) === null) { delete_option('wp_attachment_pages_enabled'); } else { update_option('wp_attachment_pages_enabled', $state['attachmentSetting']); }
    if (!empty($state['folder']) && is_dir($state['folder'])) { bixie_bundle_remove_stage($state['folder']); } delete_option('bixie_qa_http_attachment_state'); $data = ['restored' => true];
} elseif ($mode === 'pilot-force-remote') {
    $parts = (array) get_option('bixie_media_bundle_parts', []); update_option('bixie_qa_pilot_registry_backup', $parts['bixie-production-pilot-001'] ?? [], false); unset($parts['bixie-production-pilot-001']); update_option('bixie_media_bundle_parts', $parts, false); $data = ['exactPilotRegistryEntryTemporarilyRemoved' => true, 'sourceFilesUntouched' => true];
} elseif ($mode === 'pilot-restore-part') {
    $saved = get_option('bixie_qa_pilot_registry_backup', []); $parts = (array) get_option('bixie_media_bundle_parts', []); if ($saved && !isset($parts['bixie-production-pilot-001'])) { $parts['bixie-production-pilot-001'] = $saved; update_option('bixie_media_bundle_parts', $parts, false); } delete_option('bixie_qa_pilot_registry_backup'); $data = ['restored' => true];
} elseif ($mode === 'pilot-inspect') {
    $data = ['looks' => [], 'part' => get_option('bixie_media_bundle_parts', [])['bixie-production-pilot-001'] ?? null, 'download' => bixie_download_status(), 'import' => Bixie_Importer::status(), 'fixtureLooks' => [], 'home' => []];
    foreach (['classic-01', 'short-01', 'long-01', 'layered-01', 'wavy-01', 'curly-01'] as $key) {
        $id = bixie_find_imported_look($key); $images = $id ? bixie_get_look_images($id) : []; $entries = [];
        foreach ($images as $image) { $source = bixie_original_source_path($image['id']); $size = is_file($source) ? wp_getimagesize($source) : false; $entries[] = array_merge($image, ['nativePathExists' => is_file($source), 'nativeSha256' => is_file($source) ? hash_file('sha256', $source) : '', 'nativeActualSize' => $size ? [$size[0], $size[1]] : false, 'displayFile' => basename((string) get_attached_file($image['id']))]); }
        $data['looks'][$key] = ['id' => $id, 'status' => $id ? get_post_status($id) : 'missing', 'gate' => $id ? bixie_check_look($id) : [], 'url' => $id ? get_permalink($id) : '', 'images' => $entries];
    }
    foreach ($fixture['looks'] ?? [] as $id) { $data['fixtureLooks'][] = ['id' => $id, 'status' => get_post_status($id), 'contentHash' => hash('sha256', (string) get_post_field('post_content', $id)), 'images' => bixie_array_meta($id, 'bixie_images')]; }
    $homes = get_posts(['post_type' => 'page', 'post_status' => ['publish', 'draft'], 'posts_per_page' => -1, 'meta_key' => '_bixie_is_front_page', 'meta_value' => '1']); foreach ($homes as $home) { $data['home'][] = ['id' => $home->ID, 'status' => $home->post_status, 'gate' => bixie_check_home($home->ID)]; }
} else { exit(2); }
echo wp_json_encode($data, JSON_UNESCAPED_SLASHES) . "\n";
