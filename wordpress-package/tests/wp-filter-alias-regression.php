<?php
/** Actual SQL/REST facet regression using only the retained synthetic code fixtures. */
if (PHP_SAPI !== 'cli' || empty($argv[1])) { exit(2); }
$_SERVER['HTTP_HOST'] = '127.0.0.1:8766'; $_SERVER['SERVER_NAME'] = '127.0.0.1'; $_SERVER['REQUEST_URI'] = '/';
require $argv[1];
if (wp_get_environment_type() !== 'local' || (int) get_option('blog_public') !== 0 || !function_exists('bixie_public_filter_value')) { exit(2); }
$fixtures = get_option('bixie_qa_fixture_state', []);
$ids = array_slice((array) ($fixtures['looks'] ?? []), 0, 3);
if (count($ids) !== 3) { exit(2); }
$snapshot = []; $checks = []; $failure = null;
function alias_check(string $name, bool $passed): void { global $checks; $checks[$name] = $passed; if (!$passed) { throw new RuntimeException($name); } }
function alias_ids(array $parameters): array { $ids = array_map(static fn($item) => (int) $item['id'], bixie_query_looks($parameters)['items']); sort($ids); return $ids; }
try {
    foreach ($ids as $id) {
        if (!get_post_meta($id, '_bixie_qa_fixture', true) || !bixie_check_look($id)['complete'] || get_post_status($id) !== 'publish') { throw new RuntimeException('Only complete, published, explicitly synthetic fixtures may be used.'); }
        foreach (['bixie_texture', 'bixie_fringe', 'bixie_colour'] as $key) { $snapshot[$id][$key] = get_post_meta($id, $key, false); }
    }
    $texture = 'qa-filter-alias-' . str_replace('-', '', wp_generate_uuid4());
    foreach ($ids as $index => $id) {
        update_post_meta($id, 'bixie_texture', $texture);
        update_post_meta($id, 'bixie_fringe', ['none', 'no-bangs', 'curtain'][$index]);
        update_post_meta($id, 'bixie_colour', ['dark', 'black', 'silver'][$index]);
    }
    bixie_invalidate_catalog();
    $pair = [$ids[0], $ids[1]]; sort($pair);
    $all = $ids; sort($all);
    foreach (['none', 'no-bangs', 'no bangs'] as $value) { alias_check('Fringe ' . $value . ' returns both stored aliases', alias_ids(['texture' => $texture, 'fringe' => $value]) === $pair); }
    foreach (['dark', 'black'] as $value) { alias_check('Colour ' . $value . ' returns both stored aliases', alias_ids(['texture' => $texture, 'colour' => $value]) === $pair); }
    alias_check('Combined aliases retain intersection', alias_ids(['texture' => $texture, 'fringe' => 'none', 'colour' => 'black']) === $pair);
    alias_check('Unrelated fringe remains an exact filter', alias_ids(['texture' => $texture, 'fringe' => 'curtain']) === [$ids[2]]);
    alias_check('Unrelated colour remains an exact filter', alias_ids(['texture' => $texture, 'colour' => 'silver']) === [$ids[2]]);
    alias_check('Other facet values remain unchanged', alias_ids(['texture' => $texture]) === $all);
    $request = new WP_REST_Request('GET', '/bixie/v1/looks'); $request->set_param('texture', $texture); $request->set_param('fringe', 'none');
    $response = rest_do_request($request); $rest_ids = array_map(static fn($item) => (int) $item['id'], $response->get_data()['items'] ?? []); sort($rest_ids);
    alias_check('Public REST uses the same alias SQL', $response->get_status() === 200 && $rest_ids === $pair);
    $facets = bixie_catalog_facets();
    alias_check('Live facets expose one no-bangs choice', in_array('none', $facets['fringe'], true) && !array_intersect(['no-bangs', 'no bangs'], $facets['fringe']));
    alias_check('Live facets expose one dark choice', in_array('dark', $facets['colour'], true) && !in_array('black', $facets['colour'], true));
    set_transient('bixie_catalog_facets', ['fringe' => ['none', 'no-bangs', 'no bangs', 'curtain'], 'colour' => ['dark', 'black', 'silver'], 'texture' => [$texture]], HOUR_IN_SECONDS);
    $cached = bixie_catalog_facets();
    alias_check('Old cached choices normalize without stale aliases', $cached['fringe'] === ['none', 'curtain'] && $cached['colour'] === ['dark', 'silver']);
    alias_check('Querying does not rewrite owner metadata', get_post_meta($ids[1], 'bixie_fringe', true) === 'no-bangs' && get_post_meta($ids[1], 'bixie_colour', true) === 'black');
} catch (Throwable $error) { $failure = $error->getMessage(); }
finally {
    foreach ($snapshot as $id => $fields) { foreach ($fields as $key => $values) { delete_post_meta($id, $key); foreach ($values as $value) { add_post_meta($id, $key, $value); } } }
    bixie_invalidate_catalog();
}
$restored = true;
foreach ($snapshot as $id => $fields) { foreach ($fields as $key => $values) { $restored = $restored && get_post_meta($id, $key, false) === $values; } }
$checks['Exact original fixture metadata restored'] = $restored;
$checks['No source or publication gate weakened'] = count(array_filter($ids, static fn($id) => get_post_status($id) === 'publish' && bixie_check_look($id)['complete'])) === 3 && absint(bixie_requirements()['minimum_native_long_edge']) === 1024;
$report = ['passed' => !$failure && !in_array(false, $checks, true), 'check_count' => count($checks), 'checks' => $checks, 'failure' => $failure, 'scope' => 'Actual WordPress SQL, public REST and live/cached facets with explicitly synthetic software fixtures on the older local noindex site. Exact fixture metadata restored; no production photographs or publication requirements changed.'];
file_put_contents(__DIR__ . '/wp-filter-alias-report.json', wp_json_encode($report, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES) . "\n");
echo wp_json_encode($report, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES) . "\n";
exit($report['passed'] ? 0 : 1);
