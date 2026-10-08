<?php
/** The home page is ordinary Gutenberg content, not a hidden template renderer. */
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

function bixie_editorial_home_pattern() {
	$sections = '';
	$used_media = array_filter( array_map( 'bixie_editorial_media_id', (array) get_option( 'bixie_required_home_media', array() ) ) );
	$used_looks = array();
	$shelves = array();
	foreach ( array( 'classic' => 7, 'short' => 4, 'long' => 4, 'round-face' => 6, 'fine-hair' => 3, 'thin-hair' => 3, 'easy-styling' => 6, '90s-inspired' => 6, 'shaggy' => 6 ) as $collection => $count ) {
		$shelves[ $collection ] = bixie_editorial_select_photos( $collection, $count, $used_media, $used_looks );
	}

	$hero_copy = bixie_editorial_paragraph( 'THE BIXIE HAIRCUT COLLECTION', 'bixie-eyebrow' );
	$hero_copy .= bixie_editorial_heading( 'Bixie, in<br><em>every direction.</em>', 1 );
	$hero_copy .= bixie_editorial_paragraph( 'The softness of a bob. The ease of a pixie. Explore the shape from the front, the side and the back before choosing your next cut.', 'bixie-hero-deck' );
	$hero_copy .= bixie_editorial_button( 'Explore the photo library', '/looks/' );
	$hero_copy .= bixie_editorial_paragraph( 'Browse by texture, length, fringe, age and colour.<br>Save the shapes that feel like you.', 'bixie-caption' );
	$hero = bixie_editorial_group( $hero_copy, 'bixie-hero-copy' );
	$hero .= bixie_editorial_image( 'home-hero', 'Fictional adult with a softly layered chestnut bixie, complete head and shoulders visible, wearing an opaque high-neck top.', '01 / SOFT LAYERS · A rounded crown, lighter ends, an easy outline.', 'bixie-hero-image', '/collections/layered/' );
	$sections .= bixie_editorial_group( bixie_editorial_group( $hero, 'bixie-hero-grid' ), 'bixie-hero bixie-section', '01 · Opening edit', 'section' );

	$browse = bixie_editorial_paragraph( 'START WITH A DETAIL', 'bixie-eyebrow' );
	$browse .= bixie_editorial_group( bixie_editorial_paragraph( '<a href="' . esc_url( home_url( '/collections/fine-hair/' ) ) . '">Fine hair</a>' ) . bixie_editorial_paragraph( '<a href="' . esc_url( home_url( '/collections/curly/' ) ) . '">Curly shapes</a>' ) . bixie_editorial_paragraph( '<a href="' . esc_url( home_url( '/collections/bangs/' ) ) . '">A fringe</a>' ) . bixie_editorial_paragraph( '<a href="' . esc_url( home_url( '/collections/over-50/' ) ) . '">Over 50</a>' ) . bixie_editorial_paragraph( '<a href="' . esc_url( home_url( '/collections/long/' ) ) . '">More length</a>' ), 'bixie-link-grid' );
	$sections .= bixie_editorial_group( $browse, 'bixie-section bixie-quick-browse', '02 · Browse by detail', 'section' );

	$rail = bixie_editorial_intro( '01 / THE MOVING EDIT', 'Four shapes. Different moods.', 'Watch the whole silhouette. Open a photograph to look more closely; pause the row whenever you like.' );
	$rail_items = '';
	foreach ( array( 'feathered' => array( 'Feathered edges', 'feathered' ), 'curly' => array( 'Curly and sculptural', 'curly' ), 'short' => array( 'A closer nape', 'short' ), 'long' => array( 'Longer at the temples', 'long' ) ) as $key => $item ) {
		$rail_items .= bixie_editorial_image( 'home-rail-' . $key, 'Fictional adult with ' . strtolower( $item[0] ) . ' in a complete uncropped haircut portrait and opaque high-neck clothing.', $item[0], 'bixie-photo-item', '/collections/' . $item[1] . '/' );
	}
	$rail .= bixie_editorial_group( bixie_editorial_group( $rail_items, 'bixie-photo-track' ), 'bixie-photo-row', '', 'div', 'photo-flow' );
	$rail .= bixie_editorial_group( bixie_editorial_button( 'Pause photographs', '/#photo-flow', 'bixie-photo-motion-toggle' ) . bixie_editorial_paragraph( 'Motion follows your device preferences.', 'bixie-caption' ), 'bixie-motion-controls' );
	$sections .= bixie_editorial_group( $rail, 'bixie-section', '03 · Moving photo collection', 'section' );

	$sections .= bixie_editorial_photo_section( '02 / THE CLASSIC OUTLINE', 'The bob-pixie balance.', 'A short nape, a softer crown and enough length around the face. Open each photograph for its complete gallery.', $shelves['classic'], '/collections/classic/', '04 · Classic bixie photo shelf', 'is-moss' );

	$textures = bixie_editorial_intro( '03 / NATURAL TEXTURE', 'Begin with the hair you have.', 'Texture is a useful starting point, not a promise of identical results. See the collection, then discuss your density and daily routine with your stylist.' );
	$texture_items = '';
	foreach ( array( 'fine' => array( 'Fine hair', 'fine-hair', 'Lift without losing the outline.' ), 'wavy' => array( 'Wavy hair', 'wavy', 'Leave room for a natural bend.' ), 'thick' => array( 'Thick hair', 'thick-hair', 'Manage weight through the crown.' ), 'straight' => array( 'Straight hair', 'straight', 'Clean lines and gentle layers.' ) ) as $key => $item ) {
		$texture_items .= bixie_editorial_group( bixie_editorial_image( 'home-texture-' . $key, 'Fictional adult with a bixie for ' . strtolower( $item[0] ) . ', full head and shoulders visible in high-neck clothing.', '', '', '/collections/' . $item[1] . '/' ) . bixie_editorial_heading( '<a href="' . esc_url( home_url( '/collections/' . $item[1] . '/' ) ) . '">' . $item[0] . '</a>', 3 ) . bixie_editorial_paragraph( $item[2], 'bixie-caption' ), 'bixie-collection-card' );
	}
	$textures .= bixie_editorial_group( $texture_items, 'bixie-collection-grid' );
	$sections .= bixie_editorial_group( $textures, 'bixie-section', '05 · Texture collections', 'section' );

	$finder = bixie_editorial_intro( '04 / YOUR STARTING POINT', 'Find the shape you want to explore.', 'Choose a few preferences. The finder takes you to actual photo collections and keeps the choice in your hands.' );
	$finder .= bixie_editorial_block( 'bixie/finder', array() );
	$sections .= bixie_editorial_group( $finder, 'bixie-section bixie-finder-section is-paper', '06 · Haircut finder', 'section' );

	$lengths = bixie_editorial_intro( '05 / THE LENGTH', 'Close at the nape.<br>Longer at the temples.', 'Explore both ends of the bixie range. Each photograph opens a complete look gallery.' );
	$lengths .= bixie_editorial_heading( 'Shorter shapes', 3 ) . bixie_editorial_photo_gallery( $shelves['short'], 'Short bixie shelf', 4 );
	$lengths .= bixie_editorial_button( 'Short bixie collection', '/collections/short/', 'is-style-outline' );
	$lengths .= bixie_editorial_heading( 'A little more length', 3 ) . bixie_editorial_photo_gallery( $shelves['long'], 'Long bixie shelf', 4 );
	$lengths .= bixie_editorial_button( 'Long bixie collection', '/collections/long/', 'is-style-outline' );
	$sections .= bixie_editorial_group( $lengths, 'bixie-section bixie-length-photos', '07 · Short and long photo shelves', 'section' );

	$library = bixie_editorial_intro( '06 / THE PHOTO LIBRARY', 'Look closely. Save thoughtfully.', 'Open a haircut to see its photo gallery. Filter the collection, save your favourites, compare up to three shapes and print the references you want to discuss.' );
	$library .= bixie_editorial_block( 'bixie/library', array( 'perPage' => 8, 'excludeLookIds' => array_values( array_unique( $used_looks ) ) ) );
	$library .= bixie_editorial_button( 'View every haircut', '/looks/', 'is-style-outline' );
	$sections .= bixie_editorial_group( $library, 'bixie-section bixie-library-section is-paper', '08 · Filterable photo library', 'section' );

	$angles = bixie_editorial_intro( '07 / THE COMPLETE OUTLINE', 'A haircut has more than one view.', 'The front shows the fringe. The side shows the weight. The back shows the taper. Use all three when choosing your references.' );
	$angle_photos = '';
	foreach ( array( 'front' => 'Front / the fringe and face frame', 'side' => 'Side / the crown and perimeter', 'back' => 'Back / the nape and taper' ) as $key => $caption ) {
		$angle_photos .= bixie_editorial_image( 'home-angle-' . $key, 'The ' . $key . ' view of the same fictional adult and coherent layered bixie, in fully covered high-neck clothing.', $caption, 'bixie-angle-image' );
	}
	$angles .= bixie_editorial_block( 'gallery', array( 'columns' => 3, 'imageCrop' => false, 'linkTo' => 'none', 'className' => 'bixie-gallery-strip' ), '<figure class="wp-block-gallery has-nested-images columns-3 bixie-gallery-strip">' . $angle_photos . '</figure>' );
	$angles .= bixie_editorial_paragraph( 'These original generated views depict a fictional person. They are haircut references, not photographs of salon client work.', 'bixie-caption' );
	$sections .= bixie_editorial_group( $angles, 'bixie-section', '09 · Front, side and back', 'section' );

	$fringe = bixie_editorial_intro( '08 / THE FACE FRAME', 'Let the fringe set the mood.', 'A small change around the forehead can make the same length feel different. Each collection opens a photo gallery.' );
	$fringe_cards = '';
	foreach ( array( 'curtain' => array( 'Curtain bangs', '/looks/?fringe=curtain' ), 'side' => array( 'Side-swept fringe', '/looks/?fringe=side-swept' ), 'wispy' => array( 'Wispy bangs', '/looks/?fringe=wispy' ) ) as $key => $item ) {
		$fringe_cards .= bixie_editorial_group( bixie_editorial_image( 'home-fringe-' . $key, 'Fictional adult with a bixie and ' . strtolower( $item[0] ) . ', wearing a high-neck opaque top.', '', '', $item[1] ) . bixie_editorial_heading( '<a href="' . esc_url( home_url( $item[1] ) ) . '">' . $item[0] . '</a>', 3 ), 'bixie-collection-card' );
	}
	$fringe .= bixie_editorial_group( $fringe_cards, 'bixie-story-grid' );
	$sections .= bixie_editorial_group( $fringe, 'bixie-section is-paper', '10 · Fringe photo collections', 'section' );

	$sections .= bixie_editorial_photo_section( '09 / PROPORTION', 'Softness around the face.', 'Compare crown height, fringe direction and the length around the cheeks. Shape labels are a starting point, not a rule.', $shelves['round-face'], '/collections/round-face/', '11 · Face-framing photo shelf', 'is-moss' );

	$mature = bixie_editorial_intro( '10 / AT EVERY AGE', 'Good shape has no age limit.', 'Explore collections by age if they help you find relatable references. Texture, density, comfort and personal style matter more than a number.' );
	$mature_cards = '';
	foreach ( array( 'over40' => array( 'Over 40', 'over-40' ), 'over50' => array( 'Over 50', 'over-50' ), 'over60' => array( 'Over 60', 'over-60' ) ) as $key => $item ) {
		$mature_cards .= bixie_editorial_group( bixie_editorial_image( 'home-mature-' . $key, 'Fictional mature adult ' . strtolower( $item[0] ) . ' with a complete bixie haircut portrait and high opaque collar.', '', '', '/collections/' . $item[1] . '/' ) . bixie_editorial_heading( '<a href="' . esc_url( home_url( '/collections/' . $item[1] . '/' ) ) . '">' . $item[0] . '</a>', 3 ), 'bixie-collection-card' );
	}
	$mature .= bixie_editorial_group( $mature_cards, 'bixie-mature-grid' );
	$sections .= bixie_editorial_group( $mature, 'bixie-section', '12 · Age collections', 'section' );

	$colour = bixie_editorial_intro( '11 / COLOUR & CONTRAST', 'The same outline, a different light.', 'Colour changes how the layers read. Explore natural silver, warm copper and deep dark tones without treating colour as a requirement.' );
	$colour_cards = '';
	foreach ( array( 'silver' => array( 'Silver & grey', '/collections/natural-grey/' ), 'copper' => array( 'Copper & warm tones', '/looks/?colour=copper' ), 'black' => array( 'Dark & defined', '/looks/?colour=dark' ) ) as $key => $item ) {
		$colour_cards .= bixie_editorial_group( bixie_editorial_image( 'home-colour-' . $key, 'Fictional adult with a ' . $key . ' bixie, full hairstyle visible and fully covered high-neck clothing.', '', '', $item[1] ) . bixie_editorial_heading( '<a href="' . esc_url( home_url( $item[1] ) ) . '">' . $item[0] . '</a>', 3 ), 'bixie-collection-card' );
	}
	$colour .= bixie_editorial_group( $colour_cards, 'bixie-story-grid' );
	$sections .= bixie_editorial_group( $colour, 'bixie-section is-paper', '13 · Colour collections', 'section' );

	$film = bixie_editorial_intro( '12 / IN MOTION', 'See how the outline moves.', 'A quiet photographic motion study. It has no audio and is not live-action salon footage. Use the controls to pause or play.' );
	$video_id = bixie_editorial_media_id( 'home-motion-film' );
	$video_file = get_theme_file_path( 'assets/video/bixie-motion.mp4' );
	$poster_id = bixie_editorial_media_id( 'home-motion-poster' );
	$poster_exists = $poster_id || is_file( get_theme_file_path( 'assets/images/home-motion-poster.webp' ) );
	if ( ( $video_id || is_file( $video_file ) ) && $poster_exists ) {
		$video_url = $video_id ? wp_get_attachment_url( $video_id ) : get_theme_file_uri( 'assets/video/bixie-motion.mp4' );
		$poster = bixie_editorial_media_url( 'home-motion-poster' );
		$film .= bixie_editorial_block( 'video', array( 'id' => $video_id, 'autoplay' => true, 'controls' => true, 'loop' => true, 'muted' => true, 'playsInline' => true, 'poster' => $poster, 'preload' => 'metadata', 'className' => 'bixie-film' ), '<figure class="wp-block-video bixie-film"><video autoplay controls loop muted poster="' . esc_url( $poster ) . '" src="' . esc_url( $video_url ) . '" playsinline></video></figure>' );
		$film .= bixie_editorial_group( bixie_editorial_button( 'Play film', '/#bixie-film', 'bixie-video-motion-toggle' ) . bixie_editorial_paragraph( 'Silent photographic motion study.', 'bixie-caption' ), 'bixie-motion-controls' );
	} else {
		$film .= bixie_editorial_image( 'home-motion-poster', 'Fictional adult in a high-neck top with a fully visible bixie haircut, composed for the photographic motion study.', '', 'bixie-film' );
	}
	$sections .= bixie_editorial_group( $film, 'bixie-section bixie-film-section is-ink', '14 · Photographic motion study', 'section', 'bixie-film' );

	$sections .= bixie_editorial_photo_section( '13 / FINE & THIN HAIR', 'Lighter hair. Deliberate shape.', 'Look at the retained perimeter and crown. Fine strands and lower density are different considerations, so bring both into the salon conversation.', array_merge( $shelves['fine-hair'], $shelves['thin-hair'] ), '/collections/fine-hair/', '15 · Fine and thin hair photo shelf' );
	$sections .= bixie_editorial_photo_section( '14 / EVERYDAY SHAPES', 'A shape for your real routine.', 'Explore lighter, softer outlines and discuss the styling time you actually want to spend.', $shelves['easy-styling'], '/collections/easy-styling/', '16 · Easy styling photo shelf', 'is-paper' );
	$sections .= bixie_editorial_photo_section( '15 / THE NINETIES INFLUENCE', 'Fuller sides. A softer outline.', 'A fuller bob-pixie balance, subtle layering and a generous fringe. Browse the references in every direction.', $shelves['90s-inspired'], '/collections/90s-inspired/', '17 · Nineties inspired photo shelf', 'is-moss' );

	$features = bixie_editorial_intro( '16 / THREE DIFFERENT FINISHES', 'Piecey. Feathered. Closely tapered.', 'Choose a finish that feels like you; each cover opens a real photo collection.' );
	$feature_cards = '';
	foreach ( array( 'consultation' => array( 'Choppy bixie', '/collections/choppy/' ), 'styling' => array( 'Feathered bixie', '/collections/feathered/' ), 'growth' => array( 'Bixie with an undercut', '/collections/undercut/' ) ) as $key => $item ) {
		$feature_cards .= bixie_editorial_group( bixie_editorial_image( 'home-journal-' . $key, 'Original complete haircut portrait of a fictional adult in loose opaque high-neck clothing.', '', '', $item[1] ) . bixie_editorial_heading( '<a href="' . esc_url( home_url( $item[1] ) ) . '">' . $item[0] . '</a>', 3 ), 'bixie-collection-card' );
	}
	$features .= bixie_editorial_group( $feature_cards, 'bixie-story-grid' );
	$sections .= bixie_editorial_group( $features, 'bixie-section', '18 · Finish photo collections', 'section' );

	$sections .= bixie_editorial_photo_section( '17 / THE SHAGGY EDGE', 'Texture with room to move.', 'Look at the softer perimeter, separated layers and how much length remains around the face.', $shelves['shaggy'], '/collections/shaggy/', '19 · Shaggy bixie photo shelf', 'is-paper' );

	$faq = bixie_editorial_intro( '18 / COMMON QUESTIONS', 'Before you go short.', 'Straight answers to the questions that come up while choosing a bixie.' );
	foreach ( array( 'Is a bixie the same as a pixie bob?' => 'The names overlap. Bixie usually describes a bob-and-pixie hybrid; pixie bob can describe a similar shape. Compare the actual outline and ask your stylist what the label means to them.', 'Does a bixie work with fine hair?' => 'It can, but the placement of layers and the retained perimeter matter. Use the fine-hair collection as a reference and discuss your density with your stylist.', 'Can a bixie work with curls?' => 'Yes. Curl pattern, shrinkage and the balance of crown and sides affect the result. Look at curly references and discuss dry shape as well as wet cutting length.', 'Do I need bangs?' => 'No. A fringe is one option. Explore no-bangs and side-swept collections if you prefer a more open forehead.', 'How often does it need a trim?' => 'There is no fixed interval for every cut. A close nape or short fringe may need attention sooner. Agree on a practical refresh plan with your stylist.', 'Are these photographs real salon clients?' => 'No. They are original generated photographs of fictional adults. Use them as visual ideas, not evidence that an identical result is guaranteed.' ) as $question => $answer ) {
		$faq .= bixie_editorial_block( 'details', array(), '<details class="wp-block-details"><summary>' . esc_html( $question ) . '</summary>' . bixie_editorial_paragraph( $answer ) . '</details>' );
	}
	$sections .= bixie_editorial_group( $faq, 'bixie-section bixie-faq', '20 · Frequently asked questions', 'section' );

	$index = bixie_editorial_intro( '19 / THE COMPLETE INDEX', 'Every collection, within reach.', 'Move directly to a photo collection or a practical guide.' );
	$index_links = '';
	foreach ( array( 'Classic' => '/collections/classic/', 'Short' => '/collections/short/', 'Long' => '/collections/long/', 'Layered' => '/collections/layered/', 'Shaggy' => '/collections/shaggy/', 'Feathered' => '/collections/feathered/', 'Choppy' => '/collections/choppy/', 'Fine hair' => '/collections/fine-hair/', 'Thin hair' => '/collections/thin-hair/', 'Thick hair' => '/collections/thick-hair/', 'Straight hair' => '/collections/straight/', 'Wavy hair' => '/collections/wavy/', 'Curly hair' => '/collections/curly/', 'Bangs' => '/collections/bangs/', 'Over 40' => '/collections/over-40/', 'Over 50' => '/collections/over-50/', 'Over 60' => '/collections/over-60/', 'Natural grey' => '/collections/natural-grey/', '90s inspired' => '/collections/90s-inspired/', 'Round face' => '/collections/round-face/', 'Undercut' => '/collections/undercut/', 'Easy styling' => '/collections/easy-styling/', 'No bangs' => '/looks/?fringe=none', 'Curtain bangs' => '/looks/?fringe=curtain', 'Side-swept bangs' => '/looks/?fringe=side-swept', 'Wispy bangs' => '/looks/?fringe=wispy', 'Copper hair' => '/looks/?colour=copper', 'Dark hair' => '/looks/?colour=dark' ) as $label => $path ) {
		$index_links .= bixie_editorial_paragraph( '<a href="' . esc_url( home_url( $path ) ) . '">' . esc_html( $label ) . '</a>' );
	}
	$index .= bixie_editorial_group( $index_links, 'bixie-guide-index' );
	$sections .= bixie_editorial_group( $index, 'bixie-section is-ink', '21 · Complete collection index', 'section' );

	$close = bixie_editorial_paragraph( 'YOUR NEXT CUT STARTS WITH A CLEARER PICTURE.', 'bixie-eyebrow' );
	$close .= bixie_editorial_heading( 'Find a shape.<br><em>Make it yours.</em>' );
	$close .= bixie_editorial_button( 'Explore every collection', '/collections/' );
	$sections .= bixie_editorial_group( $close, 'bixie-section bixie-closing is-moss', '22 · Closing invitation', 'section' );

	return bixie_editorial_group( $sections, 'bixie-home', 'Bixie Haircut home' );
}
