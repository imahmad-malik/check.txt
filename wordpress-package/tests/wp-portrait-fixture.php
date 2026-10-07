<?php
/** Temporary portrait-ratio synthetic CODE fixture. Never launch photography. */
if (PHP_SAPI !== 'cli' || empty($argv[1]) || empty($argv[2])) { exit(2); }
$_SERVER['HTTP_HOST']='127.0.0.1:8766';$_SERVER['SERVER_NAME']='127.0.0.1';$_SERVER['REQUEST_URI']='/';
require $argv[1];
if (wp_get_environment_type() !== 'local' || (int)get_option('blog_public') !== 0) { exit(2); }
function portrait_cleanup() {
    $state=get_option('bixie_qa_portrait_state',[]);
    if (!empty($state['look']) && get_post_meta($state['look'],'_bixie_qa_fixture',true)) {wp_delete_post($state['look'],true);}
    foreach($state['attachments']??[] as $id) {if(get_post_meta($id,'_bixie_qa_fixture',true)){wp_delete_attachment($id,true);}}
    delete_option('bixie_qa_portrait_state');bixie_invalidate_catalog();
}
if($argv[2]==='cleanup'){portrait_cleanup();echo "{\"temporaryPortraitFixturesRemoved\":true}\n";exit;}
if($argv[2]!=='create'){exit(2);}
portrait_cleanup();
$requirements=bixie_requirements();
if((int)$requirements['minimum_native_long_edge']>1310){throw new RuntimeException('This portrait fixture cannot satisfy the configured source minimum. No requirement was changed.');}
$upload=wp_upload_dir();$state=['purpose'=>'ISOLATED PORTRAIT CODE TEST. Not hairstyle photography.','attachments'=>[]];$entries=[];$content='';
foreach(['front','side','back'] as $a=>$angle){
    $name='isolated-qa-portrait-'.$angle.'.png';$path=$upload['path'].'/'.$name;$c=imagecreatetruecolor(1048,1310);
    $background=imagecolorallocate($c,30+$a*20,100+$a*15,150+$a*15);$white=imagecolorallocate($c,255,255,255);$yellow=imagecolorallocate($c,255,220,20);$red=imagecolorallocate($c,230,50,50);
    imagefilledrectangle($c,0,0,1047,1309,$background);
    imagefilledrectangle($c,0,0,1047,100,$yellow);imagefilledrectangle($c,0,1209,1047,1309,$red);
    for($y=200;$y<1200;$y+=200){imagestring($c,5,90,$y,'ISOLATED TEST CANVAS '.$angle.' - NOT A HAIRSTYLE PHOTO',$white);}
    imagepng($c,$path,6);imagedestroy($c);
    $id=wp_insert_attachment(['post_mime_type'=>'image/png','post_title'=>'ISOLATED PORTRAIT TEST '.$angle,'post_status'=>'inherit','meta_input'=>['_bixie_qa_fixture'=>1]],$path,0,true);
    if(is_wp_error($id)){throw new RuntimeException($id->get_error_message());}
    wp_update_attachment_metadata($id,['width'=>1048,'height'=>1310,'file'=>ltrim($upload['subdir'].'/'.$name,'/'),'sizes'=>[]]);
    update_post_meta($id,'_bixie_review_approved',1);update_post_meta($id,'_bixie_native_verified',1);update_post_meta($id,'_wp_attachment_image_alt','ISOLATED portrait-ratio CODE canvas '.$angle.'; not hairstyle photography.');
    $entry=['id'=>$id,'angle'=>$angle,'caption'=>'ISOLATED CODE TEST '.$angle];$entries[]=$entry;$state['attachments'][]=$id;$content.=serialize_block(bixie_native_image_block($entry));
}
$id=wp_insert_post(wp_slash(['post_type'=>'bixie_look','post_status'=>'publish','post_title'=>'ISOLATED PORTRAIT GEOMETRY TEST — synthetic canvas','post_name'=>'isolated-portrait-geometry-test','post_content'=>$content.'<!-- wp:bixie/look-meta /-->','meta_input'=>['_bixie_qa_fixture'=>1,'bixie_images'=>$entries,'bixie_texture'=>'straight','bixie_length'=>'short','bixie_fringe'=>'none','bixie_colour'=>'brunette']]));
$state['look']=$id;update_option('bixie_qa_portrait_state',$state,false);bixie_invalidate_catalog();
if(get_post_status($id)!=='publish'||!bixie_check_look($id)['complete']){throw new RuntimeException('Unchanged configured publication gate rejected the isolated portrait code fixture.');}
echo wp_json_encode(['look'=>$id,'sourceDimensions'=>[1048,1310],'unchangedRequirements'=>bixie_requirements()===$requirements,'notLaunchAssets'=>true],JSON_PRETTY_PRINT)."\n";
