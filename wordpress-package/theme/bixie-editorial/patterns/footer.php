<?php
/**
 * Title: Bixie footer
 * Slug: bixie-editorial/footer
 * Categories: bixie-editorial, footer
 * Block Types: core/template-part/footer
 * Inserter: yes
 */
$links = '';
foreach ( array( '/collections/' => 'Photo collections', '/looks/' => 'All haircut looks', '/guides/' => 'The haircut guides', '/about/' => 'About the edit', '/disclaimer/' => 'Editorial disclaimer', '/image-policy/' => 'Image policy', '/privacy/' => 'Privacy', '/contact/' => 'Contact' ) as $path => $label ) {
	$links .= bixie_editorial_paragraph( '<a href="' . esc_url( home_url( $path ) ) . '">' . esc_html( $label ) . '</a>' );
}
$footer = bixie_editorial_group( bixie_editorial_heading( 'BIXIE HAIRCUT', 2, 'bixie-logo' ) . bixie_editorial_paragraph( 'A photograph-led collection of short hair shapes, from softly layered to closely tapered.' ), 'bixie-footer-branding' );
$footer .= bixie_editorial_group( $links, 'bixie-link-grid' );
$footer .= bixie_editorial_paragraph( 'All hairstyle photographs depict fictional adults and are original generated images. They are visual references, not salon client results. Cut and care decisions are best made with a qualified hairstylist.', 'bixie-caption' );
echo bixie_editorial_group( $footer, 'bixie-footer', 'Footer', 'footer' ); // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped
