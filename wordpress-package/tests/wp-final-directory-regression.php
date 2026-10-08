<?php
/** Actual parent-before-new-child import and owner draft/private preservation.
 * Reuses approved actual photographs and restores exact owned QA state in finally.
 */
if (PHP_SAPI !== 'cli' || empty($argv[1])) { exit(2); }
$_SERVER['HTTP_HOST'] = '127.0.0.1:8767'; $_SERVER['SERVER_NAME'] = '127.0.0.1'; $_SERVER['REQUEST_URI'] = '/';
require $argv[1];
if (wp_get_environment_type() !== 'local' || (int) get_option('blog_public') !== 0 || untrailingslashit(home_url('/')) !== 'http://127.0.0.1:8767') { exit(2); }
$admin = get_user_by('login', 'bixie_qa_admin'); if (!$admin || !user_can($admin, 'manage_options')) { exit(2); } wp_set_current_user($admin->ID);
$report = ['scope' => 'Actual isolated final-site importer using existing approved production photography. Parents are newly created before new child collection/guide pages; all temporary pages and saved owner state are restored. No synthetic look or image is imported.', 'checks' => [], 'passed' => false];
$posts = get_posts(['post_type' => 'page', 'post_status' => ['publish','draft','private','pending'], 'posts_per_page' => -1, 'meta_key' => '_bixie_import_key']);
$backup = ['pages' => [], 'terms' => [], 'options' => []]; $ids = [];
foreach ($posts as $post) { $key = (string) get_post_meta($post->ID, '_bixie_import_key', true); $ids[$key] = $post->ID; $backup['pages'][$post->ID] = ['status' => $post->post_status, 'content' => $post->post_content, 'meta' => get_post_meta($post->ID)]; }
foreach (get_terms(['taxonomy' => 'bixie_collection','hide_empty' => false]) as $term) { $backup['terms'][$term->term_id] = get_term_meta($term->term_id, 'bixie_page_id', true); }
foreach (['bixie_requirements','bixie_required_collections','bixie_required_home_media','bixie_required_home_video','bixie_import_state','show_on_front','page_on_front','blogname','blogdescription'] as $key) { $backup['options'][$key] = ['exists' => get_option($key, '__missing_final_qa__') !== '__missing_final_qa__', 'value' => get_option($key)]; }
if (empty($ids['collections']) || empty($ids['guides']) || empty($ids['about']) || !bixie_check_collection('classic')['complete']) { exit(2); }
$suffix = str_replace('-', '', wp_generate_uuid4()); $temporary_keys = ['collections','guides','final-qa-collection-' . $suffix,'final-qa-guide-' . $suffix]; $temporary_slugs = [];
$base = '/workspace/wp-final-test/directory-regression'; wp_mkdir_p($base); $backup_path = $base . '/private-owner-state-' . $suffix . '.json'; file_put_contents($backup_path, wp_json_encode($backup)); chmod($backup_path, 0600);
$path = $base . '/catalog-' . $suffix . '.json';
$original_catalog = Bixie_Importer::load();
function final_directory_qa_run(array $catalog, string $path): array {
    file_put_contents($path, wp_json_encode($catalog));
    $state = Bixie_Importer::start(false, false, $path);
    while ($state['status'] === 'running') { $state = Bixie_Importer::batch(10); }
    if (($state['counts']['errors'] ?? 0) !== 0) { throw new RuntimeException('Actual scoped importer reported an error.'); }
    return $state;
}
function final_directory_qa_find(string $key): int {
    $posts = get_posts(['post_type' => 'page','post_status' => ['publish','draft','private','pending'],'posts_per_page' => 1,'fields' => 'ids','meta_key' => '_bixie_import_key','meta_value' => $key]); return $posts ? (int) $posts[0] : 0;
}
try {
    // Hide the pre-existing real child pages, so an existing child cannot satisfy a new parent.
    foreach ($backup['pages'] as $id => $saved) {
        if (get_post_meta($id, '_bixie_collection_slug', true) !== '' || get_post_meta($id, '_bixie_content_type', true) === 'guide') { wp_update_post(['ID' => $id,'post_status' => 'draft']); }
    }
    foreach (['collections','guides'] as $key) { wp_update_post(['ID' => $ids[$key],'post_status' => 'draft']); update_post_meta($ids[$key], '_bixie_import_key', 'final-qa-held-' . $key . '-' . $suffix); }
    if (bixie_check_directory('collections')['complete'] || bixie_check_directory('guides')['complete']) { throw new RuntimeException('Existing real children were not isolated from the directory regression.'); }
    $pages = [];
    foreach (['collections','guides'] as $key) {
        $slug = 'final-qa-directory-' . $key . '-' . $suffix; $temporary_slugs[] = $slug;
        $pages[] = ['key' => $key,'slug' => $slug,'title' => 'Isolated actual source directory acceptance','status' => 'publish','type' => 'directory','content' => '<!-- wp:paragraph --><p>Actual source directory acceptance.</p><!-- /wp:paragraph -->'];
    }
    $collection_slug = 'final-qa-classic-child-' . $suffix; $guide_slug = 'final-qa-reference-child-' . $suffix; $temporary_slugs[] = $collection_slug; $temporary_slugs[] = $guide_slug;
    $pages[] = ['key' => $temporary_keys[2],'slug' => $collection_slug,'parent_key' => 'collections','title' => 'Isolated actual classic collection acceptance','status' => 'publish','type' => 'collection','gallery_collection' => 'classic','content' => '<!-- wp:bixie/library {"collection":"classic","perPage":7,"showViews":true} /-->'];
    $pages[] = ['key' => $temporary_keys[3],'slug' => $guide_slug,'parent_key' => 'guides','title' => 'Isolated actual reference guide acceptance','status' => 'publish','type' => 'guide','minimum_photos' => 3,'photo_set_requirements' => [['look_key' => 'classic-01','angles' => ['front','side','back']]],'content' => '<!-- wp:paragraph --><p>Existing actual original views form this editable reference gallery.</p><!-- /wp:paragraph -->'];
    $catalog = ['site' => $original_catalog['site'],'requirements' => $original_catalog['requirements'],'collections' => [],'looks' => [],'pages' => $pages]; file_put_contents($path, wp_json_encode($catalog));
    $state = Bixie_Importer::start(false, false, $path); $parent_start = $state['total'] - 5;
    while ($state['cursor'] < $parent_start) { $state = Bixie_Importer::batch(min(10, $parent_start - $state['cursor'])); }
    $state = Bixie_Importer::batch(1); $state = Bixie_Importer::batch(1);
    $new_collection_parent = final_directory_qa_find('collections'); $new_guide_parent = final_directory_qa_find('guides');
    $report['checks']['newParentsCreatedBeforeNewChildrenAndRemainDraftWhileChildrenAbsent'] = $new_collection_parent && $new_guide_parent && get_post_status($new_collection_parent) === 'draft' && get_post_status($new_guide_parent) === 'draft' && !final_directory_qa_find($temporary_keys[2]) && !final_directory_qa_find($temporary_keys[3]);
    if (!$report['checks']['newParentsCreatedBeforeNewChildrenAndRemainDraftWhileChildrenAbsent']) { throw new RuntimeException('Parent-first publication precondition failed.'); }
    while ($state['status'] === 'running') { $state = Bixie_Importer::batch(1); }
    $report['checks']['oneActualImportPublishesBothUneditedDirectoriesAfterRealChildrenCreated'] = get_post_status($new_collection_parent) === 'publish' && get_post_status($new_guide_parent) === 'publish' && get_post_status(final_directory_qa_find($temporary_keys[2])) === 'publish' && get_post_status(final_directory_qa_find($temporary_keys[3])) === 'publish' && ($state['counts']['errors'] ?? 0) === 0;
    $report['firstPassDirectoryDiagnostics'] = $state['diagnostics']['directories'] ?? [];
    if (!$report['checks']['oneActualImportPublishesBothUneditedDirectoriesAfterRealChildrenCreated']) { throw new RuntimeException('First-pass directory reconciliation failed.'); }
    $about = $ids['about']; $original = $backup['pages'][$about]['content']; $marker = "\n<!-- wp:paragraph --><p>Isolated actual owner draft preservation acceptance.</p><!-- /wp:paragraph -->";
    $record = array_values(array_filter($original_catalog['pages'], static fn($p) => $p['key'] === 'about'))[0]; $record['status'] = 'publish';
    $single = ['site' => $original_catalog['site'],'requirements' => $original_catalog['requirements'],'collections' => [],'looks' => [],'pages' => [$record]];
    wp_update_post(wp_slash(['ID' => $about,'post_status' => 'draft','post_content' => $original . $marker])); update_post_meta($about, '_bixie_gate_blocked', 1); update_post_meta($about, '_bixie_import_content_hash', hash('sha256', $original));
    final_directory_qa_run($single, $path);
    $report['checks']['editedOwnerBlockedDraftContentAndDraftStatusPreserved'] = get_post_status($about) === 'draft' && get_post_field('post_content', $about) === $original . $marker;
    wp_update_post(wp_slash(['ID' => $about,'post_status' => 'private','post_content' => $original])); update_post_meta($about, '_bixie_gate_blocked', 1); update_post_meta($about, '_bixie_import_content_hash', hash('sha256', $original));
    final_directory_qa_run($single, $path);
    $report['checks']['unchangedOwnerPrivateStatusAndContentPreserved'] = get_post_status($about) === 'private' && get_post_field('post_content', $about) === $original;
    if (in_array(false, $report['checks'], true)) { throw new RuntimeException('Owner draft/private preservation failed.'); }
    $report['passed'] = true;
} catch (Throwable $error) {
    $report['failure'] = $error->getMessage();
} finally {
    $removed = [];
    foreach (get_posts(['post_type' => 'page','post_status' => ['publish','draft','private','pending'],'posts_per_page' => -1]) as $post) {
        if (!isset($backup['pages'][$post->ID]) && in_array($post->post_name, $temporary_slugs, true)) { $removed[] = $post->ID; wp_delete_post($post->ID, true); }
    }
    foreach ($backup['pages'] as $id => $saved) {
        foreach (get_post_meta($id) as $key => $values) { delete_post_meta($id, $key); }
        foreach ($saved['meta'] as $key => $values) { foreach ($values as $value) { add_post_meta($id, $key, maybe_unserialize($value)); } }
    }
    // Restore real child publications before directory parents, keeping normal gates enabled.
    foreach ([false, true] as $directories) {
        foreach ($backup['pages'] as $id => $saved) {
            $is_directory = in_array(get_post_meta($id, '_bixie_directory_kind', true), ['collections','looks','guides'], true);
            if ($is_directory === $directories) { wp_update_post(wp_slash(['ID' => $id,'post_status' => $saved['status'],'post_content' => $saved['content']])); }
        }
    }
    foreach ($backup['terms'] as $id => $page_id) { update_term_meta($id, 'bixie_page_id', $page_id); }
    foreach ($backup['options'] as $key => $saved) { if ($saved['exists']) { update_option($key, $saved['value']); } else { delete_option($key); } }
    $restored = true;
    foreach ($backup['pages'] as $id => $saved) { if (get_post_status($id) !== $saved['status'] || get_post_field('post_content', $id) !== $saved['content']) { $restored = false; } }
    $report['checks']['allExactOriginalNativePageStatusesAndContentRestored'] = $restored;
    $report['checks']['allExactTemporaryPagesRemoved'] = count(array_filter($removed, 'get_post')) === 0;
    $report['temporaryPageCountRemoved'] = count($removed); $report['originalAttachmentCountPreserved'] = count(get_posts(['post_type'=>'attachment','post_status'=>'inherit','posts_per_page'=>-1,'fields'=>'ids','meta_key'=>'_bixie_asset_key']));
    if (!$restored) { $report['passed'] = false; $report['failure'] = 'Exact native page restoration failed; private backup retained.'; }
    else { unlink($backup_path); unlink($path); }
    file_put_contents(__DIR__ . '/wp-final-directory-regression-report.json', wp_json_encode($report, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES) . "\n");
    echo wp_json_encode($report, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES) . "\n";
}
exit($report['passed'] ? 0 : 1);
