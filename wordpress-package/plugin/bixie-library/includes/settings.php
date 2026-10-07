<?php
if (!defined('ABSPATH')) { exit; }

function bixie_render_owner_settings(): void { ?>
    <hr><h2><?php esc_html_e('Editorial motion and owner details', 'bixie-library'); ?></h2>
    <form method="post" action="<?php echo esc_url(admin_url('admin-post.php')); ?>"><input type="hidden" name="action" value="bixie_owner_settings"><?php wp_nonce_field('bixie_owner_settings'); ?>
      <p><label><input type="checkbox" name="motion_enabled" value="1" <?php checked(get_option('bixie_motion_enabled', true)); ?>> <?php esc_html_e('Enable photograph motion (visitors can pause; reduced-motion preferences are respected).', 'bixie-library'); ?></label></p>
      <p><label><?php esc_html_e('Photo motion speed, pixels per second', 'bixie-library'); ?> <input type="number" min="5" max="36" name="motion_speed" value="<?php echo absint(get_option('bixie_motion_speed', 15)); ?>"></label></p>
      <p><label><input type="checkbox" name="video_autoplay" value="1" <?php checked(get_option('bixie_video_autoplay', true)); ?>> <?php esc_html_e('Allow muted editorial-film autoplay when visible and motion is enabled.', 'bixie-library'); ?></label></p>
      <?php foreach (['motion_play_label' => ['Play photograph button label', 'Play photo motion'], 'motion_next_label' => ['Next photographs button label', 'Show next photographs'], 'film_pause_label' => ['Pause film button label', 'Pause film']] as $key => $field): ?><p><label><?php echo esc_html($field[0]); ?><br><input class="regular-text" name="<?php echo esc_attr($key); ?>" type="text" maxlength="80" value="<?php echo esc_attr(get_option('bixie_' . $key, $field[1])); ?>"></label></p><?php endforeach; ?>
      <p><label><?php esc_html_e('Genuine owner contact email', 'bixie-library'); ?><br><input class="regular-text" type="email" name="contact_email" value="<?php echo esc_attr(get_option('bixie_contact_email', '')); ?>"></label></p><p class="description"><?php esc_html_e('Optional until supplied by the owner. No address is invented and no message is sent. Add the Contact details block to an editable page to show the configured address.', 'bixie-library'); ?></p>
      <?php submit_button(__('Save owner settings', 'bixie-library')); ?>
    </form>
<?php }

add_action('admin_post_bixie_owner_settings', static function(): void {
    if (!current_user_can('manage_options')) { wp_die(esc_html__('Administrator permission required.', 'bixie-library'), '', ['response' => 403]); }
    check_admin_referer('bixie_owner_settings');
    update_option('bixie_motion_enabled', !empty($_POST['motion_enabled']), false);
    update_option('bixie_motion_speed', max(5, min(36, absint($_POST['motion_speed'] ?? 15))), false);
    update_option('bixie_video_autoplay', !empty($_POST['video_autoplay']), false);
    foreach (['motion_play_label' => 'Play photo motion', 'motion_next_label' => 'Show next photographs', 'film_pause_label' => 'Pause film'] as $key => $default) { $text = sanitize_text_field(wp_unslash($_POST[$key] ?? '')); update_option('bixie_' . $key, $text ? substr($text, 0, 80) : $default, false); }
    $email = sanitize_email(wp_unslash($_POST['contact_email'] ?? ''));
    if (!empty($_POST['contact_email']) && !is_email($email)) { wp_die(esc_html__('Supply a valid owner email or leave it empty.', 'bixie-library'), '', ['response' => 400]); }
    update_option('bixie_contact_email', $email, false);
    wp_safe_redirect(admin_url('tools.php?page=bixie-setup')); exit;
});

add_action('init', static function(): void {
    register_block_type('bixie/contact-details', ['api_version' => 3, 'render_callback' => static function(): string { $email = sanitize_email(get_option('bixie_contact_email', '')); return $email ? '<p class="bixie-contact-details"><a href="' . esc_url('mailto:' . $email) . '">' . esc_html($email) . '</a></p>' : '<p class="bixie-contact-details">' . esc_html__('Owner contact details have not yet been supplied.', 'bixie-library') . '</p>'; }]);
});
