<?php
if (!defined('ABSPATH')) { exit; }

function bixie_release_url_allowed(string $url): bool {
    $parsed=wp_parse_url($url);if(!is_array($parsed)||($parsed['scheme']??'')!=='https'||!in_array(strtolower($parsed['host']??''),['raw.githubusercontent.com','github.com'],true)||isset($parsed['user'])||isset($parsed['pass'])||(isset($parsed['port'])&&(int)$parsed['port']!==443)){return false;}
    return str_starts_with($parsed['path']??'','/imahmad-malik/check.txt/')&&!preg_match('/[\x00-\x20\\\\]/',$url);
}
function bixie_release_index(): array {
    $path=BIXIE_LIBRARY_DIR.'content/release-index.json';if(!is_readable($path)){return ['version'=>1,'release'=>'','parts'=>[]];}
    $index=json_decode((string)file_get_contents($path),true,64,JSON_THROW_ON_ERROR);
    if(!is_array($index)||!is_array($index['parts']??null)||count($index['parts'])>300){throw new RuntimeException('Embedded release index is invalid.');}
    $ids=[];foreach($index['parts'] as $part){if(!is_array($part)||!preg_match('/^[a-z0-9][a-z0-9-]{0,63}$/D',(string)($part['bundle_id']??''))||isset($ids[$part['bundle_id']])||!bixie_release_url_allowed((string)($part['url']??''))||!preg_match('/^[a-f0-9]{64}$/iD',(string)($part['sha256']??''))||!is_numeric($part['bytes']??null)||$part['bytes']<=0||$part['bytes']>25*MB_IN_BYTES){throw new RuntimeException('Embedded media URL, checksum, part ID or size is invalid.');}$ids[$part['bundle_id']]=true;}
    return $index;
}
function bixie_download_status(): array { return (array)get_option('bixie_media_download_state',[]); }
function bixie_download_start(): array {
    $index=bixie_release_index();if(!$index['parts']){throw new RuntimeException('This code package has no published media download index yet. Use verified local media parts, or install the final release code package when its media is available.');}
    $fingerprint=hash('sha256',wp_json_encode($index));$state=bixie_download_status();if(($state['fingerprint']??'')===$fingerprint&&($state['status']??'')==='running'){return $state;}
    $state=['status'=>'running','release'=>sanitize_text_field($index['release']??''),'fingerprint'=>$fingerprint,'cursor'=>0,'total'=>count($index['parts']),'started'=>gmdate('c'),'error'=>''];update_option('bixie_media_download_state',$state,false);return $state;
}
function bixie_fetch_release_part(array $part): array {
    if(!bixie_release_url_allowed((string)($part['url']??''))){throw new RuntimeException('Media download destination is not trusted.');}
    $temp=wp_tempnam('bixie-media-part.zip');if(!$temp){throw new RuntimeException('Cannot create a temporary media download.');}
    try{
        $url=$part['url'];$response=null;
        for($redirect=0;$redirect<3;$redirect++){
            if(!bixie_release_url_allowed($url)){throw new RuntimeException('Media download redirect is not trusted.');}
            $response=wp_safe_remote_get($url,['stream'=>true,'filename'=>$temp,'sslverify'=>true,'redirection'=>0,'timeout'=>45,'limit_response_size'=>25*MB_IN_BYTES+1,'reject_unsafe_urls'=>true]);
            if(is_wp_error($response)){throw new RuntimeException('Media download failed: '.$response->get_error_message());}
            $status=wp_remote_retrieve_response_code($response);
            if(in_array($status,[301,302,303,307,308],true)){$location=(string)wp_remote_retrieve_header($response,'location');if(str_starts_with($location,'/')){$parsed=wp_parse_url($url);$location='https://'.$parsed['host'].$location;}if(!$location||!bixie_release_url_allowed($location)){throw new RuntimeException('Media download redirect left the trusted release hosts.');}$url=$location;continue;}
            if($status!==200){throw new RuntimeException('Media download returned HTTP '.absint($status).'. Retry later or upload the matching local part.');}break;
        }
        if(!$response||wp_remote_retrieve_response_code($response)!==200){throw new RuntimeException('Too many media download redirects.');}
        clearstatcache(true,$temp);$bytes=is_file($temp)?filesize($temp):0;
        if($bytes!==absint($part['bytes']??0)||$bytes>25*MB_IN_BYTES||!hash_equals(strtolower((string)($part['sha256']??'')),hash_file('sha256',$temp))){throw new RuntimeException('Downloaded media size or SHA-256 did not match the trusted release index. The file was rejected.');}
        $verified=bixie_verify_bundle_archive($temp,25*MB_IN_BYTES,(string)$part['bundle_id']);
        if($verified['bundle_id']!==$part['bundle_id']){throw new RuntimeException('Downloaded media part ID differs from its trusted index.');}
        return $verified;
    }finally{if(is_file($temp)){unlink($temp);}}
}
function bixie_download_step(): array {
    $token=wp_generate_uuid4();if(!add_option('bixie_media_download_lock',['token'=>$token,'created'=>time()],'',false)){$lock=get_option('bixie_media_download_lock');if(is_array($lock)&&time()-(int)($lock['created']??time())>300){delete_option('bixie_media_download_lock');if(!add_option('bixie_media_download_lock',['token'=>$token,'created'=>time()],'',false)){throw new RuntimeException('Another media download is active.');}}else{throw new RuntimeException('Another media download is active.');}}
    try{$state=bixie_download_status();if(($state['status']??'')!=='running'){return $state;}$index=bixie_release_index();if(hash('sha256',wp_json_encode($index))!==($state['fingerprint']??'')){throw new RuntimeException('The release index changed. Start a fresh download to reconcile it safely.');}
        if($state['cursor']<count($index['parts'])){$part=$index['parts'][$state['cursor']];$existing=((array)get_option('bixie_media_bundle_parts',[]))[$part['bundle_id']]??null;if(!$existing||!hash_equals((string)($existing['archive_sha256']??''),strtolower($part['sha256']))){bixie_fetch_release_part($part);} $state['cursor']++;$state['last_part']=$part['bundle_id'];$state['error']='';}
        if($state['cursor']>=count($index['parts'])){$state['status']='complete';$state['finished']=gmdate('c');}update_option('bixie_media_download_state',$state,false);return $state;
    }catch(Throwable $error){$state=bixie_download_status();$state['error']=sanitize_text_field($error->getMessage());update_option('bixie_media_download_state',$state,false);throw $error;}
    finally{$lock=get_option('bixie_media_download_lock');if(is_array($lock)&&($lock['token']??'')===$token){delete_option('bixie_media_download_lock');}}
}
foreach(['start','step','status'] as $operation){add_action('wp_ajax_bixie_media_download_'.$operation,static function()use($operation):void{bixie_bundle_authorize();try{$state=$operation==='start'?bixie_download_start():($operation==='step'?bixie_download_step():bixie_download_status());wp_send_json_success($state);}catch(Throwable $error){wp_send_json_error(['message'=>sanitize_text_field($error->getMessage())],400);}});}
function bixie_render_download_admin(): void {
    try{$index=bixie_release_index();$available=!empty($index['parts']);$problem='';}catch(Throwable $error){$available=false;$problem=$error->getMessage();}
    $state=bixie_download_status();?>
    <section id="bixie-release-download"><h2><?php esc_html_e('Download the package media','bixie-library');?></h2><p><?php esc_html_e('Download the trusted release parts and import the editable pages and complete reviewed looks with one action. Downloading starts only when you press the button. Work resumes one part at a time; existing owner edits are preserved unless you select the overwrite option above. Local ZIP-part uploads below remain available.','bixie-library');?></p>
    <?php if(!$available):?><p><?php echo esc_html($problem?:__('The published media index is not included in this code checkpoint yet. Local media ZIP parts can still be uploaded below.','bixie-library'));?></p><?php endif;?>
    <button id="bixie-download-start" type="button" class="button button-primary" <?php disabled(!$available);?>><?php esc_html_e('Download media and import package','bixie-library');?></button> <button id="bixie-download-pause" type="button" class="button" disabled><?php esc_html_e('Pause after this part','bixie-library');?></button><p id="bixie-download-status" role="status" aria-live="polite"></p><progress id="bixie-download-progress" max="<?php echo max(1,absint($state['total']??1));?>" value="<?php echo absint($state['cursor']??0);?>"></progress></section>
    <?php wp_enqueue_script('bixie-release-download',BIXIE_LIBRARY_URL.'assets/downloads.js',[],BIXIE_LIBRARY_VERSION,true);wp_add_inline_script('bixie-release-download','window.BixieDownloads='.wp_json_encode(['url'=>admin_url('admin-ajax.php'),'nonce'=>wp_create_nonce('bixie_media_bundles')]).';','before');
}
