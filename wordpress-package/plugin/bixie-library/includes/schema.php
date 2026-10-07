<?php
if (!defined('ABSPATH')) { exit; }

function bixie_has_external_schema(): bool {
    $present = defined('WPSEO_VERSION') || function_exists('YoastSEO') || defined('RANK_MATH_VERSION') || class_exists('RankMath') || defined('AIOSEO_VERSION') || function_exists('aioseo') || defined('SEOPRESS_VERSION') || function_exists('seopress_get_service');
    return (bool) apply_filters('bixie_external_schema_provider', $present);
}

function bixie_image_schema(array $image): array {
    return ['@type' => 'ImageObject', 'contentUrl' => $image['originalUrl'] ?? $image['url'], 'thumbnailUrl' => $image['thumbnailUrl'] ?? $image['url'], 'caption' => ($image['caption'] ?? '') ?: ($image['alt'] ?? ''), 'width' => $image['originalWidth'] ?? $image['width'], 'height' => $image['originalHeight'] ?? $image['height']];
}

function bixie_attachment_schema(int $id): array {
    $metadata = wp_get_attachment_metadata($id); $source = bixie_original_source_path($id); $size = $source && is_file($source) ? wp_getimagesize($source) : false;
    return bixie_image_schema(['url' => wp_get_attachment_url($id), 'originalUrl' => bixie_original_source_url($id), 'thumbnailUrl' => wp_get_attachment_image_url($id, 'medium_large') ?: wp_get_attachment_url($id), 'caption' => wp_get_attachment_caption($id), 'alt' => get_post_meta($id, '_wp_attachment_image_alt', true), 'width' => $size[0] ?? $metadata['width'] ?? 0, 'height' => $size[1] ?? $metadata['height'] ?? 0]);
}

function bixie_breadcrumb_schema(int $post_id): array {
    $items = [['@type' => 'ListItem', 'position' => 1, 'name' => get_bloginfo('name'), 'item' => home_url('/')]];
    foreach (array_reverse(get_post_ancestors($post_id)) as $ancestor) { if (get_post_status($ancestor) === 'publish') { $items[] = ['@type' => 'ListItem', 'position' => count($items) + 1, 'name' => get_the_title($ancestor), 'item' => get_permalink($ancestor)]; } }
    if (get_post_type($post_id) === 'bixie_look') { $hub = get_page_by_path('looks'); if ($hub && $hub->post_status === 'publish') { $items[] = ['@type' => 'ListItem', 'position' => count($items) + 1, 'name' => get_the_title($hub), 'item' => get_permalink($hub)]; } }
    $items[] = ['@type' => 'ListItem', 'position' => count($items) + 1, 'name' => get_the_title($post_id), 'item' => get_permalink($post_id)];
    return ['@type' => 'BreadcrumbList', 'itemListElement' => $items];
}

function bixie_library_attributes(array $blocks): ?array {
    foreach ($blocks as $block) { if (($block['blockName'] ?? '') === 'bixie/library') { return $block['attrs'] ?? []; } $child = bixie_library_attributes($block['innerBlocks'] ?? []); if ($child !== null) { return $child; } }
    return null;
}

/** Scope directives to the actual package library/tools and WordPress search. */
function bixie_should_noindex(): bool {
    if (is_search()) { return true; }
    if (!is_singular()) { return false; }
    $post = get_queried_object(); if (!$post instanceof WP_Post) { return false; }
    if (get_post_meta($post->ID, '_bixie_indexability', true) === 'noindex') { return true; }
    if (has_block('bixie/library', $post->post_content)) {
        foreach (['q', 'texture', 'length', 'fringe', 'colour', 'collection', 'sort', 'exclude'] as $field) { if (isset($_GET[$field]) && is_scalar($_GET[$field]) && (string) $_GET[$field] !== '' && !($field === 'sort' && $_GET[$field] === 'curated')) { return true; } }
    }
    return false;
}

function bixie_canonical_url(string $url): string {
    if (!is_singular()) { return $url; }
    $post = get_queried_object(); if (!$post instanceof WP_Post || !has_block('bixie/library', $post->post_content)) { return $url; }
    if ($url === '' && bixie_should_noindex()) { return ''; }
    $base = get_permalink($post); $page = isset($_GET['bixie_page']) && is_scalar($_GET['bixie_page']) ? absint($_GET['bixie_page']) : 1;
    return !bixie_should_noindex() && $page > 1 ? add_query_arg('bixie_page', $page, $base) : $base;
}

add_action('wp_head', static function(): void {
    if (!is_singular() || is_preview() || bixie_should_noindex() || get_option('bixie_schema_disabled', false) || bixie_has_external_schema()) { return; }
    $post = get_queried_object(); if (!$post instanceof WP_Post || $post->post_status !== 'publish') { return; }
    $graph = []; $publisher = ['@type' => 'Organization', '@id' => home_url('/') . '#publisher', 'name' => get_bloginfo('name'), 'url' => home_url('/')];
    $dates = ['datePublished' => get_post_time(DATE_W3C, true, $post), 'dateModified' => get_post_modified_time(DATE_W3C, true, $post)];
    if ($post->post_type === 'bixie_look' && bixie_check_look($post->ID)['complete']) {
        $record = bixie_get_look_data($post->ID);
        $graph[] = array_merge(['@type' => 'CreativeWork', '@id' => $record['url'] . '#look', 'name' => $record['title'], 'url' => $record['url'], 'description' => $record['excerpt'], 'publisher' => ['@id' => $publisher['@id']], 'image' => array_map('bixie_image_schema', $record['images'])], $dates);
        $graph[] = bixie_breadcrumb_schema($post->ID);
    } elseif ($post->post_type === 'page') {
        if (is_front_page() || get_post_meta($post->ID, '_bixie_is_front_page', true)) {
            if (!bixie_check_home($post->ID)['complete']) { return; }
            $graph[] = ['@type' => 'WebSite', '@id' => home_url('/') . '#website', 'url' => home_url('/'), 'name' => get_bloginfo('name'), 'description' => get_bloginfo('description'), 'publisher' => ['@id' => $publisher['@id']]];
            $graph[] = array_merge(['@type' => 'WebPage', '@id' => get_permalink($post) . '#webpage', 'url' => get_permalink($post), 'name' => get_the_title($post), 'isPartOf' => ['@id' => home_url('/') . '#website']], $dates);
        }
        if (get_post_meta($post->ID, '_bixie_content_type', true) === 'guide' && bixie_check_page_photos($post->ID)['complete']) {
            $images = array_values(array_unique(bixie_native_photo_ids(parse_blocks($post->post_content))));
            $graph[] = array_merge(['@type' => 'Article', '@id' => get_permalink($post) . '#article', 'headline' => get_the_title($post), 'url' => get_permalink($post), 'mainEntityOfPage' => get_permalink($post), 'description' => get_post_meta($post->ID, '_bixie_meta_description', true), 'publisher' => ['@id' => $publisher['@id']], 'image' => array_map('bixie_attachment_schema', $images)], $dates);
            $graph[] = bixie_breadcrumb_schema($post->ID);
        }
        $attributes = bixie_library_attributes(parse_blocks($post->post_content));
        if ($attributes !== null) {
            $parameters = ['per_page' => $attributes['perPage'] ?? 12, 'page' => isset($_GET['bixie_page']) && is_scalar($_GET['bixie_page']) ? max(1, absint($_GET['bixie_page'])) : 1, 'collection' => $attributes['collection'] ?? '', 'exclude' => $attributes['excludeLookIds'] ?? []];
            foreach (['q', 'texture', 'length', 'fringe', 'colour', 'sort'] as $field) { if (isset($_GET[$field]) && is_scalar($_GET[$field])) { $parameters[$field] = sanitize_text_field(wp_unslash($_GET[$field])); } }
            $results = bixie_query_looks($parameters); $parts = [];
            foreach ($results['items'] as $record) { $parts[] = ['@type' => 'CreativeWork', 'name' => $record['title'], 'url' => $record['url'], 'image' => array_map('bixie_image_schema', $record['images'])]; }
            if ($parts) { $graph[] = ['@type' => 'ImageGallery', '@id' => bixie_canonical_url(get_permalink($post)) . '#photo-library', 'name' => get_the_title($post), 'url' => bixie_canonical_url(get_permalink($post)), 'hasPart' => $parts]; if (!is_front_page()) { $graph[] = bixie_breadcrumb_schema($post->ID); } }
        }
    }
    if ($graph) { $graph[] = $publisher; echo '<script type="application/ld+json" class="bixie-structured-data">' . wp_json_encode(['@context' => 'https://schema.org', '@graph' => $graph], JSON_HEX_TAG | JSON_HEX_AMP | JSON_HEX_APOS | JSON_HEX_QUOT | JSON_UNESCAPED_SLASHES) . "</script>\n"; }
}, 30);

add_filter('wp_robots', static function(array $robots): array { if (bixie_should_noindex()) { $robots['noindex'] = true; unset($robots['index']); if (empty($robots['nofollow'])) { $robots['follow'] = true; } else { unset($robots['follow']); } } return $robots; }, 99);
add_action('template_redirect', static function(): void { if (bixie_should_noindex() && !headers_sent()) { header('X-Robots-Tag: noindex, ' . (get_option('blog_public') ? 'follow' : 'nofollow'), true); } }, 1);
add_filter('get_canonical_url', static fn(string $url): string => bixie_canonical_url($url), 99);

// Provider-owned JSON-LD/title/description remains theirs. Unknown providers can use the admin disable setting.
add_filter('wpseo_robots_array', static function($robots) { if (is_array($robots) && bixie_should_noindex()) { $robots['index'] = 'noindex'; if (($robots['follow'] ?? '') !== 'nofollow') { $robots['follow'] = 'follow'; } } return $robots; }, 99);
add_filter('wpseo_robots', static function($robots) { if (!is_string($robots) || !bixie_should_noindex()) { return $robots; } $parts = array_filter(array_map('trim', explode(',', $robots)), static fn($part) => !in_array($part, ['index', 'noindex'], true)); if (!in_array('follow', $parts, true) && !in_array('nofollow', $parts, true)) { $parts[] = 'follow'; } $parts[] = 'noindex'; return implode(', ', array_values($parts)); }, 99);
add_filter('rank_math/frontend/robots', static function($robots) { if (is_array($robots) && bixie_should_noindex()) { $robots['index'] = 'noindex'; if (($robots['follow'] ?? '') !== 'nofollow') { $robots['follow'] = 'follow'; } } return $robots; }, 99);
add_filter('aioseo_robots_meta', static function($robots) { if (is_array($robots) && bixie_should_noindex()) { unset($robots['index']); $robots['noindex'] = 'noindex'; } return $robots; }, 99);
foreach (['wpseo_canonical', 'rank_math/frontend/canonical', 'aioseo_canonical_url', 'seopress_titles_canonical'] as $hook) { add_filter($hook, static fn($url) => is_string($url) ? bixie_canonical_url($url) : $url, 99); }
add_filter('seopress_titles_robots_attrs', static function($robots) { if (is_array($robots) && bixie_should_noindex()) { $robots['noindex'] = 'noindex'; unset($robots['index']); } return $robots; }, 99);

add_filter('document_title_parts', static function(array $parts): array { if (is_singular() && !bixie_has_external_schema()) { $title = get_post_meta(get_queried_object_id(), '_bixie_seo_title', true); if ($title) { $parts['title'] = $title; } } return $parts; });
add_action('wp_head', static function(): void { if (!is_singular() || bixie_has_external_schema()) { return; } $description = get_post_meta(get_queried_object_id(), '_bixie_meta_description', true); if ($description) { echo '<meta name="description" content="' . esc_attr($description) . '">' . "\n"; } }, 5);
