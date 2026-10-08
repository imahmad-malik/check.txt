<?php
/** Real actual-source SQL, public REST and native GET aliases, without raw edits. */
if (PHP_SAPI !== 'cli' || empty($argv[1])) { exit(2); }
$_SERVER['HTTP_HOST'] = '127.0.0.1:8767'; $_SERVER['SERVER_NAME'] = '127.0.0.1'; $_SERVER['REQUEST_URI'] = '/';
require $argv[1];
if (wp_get_environment_type() !== 'local' || (int) get_option('blog_public') !== 0 || untrailingslashit(home_url('/')) !== 'http://127.0.0.1:8767') { exit(2); }
$report = ['scope' => 'Actual current production look records in the separate local noindex site. Independent raw SQL expectations, real HTTP REST/GET filtering and native facet cache; no metadata edits or synthetic fixtures.', 'checks' => [], 'variants' => [], 'passed' => false];
$posts = get_posts(['post_type'=>'bixie_look','post_status'=>'publish','posts_per_page'=>-1,'orderby'=>['menu_order'=>'ASC','ID'=>'ASC']]);
$before = []; foreach ($posts as $post) { $before[$post->ID] = ['fringe'=>get_post_meta($post->ID,'bixie_fringe',true),'colour'=>get_post_meta($post->ID,'bixie_colour',true)]; }
$report['actualPublishedLooks'] = count($posts);
$groups = ['fringe' => ['canonical'=>'none','aliases'=>['none','no-bangs','no bangs']], 'colour' => ['canonical'=>'dark','aliases'=>['dark','black']]];
$hub = bixie_package_page_url('looks','/looks/');
try {
    foreach ($groups as $field=>$group) {
        $expected = []; foreach ($before as $id=>$metadata) { if (in_array(strtolower($metadata[$field]),$group['aliases'],true)) { $expected[]=$id; } }
        if (!$expected) { throw new RuntimeException('The actual source set has no positive '.$field.' alias sample.'); }
        foreach ($group['aliases'] as $alias) {
            $query = bixie_query_looks([$field=>$alias,'per_page'=>48]); $ids=array_column($query['items'],'id');
            if ($query['total']!==count($expected) || $ids!==array_slice($expected,0,48)) { throw new RuntimeException('Actual SQL filtering mismatch for '.$field.'='.$alias); }
            $url=add_query_arg([$field=>$alias,'per_page'=>48],rest_url('bixie/v1/looks')); $response=wp_remote_get($url,['timeout'=>20]);
            if (is_wp_error($response) || wp_remote_retrieve_response_code($response)!==200) { throw new RuntimeException('Actual public REST alias request failed.'); }
            $json=json_decode(wp_remote_retrieve_body($response),true,512,JSON_THROW_ON_ERROR);
            if ($json['total']!==count($expected) || array_column($json['items'],'id')!==array_slice($expected,0,48)) { throw new RuntimeException('Actual public REST alias IDs mismatch.'); }
            $response=wp_remote_get(add_query_arg($field,$alias,$hub),['timeout'=>20]);
            if (is_wp_error($response) || wp_remote_retrieve_response_code($response)!==200) { throw new RuntimeException('Actual native GET alias request failed.'); }
            $html=wp_remote_retrieve_body($response);$tags=new WP_HTML_Tag_Processor($html);$rendered=[];
            while ($tags->next_tag('ARTICLE')) { if ($tags->has_class('bixie-look-card')) {$rendered[]=absint($tags->get_attribute('data-look'));} }
            if (!$rendered || $rendered!==array_slice($expected,0,count($rendered))) { throw new RuntimeException('Native GET alias first-page actual card IDs mismatch.'); }
            $select_pattern='~<select\b[^>]*name="'.preg_quote($field,'~').'"[^>]*>(.*?)</select>~s';
            if (!preg_match($select_pattern,$html,$select) || !preg_match('~<option\b[^>]*value="'.preg_quote($group['canonical'],'~').'"[^>]*selected~',$select[1])) { throw new RuntimeException('Native GET did not retain canonical selected facet.'); }
            $report['variants'][$field.'='.$alias]=['positiveActualMatches'=>count($expected),'realSQLIDsMatch'=>true,'realHTTPRESTStatus'=>200,'realRESTIDsMatch'=>true,'realNativeGETStatus'=>200,'nativeRenderedCardCount'=>count($rendered),'selectedCanonicalFacet'=>$group['canonical']];
        }
    }
    $facets=bixie_catalog_facets();
    $report['checks']['allFiveAliasVariantsUseSamePositiveActualRecordsAcrossSQLRESTAndNativeGET']=count($report['variants'])===5;
    $report['checks']['actualFacetListsExposeCanonicalNoneAndDarkOnce']=count(array_keys($facets['fringe'],'none',true))===1 && count(array_keys($facets['colour'],'dark',true))===1 && !array_intersect($facets['fringe'],['no-bangs','no bangs']) && !in_array('black',$facets['colour'],true);
    $after=[];foreach($posts as $post){$after[$post->ID]=['fringe'=>get_post_meta($post->ID,'bixie_fringe',true),'colour'=>get_post_meta($post->ID,'bixie_colour',true)];}
    $report['checks']['allActualOwnerRawMetadataRemainsIdentical']=$before===$after;
    $report['passed']=!in_array(false,$report['checks'],true);
} catch (Throwable $error) { $report['failure']=$error->getMessage(); }
file_put_contents(__DIR__.'/wp-final-alias-report.json',wp_json_encode($report,JSON_PRETTY_PRINT|JSON_UNESCAPED_SLASHES)."\n");echo wp_json_encode($report,JSON_PRETTY_PRINT|JSON_UNESCAPED_SLASHES)."\n";exit($report['passed']?0:1);
