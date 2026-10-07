<?php
/** Credential-free retained content snapshot for owned QA service restart. */
if(PHP_SAPI!=='cli'||empty($argv[1])){exit(2);}
$_SERVER['HTTP_HOST']='127.0.0.1:8766';$_SERVER['SERVER_NAME']='127.0.0.1';$_SERVER['REQUEST_URI']='/';require $argv[1];
if(wp_get_environment_type()!=='local'||(int)get_option('blog_public')!==0){exit(2);}
global $wpdb;
$rows=$wpdb->get_results("SELECT ID,post_type,post_status,post_title,post_content,post_name,post_parent,menu_order FROM {$wpdb->posts} ORDER BY ID",ARRAY_A);
$looks=[];foreach(get_option('bixie_qa_fixture_state',[])['looks']??[] as $id){$looks[$id]=['status'=>get_post_status($id),'images'=>get_post_meta($id,'bixie_images',true)];}
echo wp_json_encode(['posts'=>count($rows),'contentDigest'=>hash('sha256',wp_json_encode($rows)),'lookIds'=>array_keys($looks),'lookRelationshipsDigest'=>hash('sha256',wp_json_encode($looks)),'requirementsDigest'=>hash('sha256',wp_json_encode(bixie_requirements())),'activeTheme'=>get_stylesheet(),'pluginActive'=>in_array('bixie-library/bixie-library.php',(array)get_option('active_plugins'),true),'homeComplete'=>bixie_check_home()['complete'],'schemaDisabled'=>(bool)get_option('bixie_schema_disabled')],JSON_PRETTY_PRINT)."\n";
