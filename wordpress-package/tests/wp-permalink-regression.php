<?php
/** Exercise actual WordPress routing choices without changing owner content. */
if (PHP_SAPI !== 'cli' || empty($argv[1])) { exit(2); }
$_SERVER['HTTP_HOST'] = '127.0.0.1:8766';
$_SERVER['SERVER_NAME'] = '127.0.0.1';
$_SERVER['REQUEST_URI'] = '/';
require $argv[1];
if (wp_get_environment_type() !== 'local' || (int) get_option('blog_public') !== 0) { exit(2); }
$original = get_option('permalink_structure');
$ids = []; $checks = [];
function permalink_qa_check($name, $pass) { global $checks; $checks[$name] = (bool) $pass; }
function permalink_qa_href($html) { $tags = new WP_HTML_Tag_Processor($html); return $tags->next_tag('A') ? html_entity_decode((string) $tags->get_attribute('href'), ENT_QUOTES, 'UTF-8') : ''; }
try {
    $suffix = str_replace('-', '', wp_generate_uuid4());
    foreach (['parent', 'child', 'draft', 'ordinary'] as $kind) {
        $args = ['post_type' => 'page', 'post_status' => $kind === 'draft' ? 'draft' : 'publish', 'post_title' => 'Isolated permalink QA ' . $kind, 'post_name' => 'permalink-qa-' . $kind . '-' . $suffix];
        if ($kind !== 'ordinary') { $args['meta_input'] = ['_bixie_import_key' => 'permalink-qa-' . $kind . '-' . $suffix]; }
        if ($kind === 'child') { $args['post_parent'] = $ids['parent']; }
        $id = wp_insert_post($args, true);
        if (is_wp_error($id)) { throw new RuntimeException($id->get_error_message()); }
        $ids[$kind] = $id;
    }
    $path = '/permalink-qa-parent-' . $suffix . '/permalink-qa-child-' . $suffix . '/';
    $ordinary_url = home_url('/permalink-qa-ordinary-' . $suffix . '/');
    $draft_url = home_url('/permalink-qa-draft-' . $suffix . '/');
    foreach (['plain' => '', 'pretty' => '/%postname%/'] as $mode => $structure) {
        $wp_rewrite->set_permalink_structure($structure);
        $url = home_url($path . '?texture=curly#photos');
        $stored = bixie_editorial_paragraph('<a href="' . esc_url($url) . '">View the photographs</a>');
        $rendered = do_blocks($stored);
        $expected = add_query_arg('texture', 'curly', get_permalink($ids['child'])) . '#photos';
        permalink_qa_check($mode . 'NestedProjectLinkUsesActualPermalink', permalink_qa_href($rendered) === $expected);
        permalink_qa_check($mode . 'StoredNativeBlocksUnchanged', strpos($stored, esc_url($url)) !== false && get_post_field('post_content', $ids['child']) === '');
        permalink_qa_check($mode . 'OwnerPageLinkPreserved', permalink_qa_href(do_blocks(bixie_editorial_paragraph('<a href="' . esc_url($ordinary_url) . '">Owner page</a>'))) === $ordinary_url);
        $external = 'https://example.org' . $path;
        permalink_qa_check($mode . 'ExternalLinkPreserved', permalink_qa_href(do_blocks(bixie_editorial_paragraph('<a href="' . esc_url($external) . '">External page</a>'))) === $external);
        $draft_button = do_blocks(bixie_editorial_button('Draft', '/permalink-qa-draft-' . $suffix . '/'));
        permalink_qa_check($mode . 'DraftButtonHidden', !str_contains($draft_button, 'Draft') && !str_contains($draft_button, '<a') && !str_contains($draft_button, '<span'));
        $query_draft = add_query_arg('page_id', $ids['draft'], home_url('/'));
        permalink_qa_check($mode . 'PlainDraftQueryDetected', bixie_editorial_is_project_draft_url($query_draft));
        $query_child = add_query_arg(['page_id' => $ids['child'], 'colour' => 'dark'], home_url('/')) . '#views';
        permalink_qa_check($mode . 'QueryProjectLinkPreservesFiltersAndFragment', permalink_qa_href(do_blocks(bixie_editorial_paragraph('<a href="' . esc_url($query_child) . '">Query link</a>'))) === add_query_arg('colour', 'dark', get_permalink($ids['child'])) . '#views');
        permalink_qa_check($mode . 'PluginPageDestinationUsesActualPermalink', bixie_package_page_url('permalink-qa-child-' . $suffix, '/fallback/') === get_permalink($ids['child']));
        $routing_fields = bixie_get_form_route_fields(get_permalink($ids['child']));
        $route_values = []; $inputs = new WP_HTML_Tag_Processor($routing_fields);
        while ($inputs->next_tag('INPUT')) { $route_values[$inputs->get_attribute('name')] = $inputs->get_attribute('value'); }
        permalink_qa_check($mode . 'GETFormRetainsRequiredRoute', $mode === 'plain' ? ($route_values['page_id'] ?? '') === (string) $ids['child'] : !$route_values);
        if ($mode === 'plain') {
            $submitted = add_query_arg(array_merge($route_values, ['q' => 'bixie', 'texture' => 'curly']), home_url('/'));
            $response = wp_remote_get($submitted, ['timeout' => 20]);
            permalink_qa_check('PlainGETFilterSubmissionReachesActualPage', !is_wp_error($response) && wp_remote_retrieve_response_code($response) === 200 && str_contains(wp_remote_retrieve_body($response), 'Isolated permalink QA child'));
        }
    }
} finally {
    $wp_rewrite->set_permalink_structure($original);
    foreach ($ids as $id) { wp_delete_post($id, true); }
}
permalink_qa_check('OriginalPermalinkSettingRestored', get_option('permalink_structure') === $original);
permalink_qa_check('OnlyOwnTemporaryPagesRemoved', count(array_filter($ids, 'get_post')) === 0);
$report = ['passed' => !in_array(false, $checks, true), 'checks' => $checks, 'check_count' => count($checks), 'runtime' => ['wordpress' => get_bloginfo('version'), 'php' => PHP_VERSION], 'scope' => 'Actual WordPress block rendering and URL functions under plain and pretty permalink settings; settings and exact temporary pages restored.'];
file_put_contents(__DIR__ . '/wp-permalink-report.json', wp_json_encode($report, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES) . "\n");
echo wp_json_encode($report, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES) . "\n";
exit($report['passed'] ? 0 : 1);
