<?php
/** Actual 80/current real-record SQL, HTTP REST, SSR and cached facet aliases. */
if (PHP_SAPI !== 'cli' || empty($argv[1])) { exit(2); }
$_SERVER['HTTP_HOST'] = '127.0.0.1:8767'; $_SERVER['SERVER_NAME'] = '127.0.0.1'; $_SERVER['REQUEST_URI'] = '/'; require $argv[1];
if (wp_get_environment_type() !== 'local' || (int) get_option('blog_public') !== 0 || untrailingslashit(home_url('/')) !== 'http://127.0.0.1:8767') { exit(2); }
$cache = get_transient('bixie_catalog_facets'); $checks = []; $report = ['scope' => 'Only actually imported approved production looks in separate local noindex WordPress. Actual SQL result sets, real HTTP REST and server-rendered GET filters, plus a cached facet list made from those same raw records. No synthetic looks or raw metadata changes.', 'checks' => [], 'observations' => [], 'passed' => false];
$ids = get_posts(['post_type'=>'bixie_look','post_status'=>'publish','posts_per_page'=>-1,'fields'=>'ids','orderby'=>'ID','order'=>'ASC']); $raw = [];
foreach ($ids as $id) { $raw[$id] = ['fringe'=>get_post_meta($id,'bixie_fringe',true),'colour'=>get_post_meta($id,'bixie_colour',true)]; }
$before_hash = hash('sha256',wp_json_encode($raw));
try {
    foreach (['fringe' => ['none','no-bangs','no bangs'], 'colour' => ['dark','black']] as $field => $aliases) {
        $expected = array_keys(array_filter($raw, static fn($record) => in_array($record[$field],$aliases,true))); sort($expected); if (!$expected) { throw new RuntimeException('Actual imported records do not exercise ' . $field . ' aliases.'); }
        foreach ($aliases as $value) {
            $results = bixie_query_looks([$field=>$value,'per_page'=>48]); $actual = array_column($results['items'],'id');
            for ($page=2;$page<=$results['pages'];$page++) { $actual=array_merge($actual,array_column(bixie_query_looks([$field=>$value,'per_page'=>48,'page'=>$page])['items'],'id')); } sort($actual);
            $checks[$field . ':' . $value . ':actualSQLCompleteSet'] = $actual === $expected && $results['total'] === count($expected);
            $url = add_query_arg([$field=>$value,'per_page'=>48],rest_url('bixie/v1/looks')); $response=wp_remote_get($url,['timeout'=>20]);
            $rest = !is_wp_error($response) ? json_decode(wp_remote_retrieve_body($response),true) : null;
            $checks[$field . ':' . $value . ':realHTTPRESTTotalAndFirstPage'] = !is_wp_error($response) && wp_remote_retrieve_response_code($response)===200 && ($rest['total']??-1)===count($expected) && count($rest['items']??[])===min(48,count($expected));
            $http=wp_remote_get(add_query_arg($field,$value,bixie_package_page_url('looks','/looks/')),['timeout'=>20]); $html=!is_wp_error($http)?wp_remote_retrieve_body($http):'';
            $tags=new WP_HTML_Tag_Processor($html);$cards=[];while($tags->next_tag('ARTICLE')){if($tags->has_class('bixie-look-card')){$cards[]=(int)$tags->get_attribute('data-look');}}
            $checks[$field . ':' . $value . ':realHTTPNonemptySSRMatchesActualRecords'] = !is_wp_error($http) && wp_remote_retrieve_response_code($http)===200 && count($cards)>0 && !array_diff($cards,$expected);
            $report['observations'][$field . ':' . $value] = ['actualMatchingApprovedLooks'=>count($expected),'actualHTTPRESTFirstPageLooks'=>count($rest['items']??[]),'actualServerRenderedCards'=>count($cards)];
        }
    }
    $raw_facets=[];foreach(['texture','length','fringe','colour'] as $field){$raw_facets[$field]=array_values(array_unique(array_map(static fn($id)=>get_post_meta($id,'bixie_'.$field,true),$ids)));}
    delete_transient('bixie_catalog_facets');$live=bixie_catalog_facets();set_transient('bixie_catalog_facets',$raw_facets,HOUR_IN_SECONDS);$cached=bixie_catalog_facets();
    foreach (['fringe'=>['canonical'=>'none','alias'=>'no-bangs'],'colour'=>['canonical'=>'dark','alias'=>'black']] as $field=>$values) {
        $checks[$field . ':liveFacetCanonicalOnly']=in_array($values['canonical'],$live[$field],true)&&!in_array($values['alias'],$live[$field],true);
        $checks[$field . ':cachedActualRawFacetCanonicalOnly']=in_array($values['canonical'],$cached[$field],true)&&!in_array($values['alias'],$cached[$field],true);
    }
    $after=[];foreach($ids as $id){$after[$id]=['fringe'=>get_post_meta($id,'bixie_fringe',true),'colour'=>get_post_meta($id,'bixie_colour',true)];}
    $checks['allRawActualOwnerMetadataUnchanged']=hash_equals($before_hash,hash('sha256',wp_json_encode($after)));
    $report['checks']=$checks;$report['actualPublishedLookCount']=count($ids);$report['passed']=!in_array(false,$checks,true);
} catch (Throwable $error) { $report['checks']=$checks;$report['failure']=$error->getMessage(); }
finally { if($cache===false){delete_transient('bixie_catalog_facets');}else{set_transient('bixie_catalog_facets',$cache,HOUR_IN_SECONDS);} file_put_contents(__DIR__.'/wp-final-alias-report.json',wp_json_encode($report,JSON_PRETTY_PRINT|JSON_UNESCAPED_SLASHES)."\n");echo wp_json_encode($report,JSON_PRETTY_PRINT|JSON_UNESCAPED_SLASHES)."\n"; }
exit($report['passed']?0:1);
