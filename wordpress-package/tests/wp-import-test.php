<?php
/** Real database importer checks. Requires a disposable local noindex WP site.
 * Usage: php wp-import-test.php /path/to/wp-load.php start|resume|idempotence|state
 */
if (PHP_SAPI !== 'cli' || empty($argv[1]) || empty($argv[2])) { exit(2); }
$_SERVER['HTTP_HOST']='127.0.0.1:8766';$_SERVER['SERVER_NAME']='127.0.0.1';$_SERVER['REQUEST_URI']='/';
require $argv[1];
if (wp_get_environment_type() !== 'local' || (int) get_option('blog_public') !== 0 || !class_exists('Bixie_Importer')) {
    fwrite(STDERR,"Requires the plugin in an isolated local noindex QA database.\n");exit(2);
}
function bixie_qa_assert($ok,string $message): void {if(!$ok){throw new RuntimeException($message);}}
function bixie_qa_counts(): array {
    global $wpdb;
    return ['pages'=>(int)$wpdb->get_var("SELECT COUNT(*) FROM {$wpdb->posts} WHERE post_type='page'"),'looks'=>(int)$wpdb->get_var("SELECT COUNT(*) FROM {$wpdb->posts} WHERE post_type='bixie_look'"),'attachments'=>(int)$wpdb->get_var("SELECT COUNT(*) FROM {$wpdb->posts} WHERE post_type='attachment'"),'collections'=>(int)wp_count_terms(['taxonomy'=>'bixie_collection','hide_empty'=>false])];
}
function bixie_qa_finish_import(): array {
    $limit=0;
    do {$state=Bixie_Importer::batch(10);if(++$limit>200){throw new RuntimeException('Import did not terminate.');}}
    while(($state['status']??'')==='running');
    bixie_qa_assert(($state['status']??'')==='complete','Import status did not reach complete.');
    bixie_qa_assert(empty($state['counts']['errors']),'Importer reported errors: '.wp_json_encode($state['log']));
    return $state;
}
try {
    if($argv[2]==='start') {
        $state=Bixie_Importer::start(false,true);
        $state=Bixie_Importer::batch(2);
        bixie_qa_assert($state['status']==='running'&&$state['cursor']===2,'First short batch did not retain its resumable cursor.');
        echo wp_json_encode(['firstBatch'=>$state['cursor'],'total'=>$state['total'],'status'=>$state['status'],'counts'=>$state['counts']],JSON_PRETTY_PRINT)."\n";
    } elseif($argv[2]==='resume') {
        $before=Bixie_Importer::status();$resumed=Bixie_Importer::start(false,true);
        bixie_qa_assert($resumed['cursor']===$before['cursor']&&$resumed['fingerprint']===$before['fingerprint'],'New PHP request did not resume the persisted import.');
        $state=bixie_qa_finish_import();
        $homes=get_posts(['post_type'=>'page','post_status'=>['draft','publish'],'posts_per_page'=>1,'meta_key'=>'_bixie_import_key','meta_value'=>'home']);
        bixie_qa_assert($homes&&$homes[0]->post_status==='draft','Unapproved production homepage became public.');
        bixie_qa_assert(!bixie_check_home()['complete'],'Production homepage unexpectedly passed its gate.');
        bixie_qa_assert(count(get_option('bixie_required_home_media',[]))===25,'Importer did not retain all 25 homepage photo requirements.');
        bixie_qa_assert(get_option('bixie_required_home_video')==='home-motion-film','Required homepage motion source was lost.');
        bixie_qa_assert(bixie_qa_counts()['looks']===0,'The zero-approved production catalog created fictitious launch looks.');
        update_option('bixie_qa_import_baseline',bixie_qa_counts(),false);
        echo wp_json_encode(['resumedFromCursor'=>$before['cursor'],'completedCursor'=>$state['cursor'],'counts'=>$state['counts'],'databaseCounts'=>bixie_qa_counts(),'homeDraft'=>true,'homeRequiredPhotos'=>count(get_option('bixie_required_home_media',[])),'homeRequiredVideo'=>get_option('bixie_required_home_video'),'productionApprovedLooks'=>0],JSON_PRETTY_PRINT)."\n";
    } elseif($argv[2]==='idempotence') {
        $pages=get_posts(['post_type'=>'page','post_status'=>'publish','posts_per_page'=>1,'meta_key'=>'_bixie_import_key']);
        bixie_qa_assert((bool)$pages,'No imported published guide/support page is available for owner-edit preservation.');
        $page=$pages[0];$description=get_post_meta($page->ID,'_bixie_meta_description',true);
        $edited='OWNER QA EDIT preserved through reimport';
        wp_update_post(wp_slash(['ID'=>$page->ID,'post_title'=>$edited,'post_content'=>$page->post_content."\n<!-- wp:paragraph --><p>OWNER QA EDIT.</p><!-- /wp:paragraph -->"]));
        update_post_meta($page->ID,'_bixie_meta_description',$edited);
        $before=bixie_qa_counts();Bixie_Importer::start(false,false);
        $lock=['token'=>'isolated-qa-lock','created'=>time()];add_option('bixie_import_lock',$lock,'',false);
        $blocked=false;try{Bixie_Importer::batch(1);}catch(RuntimeException $e){$blocked=str_contains($e->getMessage(),'Another importer');}
        if(get_option('bixie_import_lock')===$lock){delete_option('bixie_import_lock');}
        bixie_qa_assert($blocked,'Importer failed to reject a concurrent nonstale batch lock.');
        $state=bixie_qa_finish_import();$after=get_post($page->ID);
        bixie_qa_assert($before===bixie_qa_counts(),'Rerunning the importer duplicated package content.');
        bixie_qa_assert($after->post_title===$edited&&str_contains($after->post_content,'OWNER QA EDIT.'),'Default reimport overwrote owner title/body edits.');
        bixie_qa_assert(get_post_meta($page->ID,'_bixie_meta_description',true)===$edited,'Default reimport overwrote owner description metadata.');
        global $wpdb;
        $duplicate=(int)$wpdb->get_var("SELECT COUNT(*) FROM (SELECT m.meta_value,p.post_type,COUNT(*) AS n FROM {$wpdb->postmeta} m JOIN {$wpdb->posts} p ON p.ID=m.post_id WHERE m.meta_key='_bixie_import_key' AND p.post_type IN ('page','bixie_look','attachment') GROUP BY m.meta_value,p.post_type HAVING n>1) d");
        bixie_qa_assert($duplicate===0,'Duplicate package import keys found.');
        // Restore our own deliberate owner-edit fixture, leaving real owner edits untouched.
        wp_update_post(wp_slash(['ID'=>$page->ID,'post_title'=>$page->post_title,'post_content'=>$page->post_content]));
        update_post_meta($page->ID,'_bixie_meta_description',$description);
        echo wp_json_encode(['reimportCounts'=>$state['counts'],'databaseCounts'=>bixie_qa_counts(),'ownerTitleBodyAndDescriptionPreserved'=>true,'duplicateImportKeys'=>$duplicate,'concurrentBatchRejected'=>true,'testOwnerEditRestored'=>true],JSON_PRETTY_PRINT)."\n";
    } elseif($argv[2]==='state') {
        echo wp_json_encode(['counts'=>bixie_qa_counts(),'importStatus'=>Bixie_Importer::status()['status']??'not-started','requirements'=>bixie_requirements(),'homeComplete'=>bixie_check_home()['complete'],'frontPageOption'=>get_option('page_on_front'),'visibility'=>get_option('blog_public')],JSON_PRETTY_PRINT)."\n";
    } else {exit(2);}
} catch(Throwable $e) {fwrite(STDERR,$e->getMessage()."\n");exit(1);}
