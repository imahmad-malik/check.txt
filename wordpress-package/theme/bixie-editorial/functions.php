<?php
/** Theme setup and native pattern helpers. */
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

add_action( 'after_setup_theme', function () {
	add_theme_support( 'editor-styles' );
	add_editor_style( 'assets/css/editorial.css' );
	add_theme_support( 'post-thumbnails' );
	add_theme_support( 'responsive-embeds' );
	add_theme_support( 'wp-block-styles' );
	add_theme_support( 'title-tag' );
	register_block_pattern_category( 'bixie-editorial', array( 'label' => __( 'Bixie Editorial', 'bixie-editorial' ) ) );
} );

add_action( 'wp_enqueue_scripts', function () {
	$version = wp_get_theme()->get( 'Version' );
	wp_enqueue_style( 'bixie-editorial', get_theme_file_uri( 'assets/css/editorial.css' ), array(), $version );
	wp_enqueue_script( 'bixie-editorial', get_theme_file_uri( 'assets/js/editorial.js' ), array(), $version, true );
	wp_script_add_data( 'bixie-editorial', 'strategy', 'defer' );
	$motion = array(
		'motionEnabled' => (bool) get_option( 'bixie_motion_enabled', true ),
		'motionSpeed' => max( 5, min( 36, (int) get_option( 'bixie_motion_speed', 15 ) ) ),
		'videoAutoplay' => (bool) get_option( 'bixie_video_autoplay', true ),
		'photoPlayLabel' => get_option( 'bixie_motion_play_label', 'Play photo motion' ),
		'photoNextLabel' => get_option( 'bixie_motion_next_label', 'Show next photographs' ),
		'filmPauseLabel' => get_option( 'bixie_film_pause_label', 'Pause film' ),
	);
	wp_add_inline_script( 'bixie-editorial', 'window.BixieEditorialSettings=' . wp_json_encode( $motion ) . ';', 'before' );
} );

/** Return an imported media ID when the companion importer has assigned it. */
function bixie_editorial_media_id( $key ) {
	return function_exists( 'bixie_get_package_attachment' ) ? (int) bixie_get_package_attachment( $key ) : 0;
}

/** Local theme media remains usable before companion content has been imported. */
function bixie_editorial_media_url( $key ) {
	$id = bixie_editorial_media_id( $key );
	if ( $id ) {
		$url = wp_get_attachment_image_url( $id, 'full' );
		if ( $url ) {
			return $url;
		}
	}
	return get_theme_file_uri( 'assets/images/' . sanitize_file_name( $key ) . '.webp' );
}

/** Serialize standard block comments without hiding content inside a shortcode. */
function bixie_editorial_block( $name, $attrs, $content = null ) {
	$json = $attrs ? ' ' . wp_json_encode( $attrs, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE ) : '';
	if ( null === $content ) {
		return '<!-- wp:' . $name . $json . ' /-->' . "\n";
	}
	return '<!-- wp:' . $name . $json . ' -->' . "\n" . $content . "\n" . '<!-- /wp:' . $name . ' -->' . "\n";
}

function bixie_editorial_group( $content, $class = '', $name = '', $tag = 'div', $anchor = '' ) {
	$attrs = array( 'className' => $class, 'layout' => array( 'type' => 'default' ) );
	if ( $name ) {
		$attrs['metadata'] = array( 'name' => $name );
	}
	if ( 'div' !== $tag ) {
		$attrs['tagName'] = $tag;
	}
	if ( $anchor ) {
		$attrs['anchor'] = $anchor;
	}
	return bixie_editorial_block( 'group', $attrs, '<' . $tag . ( $anchor ? ' id="' . esc_attr( $anchor ) . '"' : '' ) . ' class="wp-block-group ' . esc_attr( $class ) . '">' . $content . '</' . $tag . '>' );
}

function bixie_editorial_heading( $text, $level = 2, $class = '' ) {
	return bixie_editorial_block( 'heading', array( 'level' => $level, 'className' => $class ), '<h' . $level . ' class="wp-block-heading' . ( $class ? ' ' . esc_attr( $class ) : '' ) . '">' . wp_kses_post( $text ) . '</h' . $level . '>' );
}

function bixie_editorial_paragraph( $text, $class = '' ) {
	return bixie_editorial_block( 'paragraph', $class ? array( 'className' => $class ) : array(), '<p' . ( $class ? ' class="' . esc_attr( $class ) . '"' : '' ) . '>' . wp_kses_post( $text ) . '</p>' );
}

function bixie_editorial_button( $text, $path, $class = '' ) {
	$link = home_url( $path );
	return bixie_editorial_block( 'buttons', array(), '<div class="wp-block-buttons">' . bixie_editorial_block( 'button', $class ? array( 'className' => $class ) : array(), '<div class="wp-block-button' . ( $class ? ' ' . esc_attr( $class ) : '' ) . '"><a class="wp-block-button__link wp-element-button" href="' . esc_url( $link ) . '">' . esc_html( $text ) . '</a></div>' ) . '</div>' );
}

/** Every photograph is a real editable core/image block. */
function bixie_editorial_image( $key, $alt, $caption = '', $class = '', $path = '' ) {
	$id = bixie_editorial_media_id( $key );
	$attrs = array( 'sizeSlug' => 'full', 'linkDestination' => $path ? 'custom' : 'none', 'className' => $class );
	if ( $id ) {
		$attrs['id'] = $id;
	}
	$attrs['metadata'] = array( 'name' => $key );
	if ( ! $id && ! is_file( get_theme_file_path( 'assets/images/' . sanitize_file_name( $key ) . '.webp' ) ) ) {
		// An empty native image is editable in the editor. Missing photography is
		// never replaced with a rejected photo or a fake public placeholder.
		return bixie_editorial_block( 'image', $attrs, '<figure class="wp-block-image size-full' . ( $class ? ' ' . esc_attr( $class ) : '' ) . '"><img alt=""/></figure>' );
	}
	$attrs['lightbox'] = array( 'enabled' => ! $path );
	$url = bixie_editorial_media_url( $key );
	$image = '<img src="' . esc_url( $url ) . '" alt="' . esc_attr( $alt ) . '"' . ( $id ? ' class="wp-image-' . $id . '"' : '' ) . '/>';
	if ( $path ) {
		$image = '<a href="' . esc_url( home_url( $path ) ) . '">' . $image . '</a>';
		$attrs['href'] = home_url( $path );
	}
	if ( $caption ) {
		$image .= '<figcaption class="wp-element-caption">' . wp_kses_post( $caption ) . '</figcaption>';
	}
	return bixie_editorial_block( 'image', $attrs, '<figure class="wp-block-image size-full' . ( $class ? ' ' . esc_attr( $class ) : '' ) . '">' . $image . '</figure>' );
}

function bixie_editorial_intro( $number, $title, $description = '' ) {
	return bixie_editorial_group( bixie_editorial_paragraph( $number, 'bixie-number' ) . bixie_editorial_heading( $title ) . ( $description ? bixie_editorial_paragraph( $description ) : '' ), 'bixie-section-intro' );
}

function bixie_editorial_note( $title, $text, $path = '', $link_text = 'Read the guide' ) {
	return bixie_editorial_group( bixie_editorial_heading( $title, 3 ) . bixie_editorial_paragraph( $text ) . ( $path ? bixie_editorial_button( $link_text, $path, 'is-style-outline' ) : '' ), 'bixie-field-note' );
}

require_once __DIR__ . '/inc/photo-shelves.php';
require_once __DIR__ . '/inc/home-pattern.php';

add_filter( 'bixie_import_page_content', function ( $content, $page, $state ) {
	$slug = isset( $page['slug'] ) ? $page['slug'] : '';
	if ( in_array( $slug, array( 'home', 'homepage' ), true ) || ! empty( $page['is_front_page'] ) ) {
		return bixie_editorial_home_pattern();
	}
	return $content;
}, 10, 3 );

/** Owner settings take effect before a native video reaches the browser. */
add_filter( 'render_block_core/video', function ( $content ) {
	if ( get_option( 'bixie_motion_enabled', true ) && get_option( 'bixie_video_autoplay', true ) ) {
		return $content;
	}
	$tags = new WP_HTML_Tag_Processor( $content );
	while ( $tags->next_tag( 'VIDEO' ) ) {
		$tags->remove_attribute( 'autoplay' );
	}
	return $tags->get_updated_html();
} );

/** Only imported local project pages qualify for the public draft-link gate. */
function bixie_editorial_is_project_draft_url( $url ) {
	$target = wp_parse_url( html_entity_decode( (string) $url, ENT_QUOTES, 'UTF-8' ) );
	$site = wp_parse_url( home_url( '/' ) );
	if ( ! is_array( $target ) || empty( $target['path'] ) ) {
		return false;
	}
	if ( empty( $target['host'] ) && '/' !== substr( $target['path'], 0, 1 ) ) {
		return false;
	}
	if ( ! empty( $target['scheme'] ) && ! in_array( strtolower( $target['scheme'] ), array( 'http', 'https' ), true ) ) {
		return false;
	}
	if ( ! empty( $target['host'] ) && ( strtolower( $target['host'] ) !== strtolower( $site['host'] ) || (int) ( $target['port'] ?? 0 ) !== (int) ( $site['port'] ?? 0 ) ) ) {
		return false;
	}
	$path = trim( rawurldecode( $target['path'] ), '/' );
	$base = trim( $site['path'] ?? '', '/' );
	if ( $base ) {
		if ( 0 !== strpos( $path, $base . '/' ) ) {
			return false;
		}
		$path = substr( $path, strlen( $base ) + 1 );
	}
	$page = get_page_by_path( $path, OBJECT, 'page' );
	return $page && get_post_meta( $page->ID, '_bixie_import_key', true ) && 'publish' !== get_post_status( $page );
}

/** Render-time only: editor blocks and stored owner content remain intact. */
add_filter( 'render_block', function ( $content, $block ) {
	if ( is_admin() || ( defined( 'REST_REQUEST' ) && REST_REQUEST ) || ! in_array( $block['blockName'] ?? '', array( 'core/paragraph', 'core/heading', 'core/list-item', 'core/button', 'core/navigation-link', 'core/image' ), true ) ) {
		return $content;
	}
	$tags = new WP_HTML_Tag_Processor( $content );
	$anchors = 0;
	$blocked = 0;
	while ( $tags->next_tag( 'A' ) ) {
		$anchors++;
		if ( ! bixie_editorial_is_project_draft_url( $tags->get_attribute( 'href' ) ) ) {
			continue;
		}
		$blocked++;
		foreach ( array( 'href', 'target', 'rel', 'role', 'tabindex' ) as $attribute ) {
			$tags->remove_attribute( $attribute );
		}
		$tags->set_attribute( 'data-bixie-unpublished-link', 'true' );
	}
	if ( ! $blocked ) {
		return $content;
	}
	if ( $blocked === $anchors && in_array( $block['blockName'], array( 'core/button', 'core/navigation-link' ), true ) ) {
		return '';
	}
	if ( 1 === $anchors && 1 === $blocked && 'core/paragraph' === $block['blockName'] && preg_match( '~^\s*<p\b[^>]*>\s*<a\b[^>]*>.*?</a>\s*</p>\s*$~s', $content ) ) {
		return '';
	}
	return preg_replace_callback( '~<a\b([^>]*\bdata-bixie-unpublished-link="true"[^>]*)>(.*?)</a>~is', function ( $match ) {
		$attributes = preg_replace( '~\s*data-bixie-unpublished-link="true"~', '', $match[1] );
		return '<span' . $attributes . '>' . $match[2] . '</span>';
	}, $tags->get_updated_html() );
}, 30, 2 );
