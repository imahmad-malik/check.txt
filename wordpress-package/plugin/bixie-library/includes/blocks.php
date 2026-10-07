<?php
if (!defined('ABSPATH')) { exit; }

function bixie_catalog_facets(): array {
    $cached = get_transient('bixie_catalog_facets');
    if (is_array($cached)) { return $cached; }
    global $wpdb; $facets = [];
    foreach (['texture', 'length', 'fringe', 'colour'] as $field) {
        $values = $wpdb->get_col($wpdb->prepare("SELECT DISTINCT m.meta_value FROM {$wpdb->postmeta} m INNER JOIN {$wpdb->posts} p ON p.ID=m.post_id INNER JOIN {$wpdb->postmeta} c ON c.post_id=p.ID AND c.meta_key='_bixie_record_complete' AND c.meta_value='1' WHERE p.post_type='bixie_look' AND p.post_status='publish' AND m.meta_key=%s AND m.meta_value<>'' ORDER BY m.meta_value LIMIT 100", 'bixie_' . $field));
        $facets[$field] = array_values(array_map('sanitize_text_field', $values));
    }
    set_transient('bixie_catalog_facets', $facets, HOUR_IN_SECONDS);
    return $facets;
}

function bixie_query_looks(array $parameters = []): array {
    $page = max(1, absint($parameters['page'] ?? 1));
    $per_page = max(1, min(48, absint($parameters['per_page'] ?? 12)));
    $args = ['post_type' => 'bixie_look', 'post_status' => 'publish', 'posts_per_page' => $per_page, 'paged' => $page, 'ignore_sticky_posts' => true, 'meta_query' => [['key' => '_bixie_record_complete', 'value' => '1']]];
    if (!empty($parameters['q'])) { $text = sanitize_text_field($parameters['q']); $args['s'] = function_exists('mb_substr') ? mb_substr($text, 0, 120) : substr($text, 0, 120); }
    foreach (['texture', 'length', 'fringe', 'colour'] as $field) { if (!empty($parameters[$field])) { $args['meta_query'][] = ['key' => 'bixie_' . $field, 'value' => sanitize_text_field($parameters[$field])]; } }
    if (!empty($parameters['collection'])) { $slug = sanitize_title($parameters['collection']); $args['tax_query'] = [['taxonomy' => 'bixie_collection', 'field' => 'slug', 'terms' => $slug]]; if (!bixie_requirements()['allow_source_reuse_between_primary_collections']) { $args['meta_query'][] = ['key' => 'bixie_primary_collection', 'value' => $slug]; } }
    if (!empty($parameters['exclude'])) { $args['post__not_in'] = array_slice(array_values(array_filter(array_map('absint', is_array($parameters['exclude']) ? $parameters['exclude'] : explode(',', $parameters['exclude'])))), 0, 200); }
    $sort = sanitize_key($parameters['sort'] ?? 'curated');
    if (in_array($sort, ['title', 'az'], true)) { $args['orderby'] = 'title'; $args['order'] = 'ASC'; }
    elseif (in_array($sort, ['latest', 'newest'], true)) { $args['orderby'] = 'date'; $args['order'] = 'DESC'; }
    else { $args['orderby'] = ['menu_order' => 'ASC', 'ID' => 'ASC']; }
    $query = new WP_Query($args);
    return ['items' => array_values(array_filter(array_map(static fn($post) => bixie_get_look_data($post->ID), $query->posts))), 'total' => (int) $query->found_posts, 'pages' => (int) $query->max_num_pages, 'page' => $page];
}

add_action('rest_api_init', static function(): void {
    register_rest_route('bixie/v1', '/looks', [
        'methods' => WP_REST_Server::READABLE, 'permission_callback' => '__return_true',
        'args' => array_merge(array_fill_keys(['q', 'texture', 'length', 'fringe', 'colour', 'sort', 'collection', 'exclude'], ['type' => 'string', 'sanitize_callback' => 'sanitize_text_field']), ['page' => ['type' => 'integer', 'minimum' => 1, 'sanitize_callback' => 'absint'], 'per_page' => ['type' => 'integer', 'minimum' => 1, 'maximum' => 48, 'sanitize_callback' => 'absint']]),
        'callback' => static function(WP_REST_Request $request): WP_REST_Response { $response = rest_ensure_response(bixie_query_looks($request->get_params())); $response->header('Cache-Control', 'no-store'); return $response; },
    ]);
    register_rest_route('bixie/v1', '/looks/(?P<id>\d+)', [
        'methods' => WP_REST_Server::READABLE, 'permission_callback' => '__return_true',
        'args' => ['id' => ['type' => 'integer', 'sanitize_callback' => 'absint']],
        'callback' => static function(WP_REST_Request $request) {
            $id = absint($request['id']);
            if (get_post_type($id) !== 'bixie_look' || get_post_status($id) !== 'publish' || !bixie_check_look($id)['complete']) { return new WP_Error('bixie_not_found', __('This look is not publicly available.', 'bixie-library'), ['status' => 404]); }
            $response = rest_ensure_response(bixie_get_look_data($id)); $response->header('Cache-Control', 'no-store'); return $response;
        },
    ]);
});

function bixie_render_card(array $record, bool $show_angles = false): string {
    ob_start(); ?>
    <article class="bixie-look-card" data-look="<?php echo absint($record['id']); ?>">
      <?php if (!empty($record['image'])): ?><a href="<?php echo esc_url($record['url']); ?>" class="bixie-card-photo"><?php echo wp_get_attachment_image($record['image']['id'], 'medium_large', false, ['loading' => 'lazy', 'decoding' => 'async', 'sizes' => $record['image']['thumbnailSizes']]); ?></a><?php endif; ?>
      <?php if ($show_angles): ?><div class="bixie-card-angles"><?php foreach ($record['images'] as $image): if (!in_array($image['angle'], ['side', 'back'], true) || $image['id'] === ($record['image']['id'] ?? 0)) { continue; } ?><figure class="bixie-card-angle"><a class="bixie-detail-trigger" data-look="<?php echo absint($record['id']); ?>" data-angle="<?php echo esc_attr($image['angle']); ?>" href="<?php echo esc_url($record['url']); ?>"><?php echo wp_get_attachment_image($image['id'], 'medium', false, ['loading' => 'lazy', 'decoding' => 'async', 'sizes' => '(max-width: 600px) 42vw, 14vw']); ?></a><figcaption><?php echo esc_html(ucfirst($image['angle'])); ?></figcaption></figure><?php endforeach; ?></div><?php endif; ?>
      <h3><a href="<?php echo esc_url($record['url']); ?>"><?php echo esc_html($record['title']); ?></a></h3>
      <p><?php echo esc_html(implode(' · ', array_filter([$record['texture'], $record['length'], $record['fringe'], $record['colour']]))); ?></p>
      <div class="bixie-card-actions"><button type="button" class="bixie-save" data-look="<?php echo absint($record['id']); ?>" aria-pressed="false"><?php esc_html_e('Save look', 'bixie-library'); ?></button><a class="bixie-detail-trigger" href="<?php echo esc_url($record['url']); ?>" data-look="<?php echo absint($record['id']); ?>"><?php esc_html_e('See every available view', 'bixie-library'); ?></a></div>
    </article>
    <?php return (string) ob_get_clean();
}

function bixie_render_library(array $attributes = []): string {
    $parameters = ['per_page' => absint($attributes['perPage'] ?? 12), 'collection' => sanitize_title($attributes['collection'] ?? ''), 'page' => max(1, absint($_GET['bixie_page'] ?? 1))];
    $parameters['exclude'] = implode(',', array_slice(array_filter(array_map('absint', (array) ($attributes['excludeLookIds'] ?? []))), 0, 200));
    foreach (['q', 'texture', 'length', 'fringe', 'colour', 'sort'] as $field) { $parameters[$field] = isset($_GET[$field]) && is_scalar($_GET[$field]) ? sanitize_text_field(wp_unslash($_GET[$field])) : ''; }
    $results = bixie_query_looks($parameters); $facets = bixie_catalog_facets();
    $show_angles = array_key_exists('showViews', $attributes) ? (bool) $attributes['showViews'] : !empty($parameters['collection']);
    $uid = wp_unique_id('bixie-library-');
    $action = is_singular() ? get_permalink() : home_url('/looks/');
    ob_start(); ?>
    <section class="bixie-library" id="<?php echo esc_attr($uid); ?>" data-page="<?php echo absint($results['page']); ?>" data-size="<?php echo absint($parameters['per_page']); ?>" data-collection="<?php echo esc_attr($parameters['collection']); ?>" data-exclude="<?php echo esc_attr($parameters['exclude']); ?>" data-show-angles="<?php echo $show_angles ? 'true' : 'false'; ?>" aria-label="<?php esc_attr_e('Bixie hairstyle photo library', 'bixie-library'); ?>">
      <form class="bixie-filter-form" method="get" action="<?php echo esc_url($action); ?>">
        <?php if ($parameters['collection']): ?><input type="hidden" name="collection" value="<?php echo esc_attr($parameters['collection']); ?>"><?php endif; ?>
        <?php if ($parameters['exclude']): ?><input type="hidden" name="exclude" value="<?php echo esc_attr($parameters['exclude']); ?>"><?php endif; ?>
        <label for="<?php echo esc_attr($uid); ?>-search"><?php esc_html_e('Find a hairstyle', 'bixie-library'); ?><input id="<?php echo esc_attr($uid); ?>-search" type="search" name="q" maxlength="120" value="<?php echo esc_attr($parameters['q']); ?>" placeholder="<?php esc_attr_e('Search the real photo collection', 'bixie-library'); ?>"></label>
        <?php foreach (['texture' => 'Texture', 'length' => 'Length', 'fringe' => 'Fringe', 'colour' => 'Colour'] as $field => $label): ?>
          <label for="<?php echo esc_attr($uid . '-' . $field); ?>"><?php echo esc_html($label); ?><select id="<?php echo esc_attr($uid . '-' . $field); ?>" name="<?php echo esc_attr($field); ?>"><option value=""><?php esc_html_e('All available', 'bixie-library'); ?></option><?php foreach ($facets[$field] as $value): ?><option value="<?php echo esc_attr($value); ?>" <?php selected($parameters[$field], $value); ?>><?php echo esc_html(ucwords(str_replace('-', ' ', $value))); ?></option><?php endforeach; ?></select></label>
        <?php endforeach; ?>
        <label for="<?php echo esc_attr($uid); ?>-sort"><?php esc_html_e('Order', 'bixie-library'); ?><select id="<?php echo esc_attr($uid); ?>-sort" name="sort"><?php foreach (['curated' => 'Curated', 'title' => 'A–Z', 'latest' => 'Newest'] as $value => $label): ?><option value="<?php echo esc_attr($value); ?>" <?php selected($parameters['sort'] ?: 'curated', $value); ?>><?php echo esc_html($label); ?></option><?php endforeach; ?></select></label>
        <button type="submit"><?php esc_html_e('Apply filters', 'bixie-library'); ?></button><a class="bixie-clear-filters" href="<?php echo esc_url($action); ?>"><?php esc_html_e('Clear filters', 'bixie-library'); ?></a>
      </form>
      <div class="bixie-library-tools"><button type="button" class="bixie-open-saved"><?php esc_html_e('Saved looks', 'bixie-library'); ?> <span class="bixie-saved-count">0</span></button><button type="button" class="bixie-open-compare"><?php esc_html_e('Compare saved looks', 'bixie-library'); ?></button><button type="button" class="bixie-print-saved"><?php esc_html_e('Make a salon sheet', 'bixie-library'); ?></button></div>
      <p class="bixie-result-status" role="status" aria-live="polite"><?php echo esc_html(sprintf(_n('%d available look', '%d available looks', $results['total'], 'bixie-library'), $results['total'])); ?></p>
      <div class="bixie-results"><?php foreach ($results['items'] as $record) { echo bixie_render_card($record, $show_angles); } if (!$results['items']) { echo '<p class="bixie-empty">' . esc_html__('No complete reviewed look matches these choices yet. Clear a filter to explore the available collection.', 'bixie-library') . '</p>'; } ?></div>
      <?php $link_parameters = $parameters; unset($link_parameters['page'], $link_parameters['per_page']); ?><nav class="bixie-pagination" aria-label="<?php esc_attr_e('Photo library pages', 'bixie-library'); ?>"><?php for ($page = 1; $page <= $results['pages']; $page++): ?><a href="<?php echo esc_url(add_query_arg(array_merge(array_filter($link_parameters), ['bixie_page' => $page]), $action)); ?>" data-page="<?php echo absint($page); ?>" <?php if ($page === $results['page']) { echo 'aria-current="page"'; } ?>><?php echo absint($page); ?></a><?php endfor; ?></nav>
      <script type="application/json" class="bixie-initial-data"><?php echo wp_json_encode($results, JSON_HEX_TAG | JSON_HEX_AMP | JSON_HEX_APOS | JSON_HEX_QUOT); ?></script>
    </section>
    <?php return (string) ob_get_clean();
}

function bixie_render_look_meta(array $attributes = [], string $content = '', $block = null): string {
    $id = absint($attributes['lookId'] ?? 0) ?: absint($block->context['postId'] ?? get_the_ID());
    $editor_preview = (is_admin() || (defined('REST_REQUEST') && REST_REQUEST) || is_preview()) && current_user_can('edit_post', $id);
    if (!$editor_preview && (get_post_status($id) !== 'publish' || !bixie_check_look($id)['complete'])) { return ''; }
    $record = bixie_get_look_data($id); if (!$record) { return ''; }
    ob_start(); ?>
    <section class="bixie-look-information" aria-label="<?php esc_attr_e('Hairstyle reference details', 'bixie-library'); ?>">
      <?php if (!empty($attributes['showImages'])): ?><div class="bixie-look-photos"><?php foreach ($record['images'] as $image): ?><figure><img src="<?php echo esc_url($image['url']); ?>" alt="<?php echo esc_attr($image['alt']); ?>" width="<?php echo absint($image['width']); ?>" height="<?php echo absint($image['height']); ?>" loading="lazy"><figcaption><?php echo esc_html(ucfirst($image['angle']) . ($image['caption'] ? ' · ' . $image['caption'] : '')); ?></figcaption></figure><?php endforeach; ?></div><?php endif; ?>
      <dl><?php foreach (['texture' => 'Texture', 'length' => 'Length', 'fringe' => 'Fringe', 'colour' => 'Colour'] as $key => $label): if (!$record[$key]) { continue; } ?><dt><?php echo esc_html($label); ?></dt><dd><?php echo esc_html(ucwords(str_replace('-', ' ', $record[$key]))); ?></dd><?php endforeach; ?></dl>
      <?php foreach (['styling' => 'Styling conversation', 'maintenance' => 'Maintenance'] as $field => $label): if ($record[$field]): ?><h3><?php echo esc_html($label); ?></h3><p><?php echo esc_html($record[$field]); ?></p><?php endif; endforeach; ?>
      <?php if ($record['ai_concept']): ?><p class="bixie-image-disclosure"><?php esc_html_e('AI-created hairstyle concept featuring a fictional adult. A reference for discussion, not a verified salon result.', 'bixie-library'); ?></p><?php endif; ?>
      <button type="button" class="bixie-save" data-look="<?php echo $id; ?>" aria-pressed="false"><?php esc_html_e('Save this look', 'bixie-library'); ?></button><button type="button" class="bixie-open-saved"><?php esc_html_e('Open saved looks', 'bixie-library'); ?></button>
    </section>
    <?php return (string) ob_get_clean();
}

function bixie_render_saved(): string {
    return '<section class="bixie-saved-page"><p class="bixie-saved-page-status" role="status" aria-live="polite">' . esc_html__('Your shortlist is kept in this browser; no account or tracking is used.', 'bixie-library') . '</p><div class="bixie-saved-items"><p>' . esc_html__('Save looks from the photo library to build your shortlist. JavaScript and browser storage provide saved looks; if storage is unavailable the list lasts for this visit.', 'bixie-library') . '</p></div><div class="bixie-library-tools"><button class="bixie-open-saved" type="button">' . esc_html__('Choose saved looks', 'bixie-library') . ' <span class="bixie-saved-count">0</span></button><button class="bixie-open-compare" type="button">' . esc_html__('Compare', 'bixie-library') . '</button><button class="bixie-print-saved" type="button">' . esc_html__('Print salon sheet', 'bixie-library') . '</button></div></section>';
}

function bixie_render_finder(): string {
    $facets = bixie_catalog_facets(); ob_start(); ?>
    <form class="bixie-finder-form" action="<?php echo esc_url(home_url('/looks/')); ?>" method="get">
    <?php foreach (['texture' => 'Texture preference', 'length' => 'Length preference', 'fringe' => 'Fringe preference'] as $field => $label): ?><fieldset><legend><?php echo esc_html($label); ?></legend><label><input type="radio" name="<?php echo esc_attr($field); ?>" value="" checked> <?php esc_html_e('Open to all', 'bixie-library'); ?></label><?php foreach ($facets[$field] as $value): ?><label><input type="radio" name="<?php echo esc_attr($field); ?>" value="<?php echo esc_attr($value); ?>"> <?php echo esc_html(ucwords(str_replace('-', ' ', $value))); ?></label><?php endforeach; ?></fieldset><?php endforeach; ?>
    <button type="submit"><?php esc_html_e('Explore matching photo references', 'bixie-library'); ?></button><p><?php esc_html_e('A browsing aid based on your preferences, not a suitability or hair-health assessment.', 'bixie-library'); ?></p></form>
    <?php return (string) ob_get_clean();
}

add_action('init', static function(): void {
    register_block_type('bixie/library', ['api_version' => 3, 'attributes' => ['collection' => ['type' => 'string', 'default' => ''], 'perPage' => ['type' => 'integer', 'default' => 12], 'showViews' => ['type' => 'boolean'], 'excludeLookIds' => ['type' => 'array', 'items' => ['type' => 'integer'], 'default' => []]], 'render_callback' => 'bixie_render_library']);
    register_block_type('bixie/look-meta', ['api_version' => 3, 'uses_context' => ['postId', 'postType'], 'attributes' => ['lookId' => ['type' => 'integer', 'default' => 0], 'showImages' => ['type' => 'boolean', 'default' => false]], 'render_callback' => 'bixie_render_look_meta']);
    register_block_type('bixie/saved-looks', ['api_version' => 3, 'render_callback' => 'bixie_render_saved']);
    register_block_type('bixie/finder', ['api_version' => 3, 'render_callback' => 'bixie_render_finder']);
});
