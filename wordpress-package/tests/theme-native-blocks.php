<?php
/** Local test harness; never creates or publishes a WordPress post. */
$wp_root = getenv( 'BIXIE_WP_ROOT' ) ?: '/workspace/wp-test/wordpress';
require $wp_root . '/wp-load.php';
if ( ! function_exists( 'bixie_editorial_home_pattern' ) ) {
	require dirname( __DIR__ ) . '/theme/bixie-editorial/functions.php';
}
$empty = bixie_editorial_home_pattern();

// Use the one real, reviewed high-neck source only to exercise native Image
// serialization in memory. No attachment, post, or publication is created.
$fixture = dirname( __DIR__ ) . '/media/soft-layered-01.webp';
$fixture_filter = static function ( $path, $file ) use ( $fixture ) {
	return str_starts_with( $file, 'assets/images/home-' ) && is_file( $fixture ) ? $fixture : $path;
};
add_filter( 'theme_file_path', $fixture_filter, 10, 2 );
$filled = bixie_editorial_home_pattern();
remove_filter( 'theme_file_path', $fixture_filter, 10 );

$cases = array( 'empty_native_home' => $empty, 'image_serialization_fixture_only' => $filled );
$gallery_fixture = array();
for ( $n = 1; $n <= 4; $n++ ) {
	$gallery_fixture[] = array( 'image' => array( 'id' => 91000 + $n, 'url' => 'https://example.invalid/serialization-image-' . $n . '.webp', 'alt' => 'Serialization-only gallery fixture, never imported or published.' ), 'title' => 'Native gallery fixture ' . $n, 'permalink' => 'https://example.invalid/serialization-look-' . $n . '/' );
}
$cases['native_gallery_serialization_only'] = bixie_editorial_photo_gallery( $gallery_fixture, 'Native editable gallery fixture', 4 );
$cases['native_video_serialization_only'] = bixie_editorial_block( 'video', array( 'autoplay' => true, 'controls' => true, 'loop' => true, 'muted' => true, 'playsInline' => true, 'poster' => 'https://example.invalid/poster.webp', 'preload' => 'metadata', 'className' => 'bixie-film' ), '<figure class="wp-block-video bixie-film"><video autoplay controls loop muted poster="https://example.invalid/poster.webp" src="https://example.invalid/serialization-only.mp4" playsinline></video></figure>' );
foreach ( array( 'header', 'footer' ) as $part ) {
	ob_start();
	include dirname( __DIR__ ) . '/theme/bixie-editorial/patterns/' . $part . '.php';
	$cases[ $part ] = ob_get_clean();
}

wp_enqueue_script( 'wp-block-library' );
wp_enqueue_script( 'wp-blocks' );
?><!doctype html><html><head><meta charset="utf-8"><title>Native block serialization check</title><?php wp_head(); ?></head><body>
<p>Local native-block serialization test. This page has no published hairstyle media.</p>
<?php wp_footer(); ?>
<script>
wp.blockLibrary.registerCoreBlocks();
['library','finder','look-meta','saved-looks'].forEach(function(name){
 if(!wp.blocks.getBlockType('bixie/'+name))wp.blocks.registerBlockType('bixie/'+name,{title:'Test registration only',category:'widgets',attributes:{perPage:{type:'number'}},edit:function(){return null;},save:function(){return null;}});
});
const cases=<?php echo wp_json_encode( $cases, JSON_HEX_TAG | JSON_HEX_AMP | JSON_HEX_APOS | JSON_HEX_QUOT ); ?>;
window.themeNativeValidation={cases:{},limitations:['Serialization-only media fixture never imported or published. Native-quality photography, actual video playback and the full public site remain separately gated.']};
function flatten(blocks,result=[]){blocks.forEach(function(b){result.push(b);flatten(b.innerBlocks,result);});return result;}
Object.entries(cases).forEach(function([name,content]){
 const blocks=wp.blocks.parse(content),all=flatten(blocks);
 window.themeNativeValidation.cases[name]={total:all.length,invalid:all.filter(b=>b.isValid===false).map(b=>({name:b.name,attrs:b.attributes,original:b.originalContent,issues:b.validationIssues.map(i=>({message:i.args[0],generated:typeof i.args[i.args.length-2]==='string'?i.args[i.args.length-2]:null}))})),images:all.filter(b=>b.name==='core/image').length,sections:all.filter(b=>b.name==='core/group'&&b.attributes.tagName==='section').length,headingsOne:all.filter(b=>b.name==='core/heading'&&b.attributes.level===1).length};
});
</script></body></html>
