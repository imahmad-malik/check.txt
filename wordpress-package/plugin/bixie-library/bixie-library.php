<?php
/**
 * Plugin Name: Bixie Library
 * Description: Editable hairstyle records, original-photo collections, accessible browsing tools and a resumable content importer for Bixie Haircut.
 * Version: 1.0.0
 * Requires at least: 6.6
 * Requires PHP: 8.0
 * Author: Bixie Haircut
 * License: GPL-2.0-or-later
 * Text Domain: bixie-library
 */

if (!defined('ABSPATH')) { exit; }
define('BIXIE_LIBRARY_VERSION', '1.0.0');
define('BIXIE_LIBRARY_DIR', plugin_dir_path(__FILE__));
define('BIXIE_LIBRARY_URL', plugin_dir_url(__FILE__));

function bixie_library_register_types(): void {
    register_post_type('bixie_look', [
        'labels' => ['name' => __('Bixie looks', 'bixie-library'), 'singular_name' => __('Bixie look', 'bixie-library'), 'add_new_item' => __('Add hairstyle look', 'bixie-library'), 'edit_item' => __('Edit hairstyle look', 'bixie-library')],
        'public' => true, 'show_in_rest' => true, 'has_archive' => false,
        'rewrite' => ['slug' => 'looks', 'with_front' => false],
        'menu_icon' => 'dashicons-format-gallery',
        'supports' => ['title', 'editor', 'excerpt', 'thumbnail', 'revisions', 'custom-fields'],
    ]);
    register_taxonomy('bixie_collection', 'bixie_look', [
        'labels' => ['name' => __('Look collections', 'bixie-library'), 'singular_name' => __('Look collection', 'bixie-library')],
        'public' => true, 'hierarchical' => true, 'show_in_rest' => true,
        'rewrite' => ['slug' => 'look-collection', 'with_front' => false],
    ]);
    $short_fields = ['texture', 'length', 'fringe', 'colour', 'density', 'strand', 'finish', 'age_reference', 'face_reference', 'primary_collection'];
    foreach ($short_fields as $field) {
        register_post_meta('bixie_look', 'bixie_' . $field, [
            'type' => 'string', 'single' => true, 'default' => '', 'show_in_rest' => true,
            'sanitize_callback' => 'sanitize_text_field',
            'auth_callback' => static fn($allowed, $meta_key, $post_id): bool => current_user_can('edit_post', (int) $post_id),
        ]);
    }
    foreach (['maintenance', 'styling'] as $field) {
        register_post_meta('bixie_look', 'bixie_' . $field, [
            'type' => 'string', 'single' => true, 'default' => '', 'show_in_rest' => true,
            'sanitize_callback' => 'sanitize_textarea_field',
            'auth_callback' => static fn($allowed, $meta_key, $post_id): bool => current_user_can('edit_post', (int) $post_id),
        ]);
    }
    register_post_meta('bixie_look', 'bixie_ai_concept', [
        'type' => 'boolean', 'single' => true, 'default' => false, 'show_in_rest' => true,
        'sanitize_callback' => 'rest_sanitize_boolean',
        'auth_callback' => static fn($allowed, $meta_key, $post_id): bool => current_user_can('edit_post', (int) $post_id),
    ]);
    register_post_meta('bixie_look', 'bixie_images', [
        'type' => 'array', 'single' => true, 'default' => [],
        'show_in_rest' => ['schema' => ['type' => 'array', 'items' => ['type' => 'object', 'properties' => [
            'id' => ['type' => 'integer'], 'angle' => ['type' => 'string'], 'caption' => ['type' => 'string'],
        ], 'additionalProperties' => false]]],
        'sanitize_callback' => 'bixie_sanitize_images',
        'auth_callback' => static fn($allowed, $meta_key, $post_id): bool => current_user_can('edit_post', (int) $post_id),
    ]);
}
add_action('init', 'bixie_library_register_types');

function bixie_sanitize_images($value): array {
    if (!is_array($value)) { return []; }
    $result = [];
    foreach (array_slice($value, 0, 12) as $entry) {
        if (!is_array($entry) || empty($entry['id'])) { continue; }
        $id = absint($entry['id']);
        if (!wp_attachment_is_image($id)) { continue; }
        $angle = sanitize_key($entry['angle'] ?? 'reference');
        if (!in_array($angle, ['front', 'side', 'back', 'detail', 'reference', 'triptych'], true)) { $angle = 'reference'; }
        $result[] = ['id' => $id, 'angle' => $angle, 'caption' => sanitize_text_field($entry['caption'] ?? '')];
    }
    return $result;
}

function bixie_get_package_attachment(string $key): int {
    $posts = get_posts(['post_type' => 'attachment', 'post_status' => 'inherit', 'posts_per_page' => 1, 'fields' => 'ids', 'meta_key' => '_bixie_asset_key', 'meta_value' => sanitize_text_field($key)]);
    return $posts ? (int) $posts[0] : 0;
}

function bixie_original_source_path(int $id): string {
    $source = (string) get_post_meta($id, '_bixie_original_source_file', true); $delivery = (string) get_post_meta($id, '_bixie_delivery_file', true);
    if ($source && $delivery === get_attached_file($id) && is_file($source)) { return $source; }
    return (string) (wp_get_original_image_path($id) ?: get_attached_file($id));
}
function bixie_original_source_url(int $id): string {
    $source = (string) get_post_meta($id, '_bixie_original_source_file', true);
    if ($source && bixie_original_source_path($id) === $source) { return (string) get_post_meta($id, '_bixie_original_source_url', true); }
    return (string) (wp_get_original_image_url($id) ?: wp_get_attachment_url($id));
}

function bixie_get_look_images(int $post_id): array {
    $images = [];
    $entries = get_post_meta($post_id, 'bixie_images', true);
    foreach (is_array($entries) ? $entries : [] as $entry) {
        $id = absint($entry['id'] ?? 0);
        if (!$id || !wp_attachment_is_image($id)) { continue; }
        $source = wp_get_attachment_image_src($id, 'full');
        if (!$source) { continue; }
        $original_path = bixie_original_source_path($id); $original_size = $original_path && is_file($original_path) ? wp_getimagesize($original_path) : false;
        $images[] = [
            'id' => $id, 'angle' => sanitize_key($entry['angle'] ?? 'reference'),
            'url' => $source[0], 'originalUrl' => bixie_original_source_url($id) ?: $source[0],
            'width' => $source[1], 'height' => $source[2],
            'originalWidth' => $original_size[0] ?? $source[1],
            'originalHeight' => $original_size[1] ?? $source[2],
            'thumbnailUrl' => wp_get_attachment_image_url($id, 'medium_large') ?: $source[0],
            'thumbnailSrcset' => wp_get_attachment_image_srcset($id, 'medium_large') ?: '',
            'thumbnailSizes' => '(max-width: 600px) 90vw, (max-width: 1000px) 44vw, 28vw',
            'alt' => (string) get_post_meta($id, '_wp_attachment_image_alt', true),
            'caption' => sanitize_text_field($entry['caption'] ?? ''),
        ];
    }
    if (!$images && has_post_thumbnail($post_id)) {
        $id = get_post_thumbnail_id($post_id);
        $source = wp_get_attachment_image_src($id, 'full');
        if ($source) { $images[] = ['id' => $id, 'angle' => 'reference', 'url' => $source[0], 'originalUrl' => wp_get_original_image_url($id) ?: $source[0], 'thumbnailUrl' => wp_get_attachment_image_url($id, 'medium_large') ?: $source[0], 'thumbnailSrcset' => wp_get_attachment_image_srcset($id, 'medium_large') ?: '', 'thumbnailSizes' => '(max-width: 600px) 90vw, 28vw', 'width' => $source[1], 'height' => $source[2], 'alt' => (string) get_post_meta($id, '_wp_attachment_image_alt', true), 'caption' => '']; }
    }
    $order = ['front' => 0, 'side' => 1, 'back' => 2, 'detail' => 3, 'reference' => 4, 'triptych' => 5]; usort($images, static fn($a, $b) => ($order[$a['angle']] ?? 6) <=> ($order[$b['angle']] ?? 6));
    return $images;
}

function bixie_get_look_data(int $post_id): array {
    $post = get_post($post_id);
    if (!$post || $post->post_type !== 'bixie_look') { return []; }
    $images = bixie_get_look_images($post_id);
    $data = [
        'id' => $post_id, 'key' => (string) get_post_meta($post_id, '_bixie_import_key', true),
        'title' => html_entity_decode(wp_strip_all_tags(get_the_title($post)), ENT_QUOTES, get_bloginfo('charset')),
        'url' => get_permalink($post), 'excerpt' => wp_strip_all_tags($post->post_excerpt),
        'images' => $images, 'image' => $images[0] ?? null,
        'ai_concept' => (bool) get_post_meta($post_id, 'bixie_ai_concept', true),
    ];
    foreach (['texture', 'length', 'fringe', 'colour', 'density', 'strand', 'finish', 'age_reference', 'face_reference', 'primary_collection', 'maintenance', 'styling'] as $field) { $data[$field] = (string) get_post_meta($post_id, 'bixie_' . $field, true); }
    $terms = get_the_terms($post_id, 'bixie_collection');
    $data['collections'] = is_array($terms) ? array_map(static fn($term) => ['id' => $term->term_id, 'slug' => $term->slug, 'name' => $term->name, 'url' => bixie_get_collection_url($term)], $terms) : [];
    return $data;
}

function bixie_get_collection_url($term): string {
    $term = is_object($term) ? $term : get_term($term, 'bixie_collection');
    if (!$term || is_wp_error($term)) { return ''; }
    $page_id = (int) get_term_meta($term->term_id, 'bixie_page_id', true);
    if ($page_id && get_post_status($page_id) === 'publish') { return get_permalink($page_id); }
    return home_url('/look-collection/' . $term->slug . '/');
}

add_filter('term_link', static function($link, $term, $taxonomy) {
    if ($taxonomy !== 'bixie_collection') { return $link; }
    $page_id = (int) get_term_meta($term->term_id, 'bixie_page_id', true);
    return $page_id && get_post_status($page_id) === 'publish' ? get_permalink($page_id) : $link;
}, 10, 3);
add_action('template_redirect', static function(): void {
    if (!is_tax('bixie_collection')) { return; }
    $term = get_queried_object();
    $page_id = (int) get_term_meta($term->term_id, 'bixie_page_id', true);
    if ($page_id && get_post_status($page_id) === 'publish') { wp_safe_redirect(get_permalink($page_id), 301); exit; }
});
add_filter('wp_sitemaps_taxonomies', static function(array $taxonomies): array { unset($taxonomies['bixie_collection']); return $taxonomies; });

function bixie_invalidate_catalog(): void { delete_transient('bixie_catalog_facets'); }
add_action('save_post_bixie_look', 'bixie_invalidate_catalog');
add_action('deleted_post', static function($id, $post): void { if (in_array($post->post_type, ['bixie_look', 'attachment'], true)) { bixie_invalidate_catalog(); } }, 10, 2);
add_action('trashed_post', static function($id): void { if (in_array(get_post_type($id), ['bixie_look', 'attachment'], true)) { bixie_invalidate_catalog(); } });
add_action('set_object_terms', static function($id, $terms, $ids, $taxonomy): void { if ($taxonomy === 'bixie_collection') { bixie_invalidate_catalog(); } }, 10, 4);
foreach (['updated_post_meta', 'added_post_meta', 'deleted_post_meta'] as $hook) { add_action($hook, static function($meta_id, $post_id): void { if (in_array(get_post_type($post_id), ['bixie_look', 'attachment'], true)) { bixie_invalidate_catalog(); } }, 10, 2); }

function bixie_library_frontend_assets(): void {
    wp_enqueue_style('bixie-library', BIXIE_LIBRARY_URL . 'assets/frontend.css', [], BIXIE_LIBRARY_VERSION);
    wp_enqueue_script('bixie-library', BIXIE_LIBRARY_URL . 'assets/frontend.js', [], BIXIE_LIBRARY_VERSION, true);
    wp_add_inline_script('bixie-library', 'window.BixieLibrary=' . wp_json_encode(['restUrl' => rest_url('bixie/v1/looks'), 'lookUrl' => rest_url('bixie/v1/looks/'), 'locale' => get_locale()]) . ';', 'before');
}
add_action('wp_enqueue_scripts', 'bixie_library_frontend_assets');

require_once BIXIE_LIBRARY_DIR . 'includes/publication.php';
require_once BIXIE_LIBRARY_DIR . 'includes/relationships.php';
require_once BIXIE_LIBRARY_DIR . 'includes/blocks.php';
require_once BIXIE_LIBRARY_DIR . 'includes/settings.php';
require_once BIXIE_LIBRARY_DIR . 'includes/bundles.php';
require_once BIXIE_LIBRARY_DIR . 'includes/importer.php';
require_once BIXIE_LIBRARY_DIR . 'includes/schema.php';

register_activation_hook(__FILE__, static function(): void { bixie_library_register_types(); flush_rewrite_rules(false); });
register_deactivation_hook(__FILE__, static function(): void { flush_rewrite_rules(false); });

add_action('enqueue_block_editor_assets', static function(): void {
    wp_enqueue_script('bixie-library-editor', BIXIE_LIBRARY_URL . 'assets/editor.js', ['wp-blocks', 'wp-element', 'wp-components', 'wp-block-editor', 'wp-server-side-render', 'wp-edit-post', 'wp-data', 'wp-plugins', 'wp-api-fetch'], BIXIE_LIBRARY_VERSION, true);
});
