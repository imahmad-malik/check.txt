<?php
if (!defined('ABSPATH')) { exit; }

final class Bixie_Importer {
    public static function catalog_path(): string { return (string) apply_filters('bixie_library_catalog_path', BIXIE_LIBRARY_DIR . 'content/catalog.json'); }

    public static function load(?string $path = null): array {
        $path = $path ?: self::catalog_path();
        if (!is_readable($path)) { throw new RuntimeException('Packaged content/catalog.json is missing.'); }
        $catalog = json_decode((string) file_get_contents($path), true, 512, JSON_THROW_ON_ERROR);
        if (!is_array($catalog) || !isset($catalog['pages'], $catalog['collections'], $catalog['looks'])) { throw new RuntimeException('Catalog schema requires pages, collections and looks arrays.'); }
        $media = $catalog['media'] ?? [];
        $media_path = BIXIE_LIBRARY_DIR . 'content/media/manifest.json';
        if (is_readable($media_path)) {
            $manifest = json_decode((string) file_get_contents($media_path), true, 512, JSON_THROW_ON_ERROR);
            $media = array_merge($media, (array) ($manifest['records'] ?? $manifest['media'] ?? []));
        }
        foreach ($catalog['looks'] as $look) { foreach ((array) ($look['images'] ?? []) as $image) { if (!empty($image['file']) || !empty($image['source_file'])) { $media[] = $image; } } }
        foreach ((array) get_option('bixie_media_bundle_parts', []) as $part_id => $part) {
            $root = realpath(bixie_bundle_base() . '/' . sanitize_key($part_id)); $part_manifest_path = $root ? $root . '/manifest.json' : '';
            if (!$root || !$part_manifest_path || !is_file($part_manifest_path) || !hash_equals((string) ($part['sha256'] ?? ''), hash_file('sha256', $part_manifest_path))) { throw new RuntimeException('A previously verified media-part manifest is missing or changed.'); }
            $manifest = json_decode((string) file_get_contents($part_manifest_path), true, 64, JSON_THROW_ON_ERROR);
            foreach ((array) ($manifest['records'] ?? []) as $image) { $image['_bundle_root'] = $root; $media[] = $image; }
            foreach ((array) ($manifest['looks'] ?? []) as $look) { $catalog['looks'][] = $look; }
        }
        $look_keys = []; foreach ($catalog['looks'] as $look) { $key = sanitize_text_field($look['key'] ?? ''); if (!$key) { throw new RuntimeException('Actual look record is missing its stable key.'); } $look_keys[$key] = $look; } $catalog['looks'] = array_values($look_keys);
        $unique = [];
        foreach ($media as $image) {
            $key = sanitize_text_field($image['key'] ?? $image['id'] ?? '');
            if ($key && (!empty($image['file']) || !empty($image['source_file']))) { $image['key'] = $key; $unique[$key] = $image; }
        }
        $catalog['_media'] = array_values($unique);
        $catalog['_path'] = $path;
        return $catalog;
    }

    private static function jobs(array $catalog): array {
        $jobs = [];
        foreach (['_media' => 'media', 'collections' => 'collection', 'looks' => 'look'] as $section => $type) { foreach ($catalog[$section] as $index => $entry) { $jobs[] = ['type' => $type, 'index' => $index, 'key' => $entry['key'] ?? $entry['slug'] ?? '']; } }
        $pending = $catalog['pages']; $done = []; $tries = 0;
        while ($pending && $tries++ < 1000) {
            $progress = false;
            foreach ($pending as $index => $page) {
                if (!empty($page['parent_key']) && !isset($done[$page['parent_key']])) { continue; }
                $jobs[] = ['type' => 'page', 'index' => $index, 'key' => $page['key']]; $done[$page['key']] = true; unset($pending[$index]); $progress = true;
            }
            if (!$progress) { throw new RuntimeException('Page hierarchy contains a missing parent key or a cycle.'); }
        }
        $jobs[] = ['type' => 'finish', 'index' => 0, 'key' => 'site'];
        return $jobs;
    }

    public static function start(bool $overwrite = false, bool $configure = false, ?string $path = null): array {
        $catalog = self::load($path); $fingerprint = hash('sha256', wp_json_encode($catalog));
        $state = self::status();
        if (($state['status'] ?? '') === 'running' && ($state['fingerprint'] ?? '') === $fingerprint) { return $state; }
        update_option('bixie_requirements', (array) ($catalog['requirements'] ?? []), false);
        update_option('bixie_required_collections', array_values(array_map(static fn($entry) => sanitize_title($entry['slug'] ?? $entry['key']), $catalog['collections'])), false);
        update_option('bixie_required_home_media', (array) ($catalog['requirements']['required_home_media'] ?? $catalog['required_home_media'] ?? $catalog['site']['required_home_media'] ?? []), false);
        update_option('bixie_required_home_video', (string) ($catalog['requirements']['required_home_video'] ?? $catalog['required_home_video'] ?? $catalog['site']['required_home_video'] ?? ''), false);
        $jobs = self::jobs($catalog);
        $state = ['status' => 'running', 'cursor' => 0, 'total' => count($jobs), 'fingerprint' => $fingerprint, 'path' => $catalog['_path'], 'overwrite' => $overwrite, 'configure' => $configure, 'started' => gmdate('c'), 'counts' => ['media' => 0, 'collections' => 0, 'looks' => 0, 'pages' => 0, 'skipped' => 0, 'errors' => 0], 'log' => [], 'diagnostics' => []];
        update_option('bixie_import_state', $state, false);
        return $state;
    }

    public static function status(): array { return (array) get_option('bixie_import_state', []); }
    private static function log(array &$state, string $level, string $key, string $message): void { $state['log'][] = ['level' => $level, 'key' => sanitize_text_field($key), 'message' => sanitize_text_field($message)]; $state['log'] = array_slice($state['log'], -100); }

    public static function batch(int $size = 3): array {
        $token = wp_generate_uuid4();
        if (!add_option('bixie_import_lock', ['token' => $token, 'created' => time()], '', false)) {
            $lock = get_option('bixie_import_lock');
            if (is_array($lock) && time() - (int) ($lock['created'] ?? time()) > 300) { delete_option('bixie_import_lock'); if (!add_option('bixie_import_lock', ['token' => $token, 'created' => time()], '', false)) { throw new RuntimeException('Another importer batch is active.'); } }
            else { throw new RuntimeException('Another importer batch is active.'); }
        }
        try {
            $state = self::status();
            if (($state['status'] ?? '') !== 'running') { return $state; }
            $catalog = self::load($state['path']);
            if (hash('sha256', wp_json_encode($catalog)) !== $state['fingerprint']) { throw new RuntimeException('Package changed during import. Start a fresh import to safely reconcile the changed manifest.'); }
            $jobs = self::jobs($catalog); $end = min(count($jobs), $state['cursor'] + max(1, min(10, $size)));
            for (; $state['cursor'] < $end; $state['cursor']++) {
                $job = $jobs[$state['cursor']];
                try {
                    if ($job['type'] === 'media') { self::media($catalog['_media'][$job['index']], $state); }
                    elseif ($job['type'] === 'collection') { self::collection($catalog['collections'][$job['index']], $state); }
                    elseif ($job['type'] === 'look') { self::look($catalog['looks'][$job['index']], $state); }
                    elseif ($job['type'] === 'page') { self::page($catalog['pages'][$job['index']], $state); }
                    else { self::finish($catalog, $state); }
                } catch (Throwable $error) { $state['counts']['errors']++; self::log($state, 'error', $job['key'], $error->getMessage()); }
                update_option('bixie_import_state', $state, false);
            }
            if ($state['cursor'] >= count($jobs)) { $state['status'] = 'complete'; $state['finished'] = gmdate('c'); }
            update_option('bixie_import_state', $state, false);
            bixie_invalidate_catalog();
            return $state;
        } finally {
            $lock = get_option('bixie_import_lock'); if (is_array($lock) && ($lock['token'] ?? '') === $token) { delete_option('bixie_import_lock'); }
        }
    }

    private static function existing(string $key, string $type): int {
        $ids = get_posts(['post_type' => $type, 'post_status' => ['publish', 'draft', 'pending', 'private', 'future', 'trash', 'inherit'], 'posts_per_page' => 1, 'fields' => 'ids', 'meta_key' => '_bixie_import_key', 'meta_value' => sanitize_text_field($key)]);
        return $ids ? (int) $ids[0] : 0;
    }

    private static function source_path(string $relative, ?string $bundle_root = null): string {
        if (!$relative || str_contains($relative, '..') || str_contains($relative, '\\') || preg_match('~^[a-z]+:|^/|\x00~i', $relative)) { throw new RuntimeException('Unsafe package media path rejected.'); }
        $base = realpath($bundle_root ?: BIXIE_LIBRARY_DIR . 'content');
        if ($bundle_root) { $parts_base = realpath(bixie_bundle_base()); if (!$base || !$parts_base || !str_starts_with($base, $parts_base . DIRECTORY_SEPARATOR)) { throw new RuntimeException('Media source is outside the validated project part directory.'); } }
        $path = $base ? realpath($base . '/' . $relative) : false;
        if (!$base || !$path || !str_starts_with($path, $base . DIRECTORY_SEPARATOR) || !is_file($path)) { throw new RuntimeException('Packaged source missing: ' . basename($relative)); }
        return $path;
    }

    private static function media(array $image, array &$state): void {
        if (($image['usage'] ?? '') === 'resolution-probe' && empty($image['import_as_public_look'])) { $state['counts']['skipped']++; self::log($state, 'warning', $image['key'], 'Nonpublic resolution probe was not imported into the public WordPress media library.'); return; }
        $key = $image['key']; $existing = bixie_get_package_attachment($key);
        if ($existing) { $state['counts']['skipped']++; return; }
        $relative = $image['source_file'] ?? $image['file']; $path = self::source_path($relative, $image['_bundle_root'] ?? null);
        $expected_hash = !empty($image['source_file']) ? ($image['sha256'] ?? '') : ($image['display_sha256'] ?? $image['sha256'] ?? '');
        $actual_hash = hash_file('sha256', $path);
        if (!$expected_hash || !hash_equals(strtolower($expected_hash), $actual_hash)) { throw new RuntimeException('Source checksum missing or mismatched; media not imported.'); }
        $video = strtolower(pathinfo($path, PATHINFO_EXTENSION)) === 'mp4';
        $size = $video ? [0, 0] : wp_getimagesize($path);
        if (!$size) { throw new RuntimeException('Source is not a readable supported image or MP4.'); }
        $delivery_path = $path;
        if (!$video && !empty($image['source_file']) && !empty($image['file']) && $image['source_file'] !== $image['file']) {
            $delivery_path = self::source_path($image['file'], $image['_bundle_root'] ?? null); $display_hash = (string) ($image['display_sha256'] ?? ''); $display_size = wp_getimagesize($delivery_path);
            if (!$display_hash || !hash_equals(strtolower($display_hash), hash_file('sha256', $delivery_path)) || !$display_size || abs($size[0] / $size[1] - $display_size[0] / $display_size[1]) > 0.01) { throw new RuntimeException('Optimized display checksum or original frame geometry does not match its source.'); }
        }
        $duplicate = get_posts(['post_type' => 'attachment', 'post_status' => 'inherit', 'fields' => 'ids', 'posts_per_page' => 1, 'meta_key' => '_bixie_asset_hash', 'meta_value' => $actual_hash]);
        if ($duplicate) { throw new RuntimeException('A different asset key reuses an already imported original; unique source keys are required.'); }
        require_once ABSPATH . 'wp-admin/includes/file.php'; require_once ABSPATH . 'wp-admin/includes/media.php'; require_once ABSPATH . 'wp-admin/includes/image.php';
        $temp = wp_tempnam(basename($delivery_path));
        if (!$temp || !copy($delivery_path, $temp)) { throw new RuntimeException('Could not prepare image import.'); }
        $id = media_handle_sideload(['name' => basename($delivery_path), 'tmp_name' => $temp], 0, sanitize_text_field($image['caption'] ?? $image['alt'] ?? $key));
        if (is_wp_error($id)) { if (is_file($temp)) { unlink($temp); } throw new RuntimeException($id->get_error_message()); }
        update_post_meta($id, '_bixie_asset_key', $key); update_post_meta($id, '_bixie_import_key', $key); update_post_meta($id, '_bixie_asset_hash', $actual_hash);
        update_post_meta($id, '_wp_attachment_image_alt', sanitize_text_field($image['alt'] ?? ''));
        update_post_meta($id, '_bixie_source_width', $size[0]); update_post_meta($id, '_bixie_source_height', $size[1]);
        if ($delivery_path !== $path) {
            $upload = wp_upload_dir(); $base = realpath($upload['basedir']); $original = realpath($path);
            if (!$base || !$original) { throw new RuntimeException('Cannot retain the original source.'); }
            if (!str_starts_with($original, $base . DIRECTORY_SEPARATOR)) { $folder = $base . '/bixie-package/originals'; if (!wp_mkdir_p($folder)) { throw new RuntimeException('Cannot create retained-originals directory.'); } $retained = $folder . '/' . sanitize_key($key) . '-' . substr($actual_hash, 0, 16) . '.' . strtolower(pathinfo($path, PATHINFO_EXTENSION)); if (is_file($retained) && !hash_equals($actual_hash, hash_file('sha256', $retained))) { throw new RuntimeException('Retained source filename has different content; no file was overwritten.'); } if (!is_file($retained) && !copy($path, $retained)) { throw new RuntimeException('Cannot retain the original source.'); } $original = $retained; }
            update_post_meta($id, '_bixie_original_source_file', $original); update_post_meta($id, '_bixie_original_source_url', trailingslashit($upload['baseurl']) . str_replace(DIRECTORY_SEPARATOR, '/', substr($original, strlen($base) + 1))); update_post_meta($id, '_bixie_delivery_file', get_attached_file($id));
        }
        $approved = !empty($image['approved']) || ($image['review_status'] ?? '') === 'approved' || str_starts_with((string) ($image['review']['release_status'] ?? ''), 'approved');
        update_post_meta($id, '_bixie_review_approved', $approved ? 1 : 0);
        update_post_meta($id, '_bixie_native_verified', (!empty($image['native_original']) || !empty($image['native_8k'])) && empty($image['upscaled']) ? 1 : 0);
        update_post_meta($id, '_bixie_source_review', wp_json_encode($image['review'] ?? []));
        update_post_meta($id, '_bixie_asset_angle', sanitize_key($image['angle'] ?? 'reference'));
        if ($video) {
            $sources = array_unique((array) ($image['source_asset_keys'] ?? [])); $angles = [];
            foreach ($sources as $source_key) { $source_id = bixie_get_package_attachment($source_key); if ($source_id && bixie_check_look(0, [['id' => $source_id, 'angle' => 'reference']])['ids']) { $angles[] = get_post_meta($source_id, '_bixie_asset_angle', true); } }
            $multiview = !empty($image['multiview']) && count($sources) >= 3 && !array_diff(['front', 'side', 'back'], $angles);
            update_post_meta($id, '_bixie_multiview_declared', !empty($image['multiview']) ? 1 : 0); update_post_meta($id, '_bixie_multiview_film', $multiview ? 1 : 0); update_post_meta($id, '_bixie_film_source_keys', $sources);
        }
        $state['counts']['media']++; self::log($state, 'info', $key, 'Original image imported at its actual native dimensions; public use still requires review and publication gates.');
    }

    private static function collection(array $record, array &$state): void {
        $slug = sanitize_title($record['slug'] ?? $record['key']); $term = get_term_by('slug', $slug, 'bixie_collection');
        if (!$term) {
            $result = wp_insert_term(sanitize_text_field($record['name']), 'bixie_collection', ['slug' => $slug, 'description' => sanitize_textarea_field($record['description'] ?? '')]);
            if (is_wp_error($result)) { throw new RuntimeException($result->get_error_message()); }
            $term_id = $result['term_id']; $state['counts']['collections']++;
        } else { $term_id = $term->term_id; $state['counts']['skipped']++; if ($state['overwrite']) { wp_update_term($term_id, 'bixie_collection', ['name' => sanitize_text_field($record['name']), 'description' => sanitize_textarea_field($record['description'] ?? '')]); } }
        update_term_meta($term_id, '_bixie_import_key', sanitize_text_field($record['key']));
    }

    private static function content(string $content): string {
        $content = preg_replace_callback('/\bhref=([\x22\x27])(\/(?!\/)[^\x22\x27]*)\1/i', static fn($match) => 'href=' . $match[1] . esc_url(home_url($match[2])) . $match[1], $content);
        $content = preg_replace_callback('/\x22\{\{media_id:([^}]+)\}\}\x22/', static fn($match) => (string) bixie_get_package_attachment($match[1]), $content);
        $content = preg_replace_callback('/\{\{media_id:([^}]+)\}\}/', static fn($match) => (string) bixie_get_package_attachment($match[1]), $content);
        $content = preg_replace_callback('/\{\{media_url:([^}]+)\}\}/', static function($match) { $id = bixie_get_package_attachment($match[1]); return $id ? esc_url(wp_get_original_image_url($id) ?: wp_get_attachment_url($id)) : ''; }, $content);
        return wp_kses_post($content);
    }

    private static function look(array $record, array &$state): void {
        $key = sanitize_text_field($record['key']); $id = self::existing($key, 'bixie_look'); $images = [];
        foreach ((array) ($record['images'] ?? []) as $image) {
            $asset_key = sanitize_text_field($image['key'] ?? $image['id'] ?? ''); $attachment = bixie_get_package_attachment($asset_key);
            if ($attachment) { $images[] = ['id' => $attachment, 'angle' => sanitize_key($image['angle'] ?? 'reference'), 'caption' => sanitize_text_field($image['caption'] ?? '')]; }
        }
        $primary = sanitize_title($record['primary_collection'] ?? $record['meta']['primary_collection'] ?? $record['collections'][0] ?? '');
        $check = bixie_check_look($id, $images, $primary); $status = ($record['status'] ?? 'publish') === 'publish' && $check['complete'] ? 'publish' : 'draft';
        $new = !$id; $content = self::content((string) ($record['content'] ?? ''));
        if (!has_block('core/gallery', $content) && !has_block('core/image', $content) && $images) {
            $content .= "\n<!-- wp:gallery {\"linkTo\":\"none\",\"imageCrop\":false} -->\n<figure class=\"wp-block-gallery has-nested-images columns-default\">";
            foreach ($images as $image) { $content .= "\n" . serialize_block(bixie_native_image_block($image)); }
            $content .= '</figure><!-- /wp:gallery -->';
        }
        if (!has_block('bixie/look-meta', $content)) { $content .= "\n<!-- wp:bixie/look-meta /-->"; }
        $data = ['post_type' => 'bixie_look', 'post_title' => sanitize_text_field($record['title']), 'post_name' => sanitize_title($record['slug'] ?? $key), 'post_content' => $content, 'post_excerpt' => sanitize_textarea_field($record['excerpt'] ?? ''), 'post_status' => $status, 'menu_order' => absint($record['menu_order'] ?? 0), 'meta_input' => ['_bixie_import_key' => $key, 'bixie_images' => $images, 'bixie_primary_collection' => $primary]];
        if ($new || $state['overwrite']) { if ($id) { $data['ID'] = $id; } $result = wp_insert_post(wp_slash($data), true); if (is_wp_error($result)) { throw new RuntimeException($result->get_error_message()); } $id = $result; $state['counts']['looks']++; }
        else { $state['counts']['skipped']++; if (get_post_meta($id, '_bixie_import_incomplete', true)) { update_post_meta($id, 'bixie_images', $images); if ($check['complete']) { wp_update_post(['ID' => $id, 'post_status' => $status]); } } }
        foreach ((array) ($record['meta'] ?? []) as $field => $value) { if (in_array($field, ['texture', 'length', 'fringe', 'colour', 'density', 'strand', 'finish', 'age_reference', 'face_reference', 'primary_collection', 'maintenance', 'styling', 'ai_concept'], true) && ($new || $state['overwrite'] || get_post_meta($id, 'bixie_' . $field, true) === '')) { update_post_meta($id, 'bixie_' . $field, $field === 'ai_concept' ? rest_sanitize_boolean($value) : sanitize_textarea_field($value)); } }
        if (!empty($record['primary_collection']) && ($new || $state['overwrite'] || !get_post_meta($id, 'bixie_primary_collection', true))) { update_post_meta($id, 'bixie_primary_collection', sanitize_title($record['primary_collection'])); }
        if ($new || $state['overwrite']) { wp_set_object_terms($id, array_map('sanitize_title', (array) ($record['collections'] ?? [])), 'bixie_collection'); if ($images) { set_post_thumbnail($id, $images[0]['id']); } }
        $check = bixie_check_look($id);
        update_post_meta($id, '_bixie_record_complete', $check['complete'] ? '1' : '0'); update_post_meta($id, '_bixie_import_incomplete', $check['complete'] ? 0 : 1); update_post_meta($id, '_bixie_gate_reason', implode(' ', $check['reasons']));
        if (!$check['complete'] && get_post_status($id) === 'publish') { wp_update_post(['ID' => $id, 'post_status' => 'draft']); }
        self::log($state, $check['complete'] ? 'info' : 'warning', $key, $check['complete'] ? 'Complete reviewed look reconciled.' : 'Look remains draft: ' . implode(' ', $check['reasons']));
    }

    private static function reference_content(string $content, array $record): string {
        $sets = (array) ($record['photo_set_requirements'] ?? []); if (!$sets) { return $content; }
        $references = bixie_page_reference_images($sets);
        if ($references['reasons'] || !$references['entries']) { return $content; }
        $gallery = '<!-- wp:gallery {"linkTo":"none","imageCrop":false,"metadata":{"name":"bixie-guide-reference-photos"}} --><figure class="wp-block-gallery has-nested-images columns-default">';
        foreach ($references['entries'] as $entry) { $block = bixie_native_image_block($entry); $block['attrs']['metadata']['name'] = 'bixie-guide-' . sanitize_key($entry['look_key']) . '-' . sanitize_key($entry['angle']); $gallery .= serialize_block($block); }
        $gallery .= '</figure><!-- /wp:gallery -->';
        $blocks = parse_blocks($content); $insert = max(0, min(count($blocks), absint($record['photo_insert_after_block'] ?? 1)));
        array_splice($blocks, $insert, 0, parse_blocks($gallery));
        return serialize_blocks($blocks);
    }

    private static function page(array $record, array &$state): void {
        $key = sanitize_text_field($record['key']); $id = self::existing($key, 'page'); $new = !$id;
        $parent = empty($record['parent_key']) ? 0 : self::existing($record['parent_key'], 'page');
        $collection = $record['gallery_collection'] ?? (($record['type'] ?? '') === 'collection' ? ($record['slug'] ?? '') : '');
        $home = $key === 'home' || !empty($record['is_front_page']);
        $directory = in_array($key, ['collections', 'looks', 'guides'], true) ? $key : '';
        $sets = (array) ($record['photo_set_requirements'] ?? []); $minimum = absint($record['minimum_photos'] ?? 0);
        $check = $collection ? bixie_check_collection($collection) : ['complete' => true, 'reasons' => []];
        $desired = in_array($record['status'] ?? 'draft', ['publish', 'draft', 'private', 'pending'], true) ? $record['status'] : 'draft';
        $status = $check['complete'] ? $desired : 'draft';
        $content = self::reference_content(self::content((string) apply_filters('bixie_import_page_content', $record['content'] ?? '', $record, $state)), $record);
        $existing_content = $id ? (string) get_post_field('post_content', $id) : '';
        $unchanged_blocked = $id && get_post_meta($id, '_bixie_gate_blocked', true) && hash_equals((string) get_post_meta($id, '_bixie_import_content_hash', true), hash('sha256', $existing_content));
        if (!$new && !$state['overwrite'] && !$unchanged_blocked) { $content = $existing_content; }
        if ($home) { $check = bixie_check_home($id, $content); $status = $check['complete'] ? $desired : 'draft'; }
        if ($sets || $minimum) { $check = bixie_check_page_photos($id, $content, $sets, $minimum); $status = $check['complete'] ? $desired : 'draft'; }
        if ($directory) { $check = bixie_check_directory($directory); $status = $check['complete'] ? $desired : 'draft'; }
        $data = ['post_type' => 'page', 'post_title' => sanitize_text_field($record['title']), 'post_name' => sanitize_title($record['slug']), 'post_content' => $content, 'post_excerpt' => sanitize_textarea_field($record['excerpt'] ?? ''), 'post_parent' => $parent, 'menu_order' => absint($record['menu_order'] ?? 0), 'post_status' => $status, 'meta_input' => ['_bixie_import_key' => $key, '_bixie_collection_slug' => sanitize_title($collection), '_bixie_is_front_page' => $home ? 1 : 0, '_bixie_content_type' => sanitize_key($record['type'] ?? 'page'), '_bixie_directory_kind' => $directory, '_bixie_page_photo_sets' => $sets, '_bixie_minimum_page_photos' => $minimum]];
        if ($new || $state['overwrite']) { if ($id) { $data['ID'] = $id; } $result = wp_insert_post(wp_slash($data), true); if (is_wp_error($result)) { throw new RuntimeException($result->get_error_message()); } $id = $result; $state['counts']['pages']++; }
        else { $state['counts']['skipped']++; if ($unchanged_blocked) { wp_update_post(wp_slash(['ID' => $id, 'post_content' => $content])); } if (get_post_meta($id, '_bixie_gate_blocked', true) && $check['complete']) { wp_update_post(['ID' => $id, 'post_status' => $desired]); } }
        foreach (['_bixie_content_type', '_bixie_directory_kind', '_bixie_page_photo_sets', '_bixie_minimum_page_photos'] as $field) { update_post_meta($id, $field, $data['meta_input'][$field]); }
        if ($new || $state['overwrite'] || $unchanged_blocked) { update_post_meta($id, '_bixie_import_content_hash', hash('sha256', (string) get_post_field('post_content', $id))); }
        if (!$check['complete'] && get_post_status($id) === 'publish') { wp_update_post(['ID' => $id, 'post_status' => 'draft']); }
        update_post_meta($id, '_bixie_gate_blocked', $check['complete'] ? 0 : 1); update_post_meta($id, '_bixie_gate_reason', implode(' ', $check['reasons']));
        if ($new || $state['overwrite']) { update_post_meta($id, '_bixie_indexability', sanitize_text_field($record['indexability'] ?? 'eligible')); update_post_meta($id, '_bixie_meta_description', sanitize_text_field($record['meta_description'] ?? '')); update_post_meta($id, '_bixie_seo_title', sanitize_text_field($record['seo_title'] ?? '')); if (!empty($record['template'])) { update_post_meta($id, '_wp_page_template', sanitize_text_field($record['template'])); } }
        if ($collection) { $term = get_term_by('slug', sanitize_title($collection), 'bixie_collection'); if ($term) { update_term_meta($term->term_id, 'bixie_page_id', $id); } }
        self::log($state, $check['complete'] ? 'info' : 'warning', $key, $check['complete'] ? 'Editable block page reconciled; owner edits preserved unless overwrite was selected.' : 'Page remains draft: ' . implode(' ', $check['reasons']));
    }

    private static function finish(array $catalog, array &$state): void {
        bixie_enforce_owned_pages();
        $diagnostics = ['home' => bixie_check_home(), 'collections' => [], 'guides' => []];
        foreach ($catalog['collections'] as $collection) { $diagnostics['collections'][$collection['slug'] ?? $collection['key']] = bixie_check_collection($collection['slug'] ?? $collection['key']); }
        foreach ($catalog['pages'] as $page) { if (!empty($page['photo_set_requirements'])) { $id = self::existing($page['key'], 'page'); $diagnostics['guides'][$page['key']] = bixie_check_page_photos($id); } }
        $state['diagnostics'] = $diagnostics;
        if ($state['configure']) {
            update_option('blogname', sanitize_text_field($catalog['site']['title'] ?? 'Bixie Haircut'));
            update_option('blogdescription', sanitize_text_field($catalog['site']['description'] ?? ''));
            $home = self::existing($catalog['site']['home_slug'] ?? 'home', 'page');
            if ($home && get_post_status($home) === 'publish') { update_option('show_on_front', 'page'); update_option('page_on_front', $home); }
            else { self::log($state, 'warning', 'home', 'Static front-page setting was not changed because imported home is not publishable.'); }
            // Search visibility, owner contact details and existing posts are never silently replaced.
        }
        flush_rewrite_rules(false);
    }
}

function bixie_import_authorize(): void {
    if (!current_user_can('manage_options') || !wp_verify_nonce(sanitize_text_field(wp_unslash($_POST['nonce'] ?? '')), 'bixie_import')) { wp_send_json_error(['message' => __('Administrator permission and a valid nonce are required.', 'bixie-library')], 403); }
}
add_action('wp_ajax_bixie_import_start', static function(): void { bixie_import_authorize(); try { wp_send_json_success(Bixie_Importer::start(!empty($_POST['overwrite']), !empty($_POST['configure']))); } catch (Throwable $error) { wp_send_json_error(['message' => $error->getMessage()], 400); } });
add_action('wp_ajax_bixie_import_batch', static function(): void { bixie_import_authorize(); try { wp_send_json_success(Bixie_Importer::batch()); } catch (Throwable $error) { wp_send_json_error(['message' => $error->getMessage()], 409); } });
add_action('wp_ajax_bixie_import_status', static function(): void { bixie_import_authorize(); wp_send_json_success(Bixie_Importer::status()); });

add_action('admin_menu', static function(): void { add_management_page(__('Bixie package setup', 'bixie-library'), __('Bixie package setup', 'bixie-library'), 'manage_options', 'bixie-setup', 'bixie_import_admin_page'); });
function bixie_import_admin_page(): void {
    if (!current_user_can('manage_options')) { return; }
    $state = Bixie_Importer::status(); ?>
    <div class="wrap"><h1><?php esc_html_e('Bixie package setup', 'bixie-library'); ?></h1><p><?php esc_html_e('Import real packaged media and editable native block pages. Missing, unreviewed, incomplete or undersized images keep dependent looks, collections and the homepage in draft. Planned briefs are never counted as actual looks.', 'bixie-library'); ?></p>
    <p><?php esc_html_e('Rerunning resumes interrupted work and preserves existing owner edits by default. Deactivation or deletion does not delete content or media.', 'bixie-library'); ?></p>
    <label><input id="bixie-configure" type="checkbox"> <?php esc_html_e('Set site title/description and use the imported home only when it is publishable.', 'bixie-library'); ?></label><br>
    <label><input id="bixie-overwrite" type="checkbox"> <?php esc_html_e('Replace existing package-owned page/look copy and metadata with this package (leave unchecked to preserve edits).', 'bixie-library'); ?></label>
    <p><button id="bixie-import-start" class="button button-primary"><?php esc_html_e('Start or resume import', 'bixie-library'); ?></button> <button id="bixie-import-pause" class="button" disabled><?php esc_html_e('Pause after this batch', 'bixie-library'); ?></button></p>
    <p id="bixie-import-message" role="status" aria-live="polite"></p><progress id="bixie-import-progress" max="<?php echo max(1, absint($state['total'] ?? 1)); ?>" value="<?php echo absint($state['cursor'] ?? 0); ?>"></progress><pre id="bixie-import-log" style="white-space:pre-wrap;background:white;padding:20px;max-height:500px;overflow:auto"><?php echo esc_html(wp_json_encode($state, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES)); ?></pre>
    <hr><h2><?php esc_html_e('Structured data', 'bixie-library'); ?></h2><p><?php esc_html_e('Bixie structured data is automatically suppressed when Yoast, Rank Math, AIOSEO or SEOPress is detected. Use this switch for another schema provider. No review ratings or real-person claims are generated.', 'bixie-library'); ?></p>
    <form action="<?php echo esc_url(admin_url('admin-post.php')); ?>" method="post"><input type="hidden" name="action" value="bixie_schema_settings"><?php wp_nonce_field('bixie_schema_settings'); ?><label><input name="disabled" type="checkbox" value="1" <?php checked(get_option('bixie_schema_disabled', false)); ?>> <?php esc_html_e('Disable Bixie structured data', 'bixie-library'); ?></label><?php submit_button(__('Save schema setting', 'bixie-library')); ?></form></div>
    <?php bixie_render_owner_settings(); bixie_render_bundle_admin(); wp_enqueue_script('bixie-import-admin', BIXIE_LIBRARY_URL . 'assets/admin.js', [], BIXIE_LIBRARY_VERSION, true); wp_add_inline_script('bixie-import-admin', 'window.BixieImport=' . wp_json_encode(['url' => admin_url('admin-ajax.php'), 'nonce' => wp_create_nonce('bixie_import')]) . ';', 'before');
}
add_action('admin_post_bixie_schema_settings', static function(): void { if (!current_user_can('manage_options')) { wp_die(esc_html__('Administrator permission required.', 'bixie-library'), '', ['response' => 403]); } check_admin_referer('bixie_schema_settings'); update_option('bixie_schema_disabled', !empty($_POST['disabled']), false); wp_safe_redirect(admin_url('tools.php?page=bixie-setup')); exit; });

if (defined('WP_CLI') && WP_CLI) {
    WP_CLI::add_command('bixie import', static function($args, $assoc): void {
        try {
            Bixie_Importer::start(isset($assoc['overwrite']), isset($assoc['configure']), $assoc['manifest'] ?? null);
            do { $state = Bixie_Importer::batch(3); WP_CLI::log('Progress ' . $state['cursor'] . '/' . $state['total']); } while ($state['status'] === 'running');
            WP_CLI::log(wp_json_encode($state['counts']));
            WP_CLI::log(wp_json_encode($state['diagnostics']));
            if ($state['counts']['errors']) { WP_CLI::warning('Import finished with errors; review the setup log.'); }
            WP_CLI::success('Import reconciled. Publication readiness is reported separately; incomplete content remains draft.');
        } catch (Throwable $error) { WP_CLI::error($error->getMessage()); }
    });
    WP_CLI::add_command('bixie status', static function(): void { WP_CLI::log(wp_json_encode(Bixie_Importer::status(), JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES)); });
}
