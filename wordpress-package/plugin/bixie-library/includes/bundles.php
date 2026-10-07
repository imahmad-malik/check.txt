<?php
if (!defined('ABSPATH')) { exit; }

function bixie_bundle_limit(): int { return min(25 * MB_IN_BYTES, wp_max_upload_size()); }
function bixie_bundle_parts(): array {
    $parts = (array) get_option('bixie_media_bundle_parts', []); $result = [];
    foreach ($parts as $id => $part) { $result[] = ['bundle_id' => sanitize_key($id), 'status' => $part['status'] ?? 'verified', 'media_count' => absint($part['media_count'] ?? 0), 'looks_count' => absint($part['looks_count'] ?? 0), 'files_count' => absint($part['files_count'] ?? 0), 'uploaded' => $part['uploaded'] ?? '']; }
    return $result;
}
function bixie_bundle_base(): string {
    $upload = wp_upload_dir(); if (!empty($upload['error'])) { throw new RuntimeException('WordPress uploads directory is unavailable.'); }
    return trailingslashit($upload['basedir']) . 'bixie-package/media-parts';
}
function bixie_bundle_relative(string $name): bool {
    return (bool) preg_match('~^(?:source-media|media|video)/(?:[A-Za-z0-9_-]+/)*[A-Za-z0-9_-]+\.(?:png|jpe?g|webp|avif|mp4)$~D', $name);
}
function bixie_is_real_mp4(string $path): bool {
    if (!is_file($path) || filesize($path) < 32) { return false; }
    $stream = fopen($path, 'rb'); if (!$stream) { return false; } $header = fread($stream, 32); fclose($stream);
    if (!is_string($header) || substr($header, 4, 4) !== 'ftyp') { return false; }
    require_once ABSPATH . 'wp-admin/includes/media.php';
    $metadata = wp_read_video_metadata($path);
    return is_array($metadata) && !empty($metadata['width']) && !empty($metadata['height']) && !empty($metadata['length']);
}
function bixie_bundle_remove_stage(string $path): void {
    if (!is_dir($path)) { return; }
    $iterator = new RecursiveIteratorIterator(new RecursiveDirectoryIterator($path, FilesystemIterator::SKIP_DOTS), RecursiveIteratorIterator::CHILD_FIRST);
    foreach ($iterator as $file) { if ($file->isDir() && !$file->isLink()) { rmdir($file->getPathname()); } else { unlink($file->getPathname()); } }
    rmdir($path);
}

/** Verify before publishing a part; extraction never writes outside the project staging directory. */
function bixie_verify_bundle_archive(string $archive_path, ?int $byte_limit = null, ?string $expected_id = null): array {
    if (!class_exists('ZipArchive')) { throw new RuntimeException('The PHP ZIP extension is required for validated media-part uploads.'); }
    if (!is_file($archive_path) || filesize($archive_path) <= 0 || filesize($archive_path) > min(25 * MB_IN_BYTES, $byte_limit ?? bixie_bundle_limit())) { throw new RuntimeException('Media part is empty or exceeds the current upload limit.'); }
    $zip = new ZipArchive(); if ($zip->open($archive_path, ZipArchive::RDONLY) !== true) { throw new RuntimeException('Media part is not a readable ZIP archive.'); }
    $token = wp_generate_uuid4();
    if (!add_option('bixie_media_bundle_lock', ['token' => $token, 'created' => time()], '', false)) { $lock = get_option('bixie_media_bundle_lock'); if (is_array($lock) && time() - (int) ($lock['created'] ?? time()) > 300) { delete_option('bixie_media_bundle_lock'); if (!add_option('bixie_media_bundle_lock', ['token' => $token, 'created' => time()], '', false)) { $zip->close(); throw new RuntimeException('Another media upload is active. Try this part again.'); } } else { $zip->close(); throw new RuntimeException('Another media upload is active. Try this part again.'); } }
    $stage = ''; $committed = false;
    try {
        if ($zip->numFiles > 500) { throw new RuntimeException('Media part contains too many files; split it into smaller parts.'); }
        $names = []; $lower_names = []; $total = 0; $manifest_index = null;
        for ($i = 0; $i < $zip->numFiles; $i++) {
            $stat = $zip->statIndex($i); $name = $stat['name'] ?? ''; $mode = 0;
            if (!$stat || !$name || str_contains($name, "\0") || str_contains($name, '\\') || str_contains($name, '..') || str_starts_with($name, '/') || preg_match('~^[A-Za-z]:~', $name)) { throw new RuntimeException('Unsafe archive path rejected.'); }
            if ($zip->getExternalAttributesIndex($i, $opsys, $attributes)) { $mode = ($attributes >> 16) & 0170000; }
            if ($mode === 0120000) { throw new RuntimeException('Archive links are not allowed.'); }
            if (str_ends_with($name, '/')) { if (!preg_match('~^(?:source-media|media|video)/(?:[A-Za-z0-9_-]+/)*$~D', $name)) { throw new RuntimeException('Unexpected archive directory.'); } continue; }
            if ($name !== 'manifest.json' && !bixie_bundle_relative($name)) { throw new RuntimeException('Only a root manifest and its listed image/MP4 files are allowed.'); }
            if (isset($lower_names[strtolower($name)])) { throw new RuntimeException('Duplicate archive filename rejected.'); } $lower_names[strtolower($name)] = true;
            $size = (int) ($stat['size'] ?? 0); $total += $size;
            if ($size <= 0 || $size > 32 * MB_IN_BYTES || $total > 64 * MB_IN_BYTES || ($name === 'manifest.json' && $size > 2 * MB_IN_BYTES)) { throw new RuntimeException('Archive expansion or file size exceeds the bounded media-part limit.'); }
            $names[$name] = ['index' => $i, 'size' => $size]; if ($name === 'manifest.json') { $manifest_index = $i; }
        }
        if ($manifest_index === null) { throw new RuntimeException('A root manifest.json is required.'); }
        $raw = $zip->getFromIndex($manifest_index); if (!is_string($raw)) { throw new RuntimeException('Cannot read the media-part manifest.'); }
        $manifest = json_decode($raw, true, 64, JSON_THROW_ON_ERROR); $id = $manifest['bundle_id'] ?? '';
        if (!is_string($id) || !preg_match('/^[a-z0-9][a-z0-9-]{0,63}$/D', $id)) { throw new RuntimeException('Media part requires a safe unique bundle_id.'); }
        if ($expected_id !== null && $id !== $expected_id) { throw new RuntimeException('Downloaded media part ID differs from its trusted index.'); }
        $records = $manifest['records'] ?? []; $looks = $manifest['looks'] ?? [];
        if (!is_array($records) || !is_array($looks) || count($records) > 500 || count($looks) > 200 || (!$records && !$looks)) { throw new RuntimeException('Media-part records/looks arrays are invalid or empty.'); }
        $expected = ['manifest.json' => hash('sha256', $raw)]; $known_keys = []; $record_keys = [];
        foreach ((array) get_option('bixie_media_bundle_parts', []) as $part) { if (empty($part['manifest']) || !is_readable($part['manifest'])) { continue; } $known = json_decode((string) file_get_contents($part['manifest']), true); foreach ((array) ($known['records'] ?? []) as $record) { $known_keys[$record['key'] ?? $record['id'] ?? ''] = !empty($record['source_file']) ? ($record['sha256'] ?? '') : ($record['display_sha256'] ?? $record['sha256'] ?? ''); } }
        foreach ($records as $record) {
            if (!is_array($record)) { throw new RuntimeException('Invalid media record.'); } $key = $record['key'] ?? $record['id'] ?? '';
            if (!is_string($key) || !preg_match('/^[a-z0-9][a-z0-9_-]{0,127}$/D', $key) || isset($record_keys[$key])) { throw new RuntimeException('Media asset keys must be safe and unique within each part.'); }
            if (($record['usage'] ?? '') === 'resolution-probe' || !empty($record['planned']) || ($record['status'] ?? '') === 'planned') { throw new RuntimeException('Nonpublic probes and planning records cannot be uploaded as release media.'); }
            $record_keys[$key] = true; $source_hash = !empty($record['source_file']) ? ($record['sha256'] ?? '') : ($record['display_sha256'] ?? $record['sha256'] ?? '');
            if (isset($known_keys[$key]) && !hash_equals(strtolower($known_keys[$key]), strtolower($source_hash))) { throw new RuntimeException('An uploaded asset key already has a different original. Existing media will not be overwritten.'); }
            $known_keys[$key] = $source_hash; $has_file = false;
            foreach (['source_file', 'file'] as $field) {
                if (empty($record[$field])) { continue; } $name = $record[$field]; $hash = $field === 'source_file' ? ($record['sha256'] ?? '') : ($record['display_sha256'] ?? $record['sha256'] ?? '');
                if (!is_string($name) || !bixie_bundle_relative($name) || !is_string($hash) || !preg_match('/^[a-f0-9]{64}$/iD', $hash) || !isset($names[$name])) { throw new RuntimeException('A listed source/derivative or its SHA-256 checksum is missing.'); }
                if (isset($expected[$name]) && $expected[$name] !== strtolower($hash)) { throw new RuntimeException('Conflicting checksums for a listed file.'); } $expected[$name] = strtolower($hash); $has_file = true;
            }
            if (!$has_file) { throw new RuntimeException('Each actual media record must include a source file.'); }
        }
        foreach ($looks as $look) {
            if (!is_array($look) || empty($look['key']) || empty($look['title']) || !is_array($look['images'] ?? null)) { throw new RuntimeException('Actual look records require a key, title and image records.'); }
            $angles = []; $keys = []; foreach ($look['images'] as $image) { $key = $image['key'] ?? $image['id'] ?? ''; if (!isset($known_keys[$key])) { throw new RuntimeException('Look references an asset not supplied by verified media parts. Upload its source part first.'); } $angles[] = $image['angle'] ?? ''; $keys[$key] = true; }
            if (count($keys) < 3 || array_diff(['front','side','back'], $angles)) { throw new RuntimeException('Actual look records require three distinct corresponding front/side/back sources.'); }
        }
        if (array_diff_key($names, $expected)) { throw new RuntimeException('Archive contains files not listed by its manifest.'); }
        $base = bixie_bundle_base(); if (!wp_mkdir_p($base)) { throw new RuntimeException('Cannot create the project media-part directory.'); }
        $parts = (array) get_option('bixie_media_bundle_parts', []); $destination = $base . '/' . $id; $manifest_hash = hash('sha256', $raw); $archive_hash = hash_file('sha256', $archive_path);
        if (is_dir($destination)) { $existing = $destination . '/manifest.json'; if (!is_file($existing) || !hash_equals($manifest_hash, hash_file('sha256', $existing))) { throw new RuntimeException('This bundle_id already exists with different content. Use a new part ID; existing files are preserved.'); } foreach ($expected as $name => $hash) { if (!is_file($destination . '/' . $name) || !hash_equals($hash, hash_file('sha256', $destination . '/' . $name))) { throw new RuntimeException('Previously uploaded part is incomplete or has changed. It was not overwritten.'); } } $parts[$id] = ['manifest' => $existing, 'root' => $destination, 'sha256' => $manifest_hash, 'archive_sha256' => $archive_hash, 'status' => 'verified', 'media_count' => count($records), 'looks_count' => count($looks), 'files_count' => count($names), 'uploaded' => $parts[$id]['uploaded'] ?? gmdate('c')]; update_option('bixie_media_bundle_parts', $parts, false); return ['bundle_id' => $id, 'status' => 'verified', 'media_count' => count($records), 'looks_count' => count($looks), 'files_count' => count($names), 'parts' => bixie_bundle_parts(), 'already_uploaded' => true]; }
        $stage = $base . '/pending-' . wp_generate_uuid4(); if (!wp_mkdir_p($stage)) { throw new RuntimeException('Cannot stage media part.'); }
        foreach ($expected as $name => $hash) {
            $target = $stage . '/' . $name; if (!wp_mkdir_p(dirname($target))) { throw new RuntimeException('Cannot create a source subdirectory.'); }
            $input = $zip->getStream($name); $output = fopen($target, 'xb'); if (!$input || !$output) { if (is_resource($input)) { fclose($input); } if (is_resource($output)) { fclose($output); } throw new RuntimeException('Cannot read/write a staged media file.'); }
            $written = stream_copy_to_stream($input, $output, $names[$name]['size'] + 1); fclose($input); fclose($output);
            if ($written !== $names[$name]['size'] || !hash_equals($hash, hash_file('sha256', $target))) { throw new RuntimeException('A media checksum/size failed; this entire part was rejected.'); }
            if ($name !== 'manifest.json') { $type = wp_check_filetype_and_ext($target, basename($name), ['png' => 'image/png', 'jpg|jpeg' => 'image/jpeg', 'webp' => 'image/webp', 'avif' => 'image/avif', 'mp4' => 'video/mp4']); $video = strtolower(pathinfo($name, PATHINFO_EXTENSION)) === 'mp4'; if (!$type['ext'] || !in_array($type['type'], ['image/png','image/jpeg','image/webp','image/avif','video/mp4'], true) || ($video ? !bixie_is_real_mp4($target) : !wp_getimagesize($target))) { throw new RuntimeException('A listed file is not actually supported readable image/MP4 media.'); } }
        }
        if (!rename($stage, $destination)) { throw new RuntimeException('Cannot commit the verified media part.'); } $committed = true;
        $parts[$id] = ['manifest' => $destination . '/manifest.json', 'root' => $destination, 'sha256' => $manifest_hash, 'archive_sha256' => $archive_hash, 'status' => 'verified', 'media_count' => count($records), 'looks_count' => count($looks), 'files_count' => count($names), 'uploaded' => gmdate('c')]; update_option('bixie_media_bundle_parts', $parts, false);
        return ['bundle_id' => $id, 'status' => 'verified', 'media_count' => count($records), 'looks_count' => count($looks), 'files_count' => count($names), 'parts' => bixie_bundle_parts()];
    } finally { $zip->close(); if ($stage && !$committed) { bixie_bundle_remove_stage($stage); } $lock = get_option('bixie_media_bundle_lock'); if (is_array($lock) && ($lock['token'] ?? '') === $token) { delete_option('bixie_media_bundle_lock'); } }
}

function bixie_bundle_authorize(): void {
    if (!current_user_can('manage_options') || !wp_verify_nonce(sanitize_text_field(wp_unslash($_POST['nonce'] ?? $_POST['_wpnonce'] ?? '')), 'bixie_media_bundles')) { wp_die(esc_html__('Administrator permission and a valid media-part nonce are required.', 'bixie-library'), '', ['response' => 403]); }
}
function bixie_process_bundle_upload(array $file): array {
    if (($file['error'] ?? UPLOAD_ERR_NO_FILE) !== UPLOAD_ERR_OK || empty($file['tmp_name']) || !is_uploaded_file($file['tmp_name']) || strtolower(pathinfo($file['name'] ?? '', PATHINFO_EXTENSION)) !== 'zip') { throw new RuntimeException('A successful authenticated ZIP file upload is required.'); }
    return bixie_verify_bundle_archive($file['tmp_name']);
}
add_action('wp_ajax_bixie_media_bundle_upload', static function(): void { bixie_bundle_authorize(); try { wp_send_json_success(bixie_process_bundle_upload($_FILES['bundle'] ?? [])); } catch (Throwable $error) { wp_send_json_error(['message' => sanitize_text_field($error->getMessage())], 400); } });
add_action('wp_ajax_bixie_media_bundle_status', static function(): void { bixie_bundle_authorize(); wp_send_json_success(['parts' => bixie_bundle_parts()]); });
add_action('admin_post_bixie_media_bundle_upload', static function(): void {
    bixie_bundle_authorize(); $files = $_FILES['bundle'] ?? []; $messages = [];
    if (is_array($files['name'] ?? null)) { $uploads = []; foreach (array_slice($files['name'], 0, 20) as $index => $name) { $uploads[] = ['name' => $name, 'tmp_name' => $files['tmp_name'][$index], 'error' => $files['error'][$index], 'size' => $files['size'][$index]]; } } else { $uploads = [$files]; }
    foreach ($uploads as $file) { try { $part = bixie_process_bundle_upload($file); $messages[] = 'Verified: ' . $part['bundle_id']; } catch (Throwable $error) { $messages[] = 'Rejected: ' . sanitize_text_field($error->getMessage()); } }
    set_transient('bixie_bundle_notice_' . get_current_user_id(), implode(' ', $messages), 120); wp_safe_redirect(admin_url('tools.php?page=bixie-setup#bixie-bundles')); exit;
});

function bixie_render_bundle_admin(): void {
    $notice = get_transient('bixie_bundle_notice_' . get_current_user_id()); if ($notice) { delete_transient('bixie_bundle_notice_' . get_current_user_id()); }
    ?>
    <section id="bixie-bundles"><h2><?php esc_html_e('Upload original media parts', 'bixie-library'); ?></h2><p><?php esc_html_e('Upload verified media ZIP parts separately from the small theme/plugin ZIPs. Parts are kept in the project uploads directory; re-uploading an identical part resumes safely. Existing owner media and other files are never replaced. After all parts are verified, start or resume the content import above.', 'bixie-library'); ?></p>
    <p><?php echo esc_html(sprintf(__('Maximum per part: %s, subject to the hosting upload limit. ZIP parts require the PHP ZIP extension.', 'bixie-library'), size_format(bixie_bundle_limit()))); ?></p>
    <form id="bixie-bundle-form" method="post" enctype="multipart/form-data" action="<?php echo esc_url(admin_url('admin-post.php')); ?>"><input type="hidden" name="action" value="bixie_media_bundle_upload"><?php wp_nonce_field('bixie_media_bundles'); ?><label for="bixie-bundle-files"><?php esc_html_e('Media ZIP parts', 'bixie-library'); ?></label> <input id="bixie-bundle-files" name="bundle[]" type="file" accept=".zip,application/zip" multiple required><button id="bixie-bundle-upload" class="button" type="submit"><?php esc_html_e('Upload and verify parts', 'bixie-library'); ?></button></form>
    <p id="bixie-bundle-status" role="status" aria-live="polite"><?php echo esc_html($notice ?: ''); ?></p><pre id="bixie-bundle-list" style="white-space:pre-wrap"><?php echo esc_html(wp_json_encode(['parts' => bixie_bundle_parts()], JSON_PRETTY_PRINT)); ?></pre></section>
    <?php wp_enqueue_script('bixie-media-bundles', BIXIE_LIBRARY_URL . 'assets/bundles.js', [], BIXIE_LIBRARY_VERSION, true); wp_add_inline_script('bixie-media-bundles', 'window.BixieBundles=' . wp_json_encode(['url' => admin_url('admin-ajax.php'), 'nonce' => wp_create_nonce('bixie_media_bundles'), 'maxBytes' => bixie_bundle_limit()]) . ';', 'before');
}
