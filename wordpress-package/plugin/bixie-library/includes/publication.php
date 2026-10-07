<?php
if (!defined('ABSPATH')) { exit; }

function bixie_requirements(): array {
    return wp_parse_args((array) get_option('bixie_requirements', []), ['require_complete_angles' => true, 'minimum_collection_photos' => 20, 'minimum_complete_looks_per_collection' => 7, 'minimum_native_long_edge' => 1024, 'no_upscaling' => true, 'native_resolution_tier' => 'generator-native', 'allow_source_reuse_between_primary_collections' => false]);
}

/** Exact original-file identity; cache is tied to the actual source path and file stat. */
function bixie_source_fingerprint(int $id): string {
    $path = bixie_original_source_path($id); if (!$path || !is_file($path)) { return ''; }
    $stamp = $path . '|' . filesize($path) . '|' . filemtime($path); $cached = get_post_meta($id, '_bixie_source_identity', true);
    if (is_array($cached) && ($cached['stamp'] ?? '') === $stamp && !empty($cached['hash'])) { return (string) $cached['hash']; }
    $hash = hash_file('sha256', $path); if (!$hash) { return ''; } update_post_meta($id, '_bixie_source_identity', ['stamp' => $stamp, 'hash' => $hash]); return $hash;
}

function bixie_check_look(int $post_id, ?array $entries = null, ?string $primary = null): array {
    $entries = $entries ?? (array) get_post_meta($post_id, 'bixie_images', true);
    $requirements = bixie_requirements();
    $angles = []; $ids = []; $hashes = []; $reasons = [];
    foreach ($entries as $entry) {
        if (!is_array($entry)) { continue; }
        $id = absint($entry['id'] ?? 0);
        $angle = sanitize_key($entry['angle'] ?? 'reference');
        if (!$id || !wp_attachment_is_image($id)) { $reasons[] = 'A source attachment is missing.'; continue; }
        if (!get_post_meta($id, '_bixie_review_approved', true)) { $reasons[] = 'A source has not passed the explicit composition and attire review.'; continue; }
        if (!is_file((string) get_attached_file($id))) { $reasons[] = 'A display image file cannot be read.'; continue; }
        $path = bixie_original_source_path($id);
        $size = $path && is_file($path) ? wp_getimagesize($path) : false;
        if (!$size) { $reasons[] = 'An original image file cannot be read.'; continue; }
        if (max($size[0], $size[1]) < absint($requirements['minimum_native_long_edge'])) { $reasons[] = 'A native source is below the required long-edge resolution.'; continue; }
        if ((!empty($requirements['no_upscaling']) || absint($requirements['minimum_native_long_edge']) >= 7680) && !get_post_meta($id, '_bixie_native_verified', true)) { $reasons[] = 'Original non-upscaled source provenance has not been confirmed.'; continue; }
        $ids[$id] = true; $angles[$angle] = true; $hash = bixie_source_fingerprint($id); if ($hash) { $hashes[$hash] = true; }
    }
    if (!$ids) { $reasons[] = 'No approved usable source images are attached.'; }
    if ($requirements['require_complete_angles']) {
        foreach (['front', 'side', 'back'] as $angle) { if (empty($angles[$angle])) { $reasons[] = 'Missing approved ' . $angle . ' view.'; } }
        if (count($ids) < 3) { $reasons[] = 'Three separate approved source images are required.'; }
        if (count($hashes) < 3) { $reasons[] = 'Three distinct original photographs are required; duplicate file copies do not count as separate views.'; }
    }
    $primary = sanitize_title($primary ?? (string) get_post_meta($post_id, 'bixie_primary_collection', true));
    if ($primary && !$requirements['allow_source_reuse_between_primary_collections'] && $ids) {
        $others = get_posts(['post_type' => 'bixie_look', 'post_status' => 'publish', 'posts_per_page' => -1, 'fields' => 'ids', 'exclude' => $post_id ? [$post_id] : [], 'meta_query' => [['key' => 'bixie_primary_collection', 'value' => $primary, 'compare' => '!=']]]);
        foreach ($others as $other) { foreach ((array) get_post_meta($other, 'bixie_images', true) as $entry) { $source = absint($entry['id'] ?? 0); if (isset($ids[$source]) || isset($hashes[bixie_source_fingerprint($source)])) { $reasons[] = 'A source photo is already assigned to a published look in another primary collection.'; break 2; } } }
    }
    return ['complete' => !$reasons, 'ids' => array_keys($ids), 'hashes' => array_keys($hashes), 'reasons' => array_values(array_unique($reasons))];
}

function bixie_check_collection(string $slug): array {
    $term = get_term_by('slug', sanitize_title($slug), 'bixie_collection');
    if (!$term) { return ['complete' => false, 'photos' => 0, 'looks' => 0, 'reasons' => ['Collection has no imported classification term.']]; }
    $posts = get_posts(['post_type' => 'bixie_look', 'post_status' => 'publish', 'posts_per_page' => -1, 'fields' => 'ids', 'tax_query' => [['taxonomy' => 'bixie_collection', 'field' => 'term_id', 'terms' => $term->term_id]]]);
    $ids = []; $hashes = []; $looks = 0; $requirements = bixie_requirements();
    foreach ($posts as $post_id) {
        $primary = (string) get_post_meta($post_id, 'bixie_primary_collection', true);
        if (!$requirements['allow_source_reuse_between_primary_collections'] && $primary !== $slug) { continue; }
        $result = bixie_check_look((int) $post_id);
        if (!$result['complete']) { continue; }
        $looks++;
        foreach ($result['ids'] as $id) { $ids[$id] = true; }
        foreach ($result['hashes'] as $hash) { $hashes[$hash] = true; }
    }
    $requirements = bixie_requirements(); $reasons = [];
    if (count($hashes) < absint($requirements['minimum_collection_photos'])) { $reasons[] = 'Only ' . count($hashes) . ' distinct approved original photos; ' . absint($requirements['minimum_collection_photos']) . ' required.'; }
    if ($looks < absint($requirements['minimum_complete_looks_per_collection'])) { $reasons[] = 'Only ' . $looks . ' complete published looks; ' . absint($requirements['minimum_complete_looks_per_collection']) . ' required.'; }
    return ['complete' => !$reasons, 'photos' => count($hashes), 'looks' => $looks, 'reasons' => $reasons];
}

function bixie_home_photo_ids(array $blocks): array {
    $ids = [];
    foreach ($blocks as $block) {
        if (($block['blockName'] ?? '') === 'core/image' && !empty($block['attrs']['id'])) { $ids[] = absint($block['attrs']['id']); }
        if (($block['blockName'] ?? '') === 'bixie/library') { $attrs = $block['attrs'] ?? []; $results = bixie_query_looks(['per_page' => $attrs['perPage'] ?? 12, 'collection' => $attrs['collection'] ?? '', 'exclude' => $attrs['excludeLookIds'] ?? []]); foreach ($results['items'] as $record) { if (!empty($record['image']['id'])) { $ids[] = $record['image']['id']; } } }
        $ids = array_merge($ids, bixie_home_photo_ids($block['innerBlocks'] ?? []));
    }
    return $ids;
}

function bixie_check_home(int $post_id = 0, ?string $content = null): array {
    $slugs = (array) get_option('bixie_required_collections', []); $reasons = [];
    if (!$slugs) { $reasons[] = 'Required collection definitions have not been imported.'; }
    foreach ($slugs as $slug) { $result = bixie_check_collection($slug); if (!$result['complete']) { $reasons[] = $slug . ': ' . implode(' ', $result['reasons']); } }
    foreach ((array) get_option('bixie_required_home_media', []) as $key) {
        $id = bixie_get_package_attachment($key);
        if (!$id || !bixie_check_look(0, [['id' => $id, 'angle' => 'reference']])['ids']) { $reasons[] = 'Required homepage source missing, unreviewed or below native resolution: ' . $key; }
    }
    $video_key = (string) get_option('bixie_required_home_video', '');
    if ($video_key) { $video = bixie_get_package_attachment($video_key); if (!$video || !bixie_check_film($video)) { $reasons[] = 'Required reviewed multi-view photographic film missing: ' . $video_key; } }
    if ($content === null && !$post_id) { $homes = get_posts(['post_type' => 'page', 'post_status' => ['publish', 'draft', 'private', 'pending'], 'posts_per_page' => 1, 'fields' => 'ids', 'meta_key' => '_bixie_is_front_page', 'meta_value' => '1']); $post_id = $homes ? $homes[0] : 0; }
    if ($content === null && $post_id) { $content = (string) get_post_field('post_content', $post_id); }
    $photos = $content !== null ? bixie_home_photo_ids(parse_blocks($content)) : [];
    if (count($photos) !== count(array_unique($photos))) { $reasons[] = 'The homepage repeats a photo attachment; each photograph must appear once.'; }
    $identities = array_filter(array_map('bixie_source_fingerprint', array_unique($photos))); if (count($identities) !== count(array_unique($identities))) { $reasons[] = 'The homepage repeats an original photograph under different attachment IDs.'; }
    foreach (array_unique($photos) as $photo) { if (!bixie_check_look(0, [['id' => $photo, 'angle' => 'reference']])['ids']) { $reasons[] = 'A homepage photograph is not reviewed, native-qualified or readable.'; } }
    $minimum = absint(bixie_requirements()['minimum_home_unique_photos'] ?? 75);
    if (count(array_unique($photos)) < $minimum) { $reasons[] = 'Only ' . count(array_unique($photos)) . ' unique homepage photos; ' . $minimum . ' required.'; }
    return ['complete' => !$reasons, 'reasons' => $reasons];
}

/** A film remains usable only while all of its declared photographic sources qualify. */
function bixie_check_film(int $id): bool {
    if (get_post_mime_type($id) !== 'video/mp4' || !get_post_meta($id, '_bixie_review_approved', true) || !get_post_meta($id, '_bixie_multiview_declared', true) || !bixie_is_real_mp4((string) get_attached_file($id))) { return false; }
    $entries = (array) get_post_meta($id, '_bixie_film_sources', true); $angles = []; $ids = []; $hashes = [];
    if (!$entries) { foreach (array_unique((array) get_post_meta($id, '_bixie_film_source_keys', true)) as $key) { $source = bixie_get_package_attachment((string) $key); $entries[] = ['id' => $source, 'angle' => get_post_meta($source, '_bixie_asset_angle', true)]; } }
    foreach ($entries as $entry) {
        $source = absint($entry['id'] ?? 0);
        if (!$source || !bixie_check_look(0, [['id' => $source, 'angle' => 'reference']])['ids']) { return false; }
        $ids[$source] = true; $hashes[bixie_source_fingerprint($source)] = true; $angles[] = sanitize_key($entry['angle'] ?? 'reference');
    }
    return count($ids) >= 3 && count($hashes) >= 3 && !array_diff(['front', 'side', 'back'], $angles);
}

function bixie_find_imported_look(string $key): int {
    $ids = get_posts(['post_type' => 'bixie_look', 'post_status' => ['publish', 'draft', 'pending', 'private', 'future'], 'posts_per_page' => 1, 'fields' => 'ids', 'meta_key' => '_bixie_import_key', 'meta_value' => sanitize_text_field($key)]);
    return $ids ? (int) $ids[0] : 0;
}

/** Native reference galleries use the same current, complete approved look records. */
function bixie_page_reference_images(array $sets): array {
    $entries = []; $reasons = [];
    foreach ($sets as $set) {
        $key = sanitize_text_field($set['look_key'] ?? ''); $id = bixie_find_imported_look($key);
        if (!$id || get_post_status($id) !== 'publish' || !bixie_check_look($id)['complete']) { $reasons[] = 'Referenced complete published look unavailable: ' . $key; continue; }
        $images = (array) get_post_meta($id, 'bixie_images', true);
        foreach ((array) ($set['angles'] ?? ['front', 'side', 'back']) as $angle) {
            $matches = array_values(array_filter($images, static fn($entry) => ($entry['angle'] ?? '') === $angle));
            if (!$matches) { $reasons[] = 'Referenced view unavailable: ' . $key . ' ' . $angle; continue; }
            $entry = $matches[0]; $entry['caption'] = sanitize_text_field($set['caption'] ?? '') . ' · ' . ucfirst(sanitize_key($angle)); $entry['look_key'] = $key; $entries[] = $entry;
        }
    }
    return ['entries' => $entries, 'reasons' => $reasons];
}

function bixie_native_photo_ids(array $blocks): array {
    $ids = [];
    foreach ($blocks as $block) { if (($block['blockName'] ?? '') === 'core/image' && !empty($block['attrs']['id'])) { $ids[] = absint($block['attrs']['id']); } $ids = array_merge($ids, bixie_native_photo_ids($block['innerBlocks'] ?? [])); }
    return $ids;
}

function bixie_check_page_photos(int $id, ?string $content = null, ?array $sets = null, ?int $minimum = null): array {
    $sets = $sets ?? (array) get_post_meta($id, '_bixie_page_photo_sets', true); $minimum = $minimum ?? absint(get_post_meta($id, '_bixie_minimum_page_photos', true));
    if (!$sets && !$minimum) { return ['complete' => true, 'reasons' => []]; }
    $reference = bixie_page_reference_images($sets); $reasons = $reference['reasons'];
    $ids = array_unique(bixie_native_photo_ids(parse_blocks($content ?? (string) get_post_field('post_content', $id))));
    foreach ($ids as $image) { if (!bixie_check_look(0, [['id' => $image, 'angle' => 'reference']])['ids']) { $reasons[] = 'A guide photograph is not reviewed, native-qualified or readable.'; } }
    foreach ($reference['entries'] as $entry) { if (!in_array(absint($entry['id']), $ids, true)) { $reasons[] = 'A current referenced view is missing from the editable gallery: ' . $entry['look_key'] . ' ' . $entry['angle']; } }
    if (count($ids) < $minimum) { $reasons[] = 'Only ' . count($ids) . ' distinct guide photos; ' . $minimum . ' required.'; }
    return ['complete' => !$reasons, 'reasons' => array_values(array_unique($reasons))];
}

function bixie_check_directory(string $kind): array {
    if ($kind === 'looks') { $available = bixie_query_looks(['per_page' => 1])['total'] > 0; }
    else { $key = $kind === 'collections' ? '_bixie_collection_slug' : '_bixie_content_type'; $value = $kind === 'collections' ? '' : 'guide'; $pages = get_posts(['post_type' => 'page', 'post_status' => 'publish', 'posts_per_page' => 1, 'fields' => 'ids', 'meta_query' => [['key' => $key, 'value' => $value, 'compare' => $kind === 'collections' ? '!=' : '=']]]); $available = (bool) $pages; }
    return ['complete' => $available, 'reasons' => $available ? [] : ['This directory has no complete published ' . $kind . ' yet.']];
}

add_filter('wp_insert_post_data', static function(array $data, array $postarr): array {
    if (($data['post_status'] ?? '') !== 'publish') { return $data; }
    $id = absint($postarr['ID'] ?? 0);
    if (($data['post_type'] ?? '') === 'bixie_look') {
        $entries = $postarr['meta_input']['bixie_images'] ?? null;
        $primary = $postarr['meta_input']['bixie_primary_collection'] ?? null;
        if (!bixie_check_look($id, is_array($entries) ? $entries : null, is_string($primary) ? $primary : null)['complete']) { $data['post_status'] = 'draft'; }
    } elseif (($data['post_type'] ?? '') === 'page') {
        $slug = $postarr['meta_input']['_bixie_collection_slug'] ?? get_post_meta($id, '_bixie_collection_slug', true);
        $home = $postarr['meta_input']['_bixie_is_front_page'] ?? get_post_meta($id, '_bixie_is_front_page', true);
        if ($slug && !bixie_check_collection((string) $slug)['complete']) { $data['post_status'] = 'draft'; }
        if ($home && !bixie_check_home($id, wp_unslash((string) $data['post_content']))['complete']) { $data['post_status'] = 'draft'; }
        $sets = $postarr['meta_input']['_bixie_page_photo_sets'] ?? null; $minimum = $postarr['meta_input']['_bixie_minimum_page_photos'] ?? null;
        if (!bixie_check_page_photos($id, wp_unslash((string) $data['post_content']), is_array($sets) ? $sets : null, $minimum === null ? null : absint($minimum))['complete']) { $data['post_status'] = 'draft'; }
        $directory = $postarr['meta_input']['_bixie_directory_kind'] ?? get_post_meta($id, '_bixie_directory_kind', true);
        if ($directory && !bixie_check_directory((string) $directory)['complete']) { $data['post_status'] = 'draft'; }
    }
    return $data;
}, 10, 2);

function bixie_refresh_look_gate($meta_id = 0, $post_id = 0, $meta_key = ''): void {
    static $busy = false;
    if ($busy || !$post_id || get_post_type($post_id) !== 'bixie_look' || !in_array($meta_key, ['bixie_images', 'bixie_primary_collection', '_bixie_review_approved'], true)) { return; }
    $busy = true; $result = bixie_check_look((int) $post_id);
    update_post_meta($post_id, '_bixie_record_complete', $result['complete'] ? '1' : '0');
    update_post_meta($post_id, '_bixie_gate_reason', implode(' ', $result['reasons']));
    if (!$result['complete'] && get_post_status($post_id) === 'publish') { wp_update_post(['ID' => $post_id, 'post_status' => 'draft']); }
    $busy = false;
    bixie_enforce_owned_pages();
}
add_action('updated_post_meta', 'bixie_refresh_look_gate', 10, 3);
add_action('added_post_meta', 'bixie_refresh_look_gate', 10, 3);
add_action('deleted_post_meta', 'bixie_refresh_look_gate', 10, 3);

function bixie_enforce_owned_pages(): void {
    static $busy = false; if ($busy) { return; } $busy = true;
    $pages = get_posts(['post_type' => 'page', 'post_status' => 'publish', 'posts_per_page' => -1, 'meta_query' => ['relation' => 'OR', ['key' => '_bixie_collection_slug', 'value' => '', 'compare' => '!='], ['key' => '_bixie_is_front_page', 'value' => '1'], ['key' => '_bixie_minimum_page_photos', 'value' => 0, 'compare' => '>'], ['key' => '_bixie_directory_kind', 'value' => '', 'compare' => '!=']]]);
    foreach ($pages as $page) { $slug = (string) get_post_meta($page->ID, '_bixie_collection_slug', true); $home = get_post_meta($page->ID, '_bixie_is_front_page', true); $directory = (string) get_post_meta($page->ID, '_bixie_directory_kind', true); $check = $slug ? bixie_check_collection($slug) : ($home ? bixie_check_home($page->ID) : ($directory ? bixie_check_directory($directory) : bixie_check_page_photos($page->ID))); if (!$check['complete']) { wp_update_post(['ID' => $page->ID, 'post_status' => 'draft']); update_post_meta($page->ID, '_bixie_gate_blocked', 1); update_post_meta($page->ID, '_bixie_gate_reason', implode(' ', $check['reasons'])); } }
    $busy = false;
}

function bixie_revalidate_sources(int $attachment_id = 0): void {
    static $busy = false; if ($busy) { return; } $busy = true;
    $posts = get_posts(['post_type' => 'bixie_look', 'post_status' => ['publish', 'draft', 'private', 'pending', 'future'], 'posts_per_page' => -1, 'fields' => 'ids']);
    foreach ($posts as $post_id) {
        $entries = (array) get_post_meta($post_id, 'bixie_images', true);
        if ($attachment_id && !array_filter($entries, static fn($entry) => absint($entry['id'] ?? 0) === $attachment_id)) { continue; }
        $check = bixie_check_look((int) $post_id, $entries);
        update_post_meta($post_id, '_bixie_record_complete', $check['complete'] ? '1' : '0'); update_post_meta($post_id, '_bixie_gate_reason', implode(' ', $check['reasons']));
        if (!$check['complete'] && get_post_status($post_id) === 'publish') { wp_update_post(['ID' => $post_id, 'post_status' => 'draft']); }
    }
    bixie_invalidate_catalog(); bixie_enforce_owned_pages(); $busy = false;
}
function bixie_track_attachment_review($meta_id, $id, $key): void {
    if (get_post_type($id) !== 'attachment' || !wp_attachment_is_image($id)) { return; }
    $delivery = (string) get_attached_file($id); $source = bixie_original_source_path((int) $id); clearstatcache();
    if ($key === '_bixie_review_approved' && get_post_meta($id, $key, true)) {
        update_post_meta($id, '_bixie_reviewed_delivery_file', $delivery);
        update_post_meta($id, '_bixie_reviewed_delivery_hash', is_file($delivery) ? hash_file('sha256', $delivery) : '');
        update_post_meta($id, '_bixie_reviewed_source_hash', is_file($source) ? hash_file('sha256', $source) : '');
        return;
    }
    if (!in_array($key, ['_wp_attached_file', '_wp_attachment_metadata', '_bixie_original_source_file', '_bixie_delivery_file'], true) || !get_post_meta($id, '_bixie_review_approved', true)) { return; }
    $expected = (string) get_post_meta($id, '_bixie_reviewed_delivery_hash', true); $source_hash = (string) get_post_meta($id, '_bixie_reviewed_source_hash', true);
    if (!$expected || !is_file($delivery) || get_post_meta($id, '_bixie_reviewed_delivery_file', true) !== $delivery || !hash_equals($expected, hash_file('sha256', $delivery)) || !$source_hash || !is_file($source) || !hash_equals($source_hash, hash_file('sha256', $source))) {
        update_post_meta($id, '_bixie_review_approved', 0); update_post_meta($id, '_bixie_native_verified', 0);
        foreach (['_bixie_original_source_file', '_bixie_original_source_url', '_bixie_delivery_file', '_bixie_source_identity'] as $field) { delete_post_meta($id, $field); }
    }
}
foreach (['added_post_meta', 'updated_post_meta', 'deleted_post_meta'] as $hook) { add_action($hook, 'bixie_track_attachment_review', 25, 3); }
foreach (['added_post_meta', 'updated_post_meta', 'deleted_post_meta'] as $hook) {
    add_action($hook, static function($meta_id, $post_id, $key): void { if (get_post_type($post_id) === 'attachment' && in_array($key, ['_bixie_review_approved', '_bixie_native_verified', '_wp_attached_file', '_wp_attachment_metadata', '_bixie_original_source_file', '_bixie_delivery_file', '_bixie_asset_key', '_bixie_multiview_declared', '_bixie_film_sources', '_bixie_film_source_keys'], true)) { if (in_array($key, ['_wp_attached_file', '_wp_attachment_metadata', '_bixie_original_source_file', '_bixie_delivery_file'], true)) { delete_post_meta($post_id, '_bixie_source_identity'); clearstatcache(); } bixie_revalidate_sources((int) $post_id); } }, 30, 3);
}
add_action('deleted_post', static function($id, $post): void { if ($post->post_type === 'attachment') { bixie_revalidate_sources((int) $id); } elseif ($post->post_type === 'bixie_look') { bixie_enforce_owned_pages(); } }, 30, 2);
add_action('set_object_terms', static function($id, $terms, $tt_ids, $taxonomy): void { if ($taxonomy === 'bixie_collection') { if (!get_post_meta($id, 'bixie_primary_collection', true)) { $assigned = wp_get_object_terms($id, $taxonomy, ['orderby' => 'term_id', 'order' => 'ASC']); if (is_array($assigned) && $assigned) { update_post_meta($id, 'bixie_primary_collection', $assigned[0]->slug); } } bixie_enforce_owned_pages(); } }, 30, 4);
add_action('updated_post_meta', static function($meta_id, $id, $key): void { if ($key === 'bixie_primary_collection') { bixie_enforce_owned_pages(); } }, 30, 3);
add_action('update_option_bixie_requirements', static function(): void { bixie_revalidate_sources(); });
add_action('transition_post_status', static function($new, $old, $post): void { if ($post->post_type === 'bixie_look') { if ($new === 'publish') { $check = bixie_check_look($post->ID); update_post_meta($post->ID, '_bixie_record_complete', $check['complete'] ? '1' : '0'); if (!$check['complete']) { wp_update_post(['ID' => $post->ID, 'post_status' => 'draft']); } } if ($old === 'publish' || $new === 'publish') { bixie_enforce_owned_pages(); } } elseif ($post->post_type === 'page' && ($old === 'publish' || $new === 'publish')) { bixie_enforce_owned_pages(); } }, 30, 3);

add_filter('attachment_fields_to_edit', static function(array $fields, $post): array {
    $image = wp_attachment_is_image($post->ID); $video = get_post_mime_type($post->ID) === 'video/mp4';
    if (!$image && !$video) { return $fields; }
    $fields['bixie_asset_key'] = ['label' => __('Bixie media role', 'bixie-library'), 'input' => 'text', 'value' => get_post_meta($post->ID, '_bixie_asset_key', true), 'helps' => __('Optional package role, for example home-hero or home-motion-film. Role names must be unique. The setup report lists required roles.', 'bixie-library')];
    $checked = get_post_meta($post->ID, '_bixie_review_approved', true) ? ' checked' : '';
    $fields['bixie_review_approved'] = ['label' => __('Bixie source review', 'bixie-library'), 'input' => 'html', 'html' => '<label><input type="checkbox" name="attachments[' . absint($post->ID) . '][bixie_review_approved]" value="1"' . $checked . '> ' . esc_html__('Reviewed: full hairstyle visible, opaque loose high collar, no chest outline; accurate angle and consistent look.', 'bixie-library') . '</label>', 'helps' => __('Approval does not change the actual native resolution or replace a front/side/back set.', 'bixie-library')];
    if ($image) { $fields['bixie_native_verified'] = ['label' => __('Original-source provenance', 'bixie-library'), 'input' => 'html', 'html' => '<label><input type="checkbox" name="attachments[' . absint($post->ID) . '][bixie_native_verified]" value="1"' . (get_post_meta($post->ID, '_bixie_native_verified', true) ? ' checked' : '') . '> ' . esc_html__('I have confirmed this is an original native source, not an enlarged or upscaled replica.', 'bixie-library') . '</label>']; }
    if ($video) {
        $fields['bixie_multiview_declared'] = ['label' => __('Photographic film review', 'bixie-library'), 'input' => 'html', 'html' => '<label><input type="checkbox" name="attachments[' . absint($post->ID) . '][bixie_multiview_declared]" value="1"' . (get_post_meta($post->ID, '_bixie_multiview_declared', true) ? ' checked' : '') . '> ' . esc_html__('This film actually presents the corresponding front, side and back photographs chosen below, with consistent styling and attire.', 'bixie-library') . '</label>'];
        $sources = (array) get_post_meta($post->ID, '_bixie_film_sources', true); $selected = []; foreach ($sources as $source) { $selected[$source['angle']] = absint($source['id']); }
        if (!$sources) { foreach ((array) get_post_meta($post->ID, '_bixie_film_source_keys', true) as $key) { $source = bixie_get_package_attachment($key); $selected[get_post_meta($source, '_bixie_asset_angle', true)] = $source; } }
        $photos = get_posts(['post_type' => 'attachment', 'post_status' => 'inherit', 'post_mime_type' => 'image', 'posts_per_page' => -1, 'orderby' => 'title', 'order' => 'ASC']);
        foreach (['front', 'side', 'back'] as $angle) { $html = '<select name="attachments[' . absint($post->ID) . '][bixie_film_' . $angle . ']" aria-label="' . esc_attr(ucfirst($angle) . ' film source') . '"><option value="0">' . esc_html__('Choose an actual corresponding photograph', 'bixie-library') . '</option>'; foreach ($photos as $photo) { $html .= '<option value="' . absint($photo->ID) . '"' . selected($selected[$angle] ?? 0, $photo->ID, false) . '>' . esc_html(get_the_title($photo) . ' (#' . $photo->ID . ')') . '</option>'; } $html .= '</select>'; $fields['bixie_film_' . $angle] = ['label' => ucfirst($angle) . ' source', 'input' => 'html', 'html' => $html]; }
    }
    return $fields;
}, 10, 2);
add_filter('attachment_fields_to_save', static function(array $post, array $attachment): array {
    if (current_user_can('edit_post', $post['ID']) && (wp_attachment_is_image($post['ID']) || get_post_mime_type($post['ID']) === 'video/mp4')) {
        update_post_meta($post['ID'], '_bixie_review_approved', !empty($attachment['bixie_review_approved']) ? 1 : 0);
        if (wp_attachment_is_image($post['ID'])) { update_post_meta($post['ID'], '_bixie_native_verified', !empty($attachment['bixie_native_verified']) ? 1 : 0); }
        if (isset($attachment['bixie_asset_key'])) { $key = sanitize_key($attachment['bixie_asset_key']); $existing = $key ? bixie_get_package_attachment($key) : 0; if (!$existing || $existing === absint($post['ID'])) { update_post_meta($post['ID'], '_bixie_asset_key', $key); } else { $post['errors']['bixie_asset_key']['errors'][] = __('That media role belongs to another attachment.', 'bixie-library'); } }
        if (get_post_mime_type($post['ID']) === 'video/mp4') { $entries = []; foreach (['front', 'side', 'back'] as $angle) { $source = absint($attachment['bixie_film_' . $angle] ?? 0); if ($source && wp_attachment_is_image($source)) { $entries[] = ['id' => $source, 'angle' => $angle]; } } update_post_meta($post['ID'], '_bixie_film_sources', $entries); update_post_meta($post['ID'], '_bixie_multiview_declared', !empty($attachment['bixie_multiview_declared']) ? 1 : 0); }
        bixie_enforce_owned_pages();
    }
    return $post;
}, 10, 2);
