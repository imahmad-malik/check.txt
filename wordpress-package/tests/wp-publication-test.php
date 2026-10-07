<?php
/** Actual WordPress publication/relationship tests. Isolated synthetic fixtures only.
 * php wp-publication-test.php /path/to/wp-load.php
 * Never reads credentials; never adds source files or look records to a package.
 */
if (PHP_SAPI !== 'cli' || empty($argv[1])) { exit(2); }
$_SERVER['HTTP_HOST'] = '127.0.0.1:8766'; $_SERVER['SERVER_NAME'] = '127.0.0.1'; $_SERVER['REQUEST_URI'] = '/';
require $argv[1];
if (wp_get_environment_type() !== 'local' || (int) get_option('blog_public') !== 0 || !function_exists('bixie_check_page_photos')) { fwrite(STDERR, "Requires latest plugin in an isolated local noindex QA site.\n"); exit(2); }
$fixtures = get_option('bixie_qa_fixture_state', []); $looks = $fixtures['looks'] ?? [];
if (count($looks) !== 14) { fwrite(STDERR, "Requires the explicitly synthetic 14-look QA fixture set.\n"); exit(2); }
$original = end($looks); $entries = (array) get_post_meta($original, 'bixie_images', true); $front = absint($entries[0]['id']);
$original_status = get_post_status($original); $original_approval = get_post_meta($front, '_bixie_review_approved', true); $original_file = get_post_meta($front, '_wp_attached_file', true); $native = get_post_meta($front, '_bixie_native_verified', true);
$created_posts = []; $created_attachments = []; $created_files = []; $tests = []; $failure = null;
function qa_assert(string $name, bool $ok, array $detail = []): void { global $tests; $tests[] = ['name' => $name, 'passed' => $ok, 'detail' => $detail]; if (!$ok) { throw new RuntimeException($name); } }
function qa_call_page(array $record, array &$state): void { $method = new ReflectionMethod(Bixie_Importer::class, 'page'); $method->invokeArgs(null, [$record, &$state]); }
try {
    qa_assert('Accepted original-resolution and strict three-angle/no-upscaling gates', absint(bixie_requirements()['minimum_native_long_edge']) === 1024 && !empty(bixie_requirements()['no_upscaling']) && !empty(bixie_requirements()['require_complete_angles']));
    $content = '<!-- wp:paragraph --><p>ISOLATED synthetic code test, never a production hairstyle.</p><!-- /wp:paragraph -->'; foreach ($entries as $entry) { $content .= serialize_block(bixie_native_image_block($entry)); }
    $clone = wp_insert_post(wp_slash(['post_type' => 'bixie_look', 'post_title' => 'ISOLATED guide gate test', 'post_name' => 'isolated-guide-gate-look', 'post_status' => 'publish', 'post_content' => $content, 'meta_input' => ['_bixie_qa_fixture' => 1, '_bixie_import_key' => 'isolated-guide-gate-look', 'bixie_images' => $entries, 'bixie_primary_collection' => 'isolated-qa-fixtures', 'bixie_texture' => 'qa-temporary']]), true);
    if (is_wp_error($clone)) { throw new RuntimeException($clone->get_error_message()); } $created_posts[] = $clone;
    qa_assert('Complete source-backed same-primary code clone publishes', get_post_status($clone) === 'publish' && bixie_check_look($clone)['complete']);
    $record = ['key' => 'isolated-guide-gate-page', 'slug' => 'isolated-guide-gate-page', 'title' => 'ISOLATED native guide test', 'type' => 'guide', 'status' => 'publish', 'content' => '<!-- wp:paragraph --><p>ISOLATED synthetic reference test.</p><!-- /wp:paragraph --><!-- wp:paragraph --><p>Editable supporting text.</p><!-- /wp:paragraph -->', 'photo_set_requirements' => [['look_key' => 'isolated-guide-gate-look', 'angles' => ['front', 'side', 'back'], 'caption' => 'ISOLATED fixture views']], 'minimum_photos' => 3, 'photo_insert_after_block' => 1];
    $state = ['overwrite' => false, 'counts' => ['pages' => 0, 'skipped' => 0], 'log' => []]; qa_call_page($record, $state);
    $guide = get_posts(['post_type' => 'page', 'post_status' => ['publish','draft'], 'posts_per_page' => 1, 'fields' => 'ids', 'meta_key' => '_bixie_import_key', 'meta_value' => $record['key']])[0]; $created_posts[] = $guide; update_post_meta($guide, '_bixie_qa_fixture', 1);
    $guide_content = get_post_field('post_content', $guide); $blocks = parse_blocks($guide_content);
    qa_assert('Importer inserts actual editable three-angle gallery after opening paragraph', get_post_status($guide) === 'publish' && ($blocks[1]['blockName'] ?? '') === 'core/gallery' && count(bixie_native_photo_ids($blocks)) === 3 && bixie_check_page_photos($guide)['complete']);
    wp_update_post(wp_slash(['ID' => $guide, 'post_content' => $guide_content . '<!-- wp:paragraph --><p>OWNER EDIT PRESERVED</p><!-- /wp:paragraph -->'])); qa_call_page($record, $state);
    qa_assert('Guide reimport preserves owner block copy', str_contains(get_post_field('post_content', $guide), 'OWNER EDIT PRESERVED'));
    $guide_content = get_post_field('post_content', $guide);
    qa_assert('Facet cache contains current synthetic-only texture', in_array('qa-temporary', bixie_catalog_facets()['texture'], true));
    update_post_meta($front, '_bixie_review_approved', 0);
    qa_assert('Revoking attachment approval drafts all affected looks and guide', get_post_status($original) === 'draft' && get_post_status($clone) === 'draft' && get_post_status($guide) === 'draft' && get_post_meta($clone, '_bixie_record_complete', true) === '0');
    qa_assert('Source revocation invalidates affected catalog facets', !in_array('qa-temporary', bixie_catalog_facets()['texture'], true));
    $response = rest_do_request(new WP_REST_Request('GET', '/bixie/v1/looks/' . $clone)); qa_assert('Unqualified source record unavailable in public REST', $response->get_status() === 404);
    qa_assert('Public look-meta cannot expose incomplete draft override', bixie_render_look_meta(['lookId' => $clone, 'showImages' => true]) === '');
    update_post_meta($front, '_bixie_review_approved', $original_approval); wp_update_post(['ID' => $original, 'post_status' => 'publish']); wp_update_post(['ID' => $clone, 'post_status' => 'publish']); wp_update_post(wp_slash(['ID' => $guide, 'post_status' => 'publish', 'post_content' => $guide_content]));
    qa_assert('Restored review permits explicit republish; no silent source auto-publish', get_post_status($original) === 'publish' && get_post_status($clone) === 'publish' && get_post_status($guide) === 'publish');
    update_post_meta($front, '_wp_attached_file', $original_file . '.missing');
    qa_assert('Changing attachment file invalidates dependent records', get_post_status($clone) === 'draft' && get_post_status($guide) === 'draft' && !bixie_check_look($clone)['complete']);
    update_post_meta($front, '_wp_attached_file', $original_file); wp_update_post(['ID' => $original, 'post_status' => 'publish']); wp_update_post(['ID' => $clone, 'post_status' => 'publish']); wp_update_post(['ID' => $guide, 'post_status' => 'publish']);
    delete_post_meta($front, '_bixie_native_verified'); qa_assert('Removing native-source provenance invalidates publication', get_post_status($clone) === 'draft' && get_post_status($guide) === 'draft');
    update_post_meta($front, '_bixie_native_verified', $native); wp_update_post(['ID' => $original, 'post_status' => 'publish']); wp_update_post(['ID' => $clone, 'post_status' => 'publish']); wp_update_post(['ID' => $guide, 'post_status' => 'publish']);
    $other_entries = (array) get_post_meta($looks[0], 'bixie_images', true); $replacement = $other_entries[0]; $replacement['caption'] = 'OWNER REPLACED FRONT';
    $blocks = parse_blocks(get_post_field('post_content', $clone)); foreach ($blocks as &$block) { if (($block['attrs']['metadata']['name'] ?? '') === 'bixie-front') { $block = bixie_native_image_block($replacement); } } unset($block); wp_update_post(wp_slash(['ID' => $clone, 'post_content' => serialize_blocks($blocks)]));
    $canonical = get_post_meta($clone, 'bixie_images', true);
    qa_assert('Native Gutenberg image replacement updates canonical API front', absint($canonical[0]['id']) === absint($replacement['id']) && bixie_get_look_data($clone)['image']['id'] === absint($replacement['id']));
    qa_assert('Guide referencing obsolete canonical source safely returns to draft', get_post_status($guide) === 'draft');
    update_post_meta($clone, 'bixie_images', $entries);
    $named = bixie_named_images(parse_blocks(get_post_field('post_content', $clone)));
    qa_assert('Sidebar media metadata synchronizes actual native image blocks', absint($named[0]['id'] ?? 0) === $front && bixie_get_look_data($clone)['image']['id'] === $front);
    wp_update_post(wp_slash(['ID' => $guide, 'post_status' => 'publish', 'post_content' => $guide_content]));
    $reused = wp_insert_post(wp_slash(['post_type' => 'bixie_look', 'post_title' => 'ISOLATED rejected cross-primary copy', 'post_status' => 'publish', 'post_content' => $content, 'meta_input' => ['_bixie_qa_fixture' => 1, 'bixie_images' => $entries, 'bixie_primary_collection' => 'isolated-other-primary']]), true); $created_posts[] = $reused;
    qa_assert('Cross-primary source attachment reuse cannot publish', get_post_status($reused) === 'draft' && !bixie_check_look($reused)['complete']);
    $upload = wp_upload_dir(); $copies = [];
    foreach ($entries as $i => $entry) { $path = $upload['path'] . '/isolated-identity-copy-' . $i . '-' . wp_generate_password(8, false) . '.png'; copy(wp_get_original_image_path($entry['id']), $path); $created_files[] = $path; $id = wp_insert_attachment(['post_mime_type' => 'image/png', 'post_title' => 'ISOLATED duplicate file identity test', 'post_status' => 'inherit', 'meta_input' => ['_bixie_qa_fixture' => 1]], $path); $created_attachments[] = $id; wp_update_attachment_metadata($id, ['width' => 7680, 'height' => 512, 'file' => ltrim($upload['subdir'] . '/' . basename($path), '/')]); update_post_meta($id, '_bixie_review_approved', 1); update_post_meta($id, '_bixie_native_verified', 1); $copies[] = ['id' => $id, 'angle' => $entry['angle'], 'caption' => 'ISOLATED duplicated file test']; }
    qa_assert('Different attachment IDs cannot hide cross-primary exact-source reuse', !bixie_check_look(0, $copies, 'isolated-other-primary')['complete']);
    qa_assert('Owner privacy setting remains noindex', (int) get_option('blog_public') === 0);
} catch (Throwable $error) { $failure = $error->getMessage(); }
finally {
    update_post_meta($front, '_wp_attached_file', $original_file); update_post_meta($front, '_bixie_native_verified', $native); update_post_meta($front, '_bixie_review_approved', $original_approval);
    foreach (array_reverse($created_posts) as $post_id) { if (is_int($post_id)) { wp_delete_post($post_id, true); } }
    foreach ($created_attachments as $id) { wp_delete_attachment($id, true); }
    foreach ($created_files as $path) { if (is_file($path)) { unlink($path); } }
    wp_update_post(['ID' => $original, 'post_status' => $original_status]); bixie_invalidate_catalog();
}
$remaining = 0; foreach ($looks as $id) { if (get_post_status($id) === 'publish' && bixie_check_look($id)['complete']) { $remaining++; } }
$report = ['environment' => ['wordpress' => get_bloginfo('version'), 'php' => PHP_VERSION], 'method' => 'Actual isolated WordPress execution with explicitly synthetic 7680px TEST canvases; no production photographs or gate bypass', 'passed' => $failure === null && $remaining === 14, 'tests' => $tests, 'failure' => $failure, 'restoredOriginalFixtures' => $remaining, 'approvedProductionImages' => 0];
if (!empty($argv[2])) { file_put_contents($argv[2], wp_json_encode($report, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES) . "\n"); }
echo wp_json_encode($report, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES) . "\n"; exit($report['passed'] ? 0 : 1);
