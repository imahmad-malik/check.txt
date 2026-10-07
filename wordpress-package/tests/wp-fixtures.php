<?php
/** Synthetic CODE fixtures for an isolated local noindex WordPress test database.
 * Usage: php wp-fixtures.php /path/to/wp-load.php create|check|cleanup
 * Native 7680px generated test canvases are not hairstyle photographs, launch
 * assets, or approved production content. Nothing is written into the package.
 * The production resolution/review/angle requirements remain enabled.
 */
if (PHP_SAPI !== 'cli' || empty($argv[1]) || empty($argv[2])) { exit(2); }
$_SERVER['HTTP_HOST'] = '127.0.0.1:8766';
$_SERVER['SERVER_NAME'] = '127.0.0.1';
$_SERVER['REQUEST_URI'] = '/';
require $argv[1];
if (wp_get_environment_type() !== 'local' || (int) get_option('blog_public') !== 0 || !function_exists('bixie_check_look')) {
    fwrite(STDERR, "Requires the companion plugin in an isolated local noindex QA site.\n"); exit(2);
}
function bixie_qa_cleanup(): array {
    $posts = get_posts(['post_type' => ['bixie_look', 'page', 'attachment'], 'post_status' => ['publish','draft','private','inherit','trash','pending'], 'posts_per_page' => -1, 'meta_key' => '_bixie_qa_fixture', 'meta_value' => '1']);
    $removed = 0;
    foreach ($posts as $post) {
        if ($post->post_type === 'attachment') { wp_delete_attachment($post->ID, true); }
        else { wp_delete_post($post->ID, true); }
        $removed++;
    }
    $term = get_term_by('slug','isolated-qa-fixtures','bixie_collection');
    if ($term) { wp_delete_term($term->term_id,'bixie_collection'); }
    delete_option('bixie_qa_fixture_state');
    bixie_invalidate_catalog();
    return ['removedOnlyQaTaggedPosts' => $removed, 'productionRequirements' => bixie_requirements()];
}
if ($argv[2] === 'cleanup') { echo wp_json_encode(bixie_qa_cleanup(), JSON_PRETTY_PRINT) . "\n"; exit; }
if ($argv[2] === 'check') {
    $state = get_option('bixie_qa_fixture_state', []);
    $valid = [];
    foreach ($state['looks'] ?? [] as $id) { $valid[$id] = bixie_check_look((int) $id); }
    echo wp_json_encode(['fixtures' => $state, 'checks' => $valid, 'total' => bixie_query_looks(['per_page' => 6])['total']], JSON_PRETTY_PRINT) . "\n"; exit;
}
if ($argv[2] !== 'create') { exit(2); }
bixie_qa_cleanup();
$requirements = bixie_requirements();
$catalog = json_decode(file_get_contents(BIXIE_LIBRARY_DIR . 'content/catalog.json'), true);
if ((int) $requirements['minimum_native_long_edge'] !== (int) $catalog['requirements']['minimum_native_long_edge'] || empty($requirements['require_complete_angles'])) {
    fwrite(STDERR, "Configured source resolution/three-angle requirements must remain unchanged for this fixture check.\n"); exit(1);
}
require_once ABSPATH . 'wp-admin/includes/image.php';
$upload = wp_upload_dir();
$state = ['purpose' => 'ISOLATED SYNTHETIC CODE TEST FIXTURES — never release photographs', 'looks' => [], 'attachments' => []];
$term = wp_insert_term('ISOLATED QA fixtures — not hairstyles', 'bixie_collection', ['slug' => 'isolated-qa-fixtures']);
if (is_wp_error($term)) { fwrite(STDERR,$term->get_error_message()); exit(1); }
for ($i = 1; $i <= 14; $i++) {
    $entries = []; $blocks = "<!-- wp:paragraph --><p>ISOLATED SYNTHETIC CODE TEST. This is not a haircut reference or a launch asset.</p><!-- /wp:paragraph -->\n";
    foreach (['front','side','back'] as $a => $angle) {
        $file = sprintf('isolated-qa-%02d-%s.png', $i, $angle);
        $path = $upload['path'] . '/' . $file;
        $canvas = imagecreatetruecolor(7680, 512);
        $background = imagecolorallocate($canvas, 180 + $i * 3, 150 + $a * 15, 145 + $i);
        $ink = imagecolorallocate($canvas, 20, 20, 20);
        imagefilledrectangle($canvas,0,0,7679,511,$background);
        for ($x=80;$x<7680;$x+=640) { imagestring($canvas,5,$x,250,sprintf('TEST %02d %s — NOT HAIRSTYLE MEDIA',$i,strtoupper($angle)),$ink); }
        imagepng($canvas,$path,6); imagedestroy($canvas);
        $id = wp_insert_attachment(['post_mime_type'=>'image/png','post_title'=>sprintf('ISOLATED TEST %02d %s — synthetic canvas',$i,$angle),'post_status'=>'inherit','meta_input'=>['_bixie_qa_fixture'=>1]],$path,0,true);
        if (is_wp_error($id)) { fwrite(STDERR,$id->get_error_message()); exit(1); }
        wp_update_attachment_metadata($id,['width'=>7680,'height'=>512,'file'=>ltrim($upload['subdir'] . '/' . $file,'/'),'sizes'=>[]]);
        update_post_meta($id,'_bixie_review_approved',1);
        update_post_meta($id,'_bixie_native_verified',1);
        update_post_meta($id,'_wp_attachment_image_alt',sprintf('ISOLATED SYNTHETIC QA canvas %02d %s. Not hairstyle photography.',$i,$angle));
        $entry=['id'=>$id,'angle'=>$angle,'caption'=>'ISOLATED TEST — '.$angle];
        $entries[]=$entry;
        $blocks .= serialize_block(bixie_native_image_block($entry)) . "\n";
        $state['attachments'][]=$id;
    }
    $blocks .= "\n<!-- wp:bixie/look-meta /-->";
    $id=wp_insert_post(wp_slash(['post_type'=>'bixie_look','post_title'=>sprintf('ISOLATED TEST look %02d — not hairstyle content',$i),'post_name'=>sprintf('isolated-test-look-%02d',$i),'post_content'=>$blocks,'post_status'=>'publish','menu_order'=>$i,'meta_input'=>['_bixie_qa_fixture'=>1,'bixie_images'=>$entries,'bixie_texture'=>$i%2?'wavy':'straight','bixie_length'=>$i%3?'short':'long','bixie_fringe'=>$i%2?'curtain':'none','bixie_colour'=>$i%2?'brunette':'silver','bixie_styling'=>'ISOLATED test styling note.','bixie_maintenance'=>'ISOLATED test maintenance note.','bixie_ai_concept'=>false]]),true);
    if (is_wp_error($id) || get_post_status($id)!=='publish' || !bixie_check_look($id)['complete']) { fwrite(STDERR,wp_json_encode(['error'=>'Synthetic fixture failed the unchanged production gate','look'=>$id,'check'=>is_int($id)?bixie_check_look($id):null]));exit(1); }
    wp_set_object_terms($id,[(int)$term['term_id']],'bixie_collection');
    update_post_meta($id,'_bixie_record_complete','1');
    $state['looks'][]=$id;
}
$state['libraryPage']=wp_insert_post(['post_type'=>'page','post_title'=>'ISOLATED CODE TEST photo library — synthetic fixtures','post_name'=>'isolated-code-test-library','post_status'=>'publish','post_content'=>'<!-- wp:paragraph --><p>ISOLATED CODE TEST ONLY. These synthetic canvases are not hairstyle photographs and never ship in the package.</p><!-- /wp:paragraph --><!-- wp:bixie/library {"perPage":6} /-->','meta_input'=>['_bixie_qa_fixture'=>1]]);
$state['savedPage']=wp_insert_post(['post_type'=>'page','post_title'=>'ISOLATED CODE TEST saved looks','post_name'=>'isolated-code-test-saved','post_status'=>'publish','post_content'=>'<!-- wp:bixie/saved-looks /-->','meta_input'=>['_bixie_qa_fixture'=>1]]);
update_option('bixie_qa_fixture_state',$state,false);
bixie_invalidate_catalog();flush_rewrite_rules(false);
echo wp_json_encode(['createdLooks'=>count($state['looks']),'createdSyntheticSources'=>count($state['attachments']),'libraryPage'=>$state['libraryPage'],'savedPage'=>$state['savedPage'],'requirementsUnchanged'=>bixie_requirements()===$requirements,'productionApprovedAssetCount'=>0],JSON_PRETTY_PRINT) . "\n";
