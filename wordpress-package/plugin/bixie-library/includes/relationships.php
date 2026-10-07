<?php
if (!defined('ABSPATH')) { exit; }

function bixie_native_image_block(array $entry): array {
    $id = absint($entry['id']); $angle = sanitize_key($entry['angle']);
    $url = wp_get_attachment_image_url($id, 'full'); $alt = (string) get_post_meta($id, '_wp_attachment_image_alt', true);
    $attributes = ['id' => $id, 'sizeSlug' => 'full', 'linkDestination' => 'none', 'metadata' => ['name' => 'bixie-' . $angle]];
    $caption = sanitize_text_field($entry['caption'] ?? '') ?: ucfirst($angle);
    $markup = '<!-- wp:image ' . wp_json_encode($attributes) . ' --><figure class="wp-block-image size-full"><img src="' . esc_url($url) . '" alt="' . esc_attr($alt) . '" class="wp-image-' . $id . '"><figcaption class="wp-element-caption">' . esc_html($caption) . '</figcaption></figure><!-- /wp:image -->';
    return parse_blocks($markup)[0];
}

function bixie_named_images(array $blocks): array {
    $result = [];
    foreach ($blocks as $block) {
        $name = (string) ($block['attrs']['metadata']['name'] ?? '');
        if (($block['blockName'] ?? '') === 'core/image' && preg_match('/^bixie-(front|side|back|detail|reference)$/', $name, $match) && !empty($block['attrs']['id'])) {
            $caption = (string) ($block['attrs']['caption'] ?? '');
            if (!$caption && preg_match('/<figcaption[^>]*>(.*?)<\/figcaption>/s', $block['innerHTML'] ?? '', $caption_match)) { $caption = html_entity_decode(wp_strip_all_tags($caption_match[1]), ENT_QUOTES, get_bloginfo('charset')); }
            $result[] = ['id' => absint($block['attrs']['id']), 'angle' => $match[1], 'caption' => $caption];
        }
        $result = array_merge($result, bixie_named_images($block['innerBlocks'] ?? []));
    }
    return $result;
}

function bixie_sync_native_to_meta(int $post_id, $post = null): void {
    if (!empty($GLOBALS['bixie_relationship_sync']) || wp_is_post_revision($post_id) || wp_is_post_autosave($post_id) || get_post_type($post_id) !== 'bixie_look') { return; }
    $post = $post ?: get_post($post_id); if (!$post) { return; }
    $images = bixie_named_images(parse_blocks($post->post_content));
    // Only package-labelled native blocks own these relationships; unrelated editorial images are left alone.
    if (!$images && !get_post_meta($post_id, '_bixie_named_views_managed', true) && !str_contains($post->post_content, 'bixie-front') && !str_contains($post->post_content, 'bixie-side') && !str_contains($post->post_content, 'bixie-back')) { return; }
    $images = bixie_sanitize_images($images);
    $existing = (array) get_post_meta($post_id, 'bixie_images', true);
    foreach ($images as &$image) { foreach ($existing as $entry) { if ($entry['id'] === $image['id'] && $entry['angle'] === $image['angle'] && !$image['caption']) { $image['caption'] = $entry['caption'] ?? ''; } } } unset($image);
    if ($images === $existing) { return; }
    $GLOBALS['bixie_relationship_sync'] = true;
    update_post_meta($post_id, '_bixie_named_views_managed', 1);
    update_post_meta($post_id, 'bixie_images', $images);
    if ($images) { set_post_thumbnail($post_id, $images[0]['id']); } else { delete_post_thumbnail($post_id); }
    $GLOBALS['bixie_relationship_sync'] = false;
}
add_action('save_post_bixie_look', 'bixie_sync_native_to_meta', 20, 2);

function bixie_replace_named_blocks(array $blocks, array $entries, array &$seen): array {
    $output = [];
    foreach ($blocks as $block) {
        $name = (string) ($block['attrs']['metadata']['name'] ?? '');
        if (($block['blockName'] ?? '') === 'core/image' && preg_match('/^bixie-(front|side|back|detail|reference)$/', $name, $match)) {
            $angle = $match[1];
            if (empty($entries[$angle])) { continue; }
            $seen[$angle] = true; $output[] = bixie_native_image_block($entries[$angle]); continue;
        }
        if (!empty($block['innerBlocks'])) {
            $children = []; $inner = []; $index = 0;
            foreach ($block['innerContent'] as $fragment) {
                if ($fragment !== null) { $inner[] = $fragment; continue; }
                $child = $block['innerBlocks'][$index++] ?? null;
                if (!$child) { continue; }
                $replacement = bixie_replace_named_blocks([$child], $entries, $seen);
                if ($replacement) { $children[] = $replacement[0]; $inner[] = null; }
            }
            $block['innerBlocks'] = $children; $block['innerContent'] = $inner;
            if ($block['blockName'] === 'core/gallery' && !$children) { continue; }
        }
        $output[] = $block;
    }
    return $output;
}

function bixie_sync_meta_to_native($meta_id, $post_id, $meta_key): void {
    if ($meta_key !== 'bixie_images' || !empty($GLOBALS['bixie_relationship_sync']) || get_post_type($post_id) !== 'bixie_look') { return; }
    $post = get_post($post_id); if (!$post) { return; }
    $entries = [];
    foreach ((array) get_post_meta($post_id, 'bixie_images', true) as $entry) { if (!empty($entry['id'])) { $entries[$entry['angle']] = $entry; } }
    $seen = []; $blocks = bixie_replace_named_blocks(parse_blocks($post->post_content), $entries, $seen);
    foreach ($entries as $angle => $entry) { if (empty($seen[$angle])) { $blocks[] = bixie_native_image_block($entry); } }
    $content = serialize_blocks($blocks);
    if ($content === $post->post_content) { return; }
    $GLOBALS['bixie_relationship_sync'] = true;
    update_post_meta($post_id, '_bixie_named_views_managed', 1);
    wp_update_post(wp_slash(['ID' => $post_id, 'post_content' => $content]));
    if ($entries) { set_post_thumbnail($post_id, reset($entries)['id']); } else { delete_post_thumbnail($post_id); }
    $GLOBALS['bixie_relationship_sync'] = false;
}
add_action('updated_post_meta', 'bixie_sync_meta_to_native', 20, 3);
add_action('added_post_meta', 'bixie_sync_meta_to_native', 20, 3);
add_action('deleted_post_meta', 'bixie_sync_meta_to_native', 20, 3);
