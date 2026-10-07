<?php
/** Isolated media-upload authorization state and cleanup. Never print secrets. */
if(PHP_SAPI!=='cli'||empty($argv[1])||empty($argv[2])){exit(2);}
$_SERVER['HTTP_HOST']='127.0.0.1:8766';$_SERVER['SERVER_NAME']='127.0.0.1';$_SERVER['REQUEST_URI']='/';require $argv[1];
if(wp_get_environment_type()!=='local'||(int)get_option('blog_public')!==0){exit(2);}
$state_path='/workspace/wp-test/qa-subscriber-state.json';$nonce_path='/workspace/wp-test/qa-subscriber-nonce.json';
if($argv[2]==='subscriber'){
    $user=get_user_by('login','isolated_qa_upload_subscriber');
    if(!$user){$id=wp_insert_user(['user_login'=>'isolated_qa_upload_subscriber','user_pass'=>wp_generate_password(48,true,true),'user_email'=>'isolated-upload-qa@example.invalid','role'=>'subscriber']);if(is_wp_error($id)){throw new RuntimeException('Cannot create isolated capability fixture.');}$user=get_user_by('id',$id);}
    if(!in_array('subscriber',$user->roles,true)){throw new RuntimeException('Existing fixture user role differs.');}
    wp_set_current_user($user->ID);$expires=time()+3600;$cookies=[];
    foreach([[AUTH_COOKIE,ADMIN_COOKIE_PATH,'auth'],[LOGGED_IN_COOKIE,COOKIEPATH,'logged_in']] as [$name,$path,$scheme]){
        $value=wp_generate_auth_cookie($user->ID,$expires,$scheme);$_COOKIE[$name]=$value;
        $cookies[]=['name'=>$name,'value'=>$value,'domain'=>'127.0.0.1','path'=>$path,'expires'=>$expires,'httpOnly'=>true,'secure'=>false,'sameSite'=>'Lax'];
    }
    file_put_contents($state_path,wp_json_encode(['cookies'=>$cookies,'origins'=>[]]));chmod($state_path,0600);
    $nonce=wp_create_nonce('bixie_media_bundles');file_put_contents($nonce_path,wp_json_encode(['nonce'=>$nonce]));chmod($nonce_path,0600);
    if(!wp_verify_nonce($nonce,'bixie_media_bundles')){throw new RuntimeException('Isolated nonce context did not validate.');}
    echo "{\"isolatedSubscriberStateCreated\":true,\"ownNonceContextValid\":true}\n";exit;
}
if($argv[2]==='check'){
    $result=[];foreach(['front','side','back'] as $angle){$id=bixie_get_package_attachment('isolated-qa-upload-'.$angle);if(!$id){throw new RuntimeException('GUI-imported isolated upload source missing.');}update_post_meta($id,'_bixie_qa_fixture',1);$result[]=['angle'=>$angle,'sourceWidth'=>(int)get_post_meta($id,'_bixie_source_width',true),'sourceHeight'=>(int)get_post_meta($id,'_bixie_source_height',true),'approved'=>(bool)get_post_meta($id,'_bixie_review_approved',true)];}
    echo wp_json_encode(['unapprovedSyntheticSourcesImported'=>$result,'notLaunchMedia'=>true],JSON_PRETTY_PRINT)."\n";exit;
}
if($argv[2]==='cleanup'){
    require_once ABSPATH.'wp-admin/includes/user.php';$user=get_user_by('login','isolated_qa_upload_subscriber');if($user&&in_array('subscriber',$user->roles,true)){wp_delete_user($user->ID);}
    foreach([$state_path,$nonce_path] as $path){if(is_file($path)){unlink($path);}}
    foreach(['front','side','back'] as $angle){$id=bixie_get_package_attachment('isolated-qa-upload-'.$angle);if($id){wp_delete_attachment($id,true);}}
    $parts=(array)get_option('bixie_media_bundle_parts',[]);$id='isolated-qa-browser-upload';if(isset($parts[$id])){$root=bixie_bundle_base().'/'.$id;if(is_dir($root)){bixie_bundle_remove_stage($root);}unset($parts[$id]);update_option('bixie_media_bundle_parts',$parts,false);}
    bixie_invalidate_catalog();echo "{\"onlyIsolatedUploadDataRemoved\":true}\n";exit;
}
exit(2);
