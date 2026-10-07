<?php
/** Temporary collection page referring only to existing isolated QA canvases. */
if(PHP_SAPI!=='cli'||empty($argv[1])||empty($argv[2])){exit(2);}
$_SERVER['HTTP_HOST']='127.0.0.1:8766';$_SERVER['SERVER_NAME']='127.0.0.1';$_SERVER['REQUEST_URI']='/';require $argv[1];
if(wp_get_environment_type()!=='local'||(int)get_option('blog_public')!==0){exit(2);}
$id=(int)get_option('bixie_qa_collection_page');
if($argv[2]==='cleanup'){if($id&&get_post_meta($id,'_bixie_qa_fixture',true)){wp_delete_post($id,true);}delete_option('bixie_qa_collection_page');echo "{\"temporaryCollectionPageRemoved\":true}\n";exit;}
if($argv[2]!=='create'){exit(2);}
if(!$id){$id=wp_insert_post(['post_type'=>'page','post_status'=>'publish','post_title'=>'ISOLATED COLLECTION CODE TEST — not hairstyle photography','post_name'=>'isolated-code-test-collection','post_content'=>'<!-- wp:paragraph --><p>ISOLATED SYNTHETIC CODE TEST CANVASES. Not launch photographs.</p><!-- /wp:paragraph --><!-- wp:bixie/library {"collection":"isolated-qa-fixtures","perPage":7,"showViews":true} /-->','meta_input'=>['_bixie_qa_fixture'=>1]]);update_option('bixie_qa_collection_page',$id,false);}
if(get_post_status($id)!=='publish'){wp_update_post(['ID'=>$id,'post_status'=>'publish']);}
if(get_post_status($id)!=='publish'){throw new RuntimeException('Ordinary native page with no guide-photo dependencies could not publish.');}
if(bixie_query_looks(['collection'=>'isolated-qa-fixtures','per_page'=>7])['total']!==14){throw new RuntimeException('Expected stable original 14 isolated look fixtures.');}
flush_rewrite_rules(false);echo wp_json_encode(['page'=>$id,'perPage'=>7,'expectedPhotosPerPage'=>21,'notLaunchMedia'=>true])."\n";
