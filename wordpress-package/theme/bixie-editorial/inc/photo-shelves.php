<?php
/** Curated shelves become ordinary native Gallery/Image blocks at import. */
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

function bixie_editorial_select_photos( $collection, $count, &$used_media, &$used_looks ) {
	if ( ! function_exists( 'bixie_get_look_images' ) || ! taxonomy_exists( 'bixie_collection' ) ) {
		return array();
	}
	$posts = get_posts( array( 'post_type' => 'bixie_look', 'post_status' => 'publish', 'posts_per_page' => 100, 'orderby' => array( 'menu_order' => 'ASC', 'title' => 'ASC' ), 'tax_query' => array( array( 'taxonomy' => 'bixie_collection', 'field' => 'slug', 'terms' => $collection ) ) ) );
	$photos = array();
	foreach ( $posts as $post ) {
		if ( function_exists( 'bixie_check_look' ) && ! bixie_check_look( $post->ID )['complete'] ) {
			continue;
		}
		foreach ( bixie_get_look_images( $post->ID ) as $image ) {
			$id = (int) ( $image['id'] ?? 0 );
			if ( 'front' !== ( $image['angle'] ?? '' ) || ! $id || in_array( $id, $used_media, true ) ) {
				continue;
			}
			$used_media[] = $id;
			$used_looks[] = $post->ID;
			$photos[] = array( 'image' => $image, 'title' => get_the_title( $post ), 'permalink' => get_permalink( $post ) );
			break;
		}
		if ( count( $photos ) >= $count ) {
			break;
		}
	}
	return $photos;
}

function bixie_editorial_photo_gallery( $photos, $name, $columns = 3 ) {
	$content = '';
	foreach ( $photos as $photo ) {
		$image = $photo['image'];
		$id = (int) $image['id'];
		$attrs = array( 'id' => $id, 'sizeSlug' => 'full', 'linkDestination' => 'custom', 'href' => $photo['permalink'], 'lightbox' => array( 'enabled' => false ) );
		$figure = '<figure class="wp-block-image size-full"><a href="' . esc_url( $photo['permalink'] ) . '"><img src="' . esc_url( $image['url'] ) . '" alt="' . esc_attr( $image['alt'] ) . '" class="wp-image-' . $id . '"/></a><figcaption class="wp-element-caption">' . esc_html( $photo['title'] ) . '</figcaption></figure>';
		$content .= bixie_editorial_block( 'image', $attrs, $figure );
	}
	return bixie_editorial_block( 'gallery', array( 'columns' => $columns, 'imageCrop' => false, 'linkTo' => 'custom', 'className' => 'bixie-gallery-strip bixie-photo-shelf', 'metadata' => array( 'name' => $name ) ), '<figure class="wp-block-gallery has-nested-images columns-' . $columns . ' bixie-gallery-strip bixie-photo-shelf">' . $content . '</figure>' );
}

function bixie_editorial_photo_section( $number, $title, $description, $photos, $path, $name, $class = '' ) {
	$content = bixie_editorial_intro( $number, $title, $description );
	$content .= bixie_editorial_photo_gallery( $photos, $name );
	$content .= bixie_editorial_button( 'Open the photo collection', $path, 'is-style-outline' );
	return bixie_editorial_group( $content, 'bixie-section bixie-photo-shelf-section ' . $class, $name, 'section' );
}
