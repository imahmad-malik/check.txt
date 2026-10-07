<?php
/**
 * Title: Bixie navigation
 * Slug: bixie-editorial/header
 * Categories: bixie-editorial, header
 * Block Types: core/template-part/header
 * Inserter: yes
 */
$nav = '';
foreach ( array( '/collections/' => 'Collections', '/looks/' => 'Photo library', '/find-your-bixie/' => 'Find your bixie', '/guides/' => 'Hair guides', '/saved-looks/' => 'Saved looks' ) as $path => $label ) {
	$nav .= bixie_editorial_block( 'navigation-link', array( 'label' => $label, 'url' => home_url( $path ), 'kind' => 'custom', 'isTopLevelLink' => true ) );
}
$navigation = bixie_editorial_block( 'navigation', array( 'overlayMenu' => 'mobile', 'className' => 'bixie-nav', 'layout' => array( 'type' => 'flex', 'justifyContent' => 'right' ) ), $nav );
$branding = bixie_editorial_group( bixie_editorial_block( 'site-title', array( 'level' => 0, 'className' => 'bixie-logo' ) ) . bixie_editorial_paragraph( 'THE SHORT HAIR PHOTO EDIT', 'bixie-eyebrow' ), 'bixie-branding' );
echo bixie_editorial_group( bixie_editorial_group( $branding . $navigation, 'bixie-header-inner' ), 'bixie-site-header', 'Site navigation', 'header' ); // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped
