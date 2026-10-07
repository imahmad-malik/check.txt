<?php
/** Actual WordPress core ZIP installation/activation in an isolated QA site.
 * Usage: php wp-install-package.php /path/to/wp-load.php theme.zip [plugin.zip]
 * Does not import production content or weaken publication requirements.
 */
if (PHP_SAPI !== 'cli' || empty($argv[1]) || empty($argv[2])) { exit(2); }
$_SERVER['HTTP_HOST'] = '127.0.0.1:8766';
$_SERVER['SERVER_NAME'] = '127.0.0.1';
$_SERVER['REQUEST_URI'] = '/';
require $argv[1];
if (wp_get_environment_type() !== 'local' || (int) get_option('blog_public') !== 0) {
    fwrite(STDERR, "This mutating ZIP check requires an isolated local noindex QA site.\n"); exit(2);
}
require_once ABSPATH . 'wp-admin/includes/admin.php';
require_once ABSPATH . 'wp-admin/includes/class-wp-upgrader.php';
$user = get_user_by('login', 'bixie_qa_admin');
if (!$user) { fwrite(STDERR, "QA administrator is missing.\n"); exit(2); }
wp_set_current_user($user->ID);
$results = [];
ob_start();
$skin = new Automatic_Upgrader_Skin();
$upgrader = new Theme_Upgrader($skin);
$result = $upgrader->install($argv[2], ['overwrite_package' => true]);
ob_end_clean();
if (is_wp_error($result) || !$result) {
    fwrite(STDERR, is_wp_error($result) ? $result->get_error_message() : wp_json_encode($skin->get_errors())); exit(1);
}
switch_theme('bixie-editorial');
$results['themeInstalledViaCoreZip'] = true;
$results['activeTheme'] = get_stylesheet();
if (!empty($argv[3])) {
    ob_start();
    $skin = new Automatic_Upgrader_Skin();
    $upgrader = new Plugin_Upgrader($skin);
    $result = $upgrader->install($argv[3], ['overwrite_package' => true]);
    ob_end_clean();
    if (is_wp_error($result) || !$result) {
        fwrite(STDERR, is_wp_error($result) ? $result->get_error_message() : wp_json_encode($skin->get_errors())); exit(1);
    }
    $result = activate_plugin('bixie-library/bixie-library.php');
    if (is_wp_error($result)) { fwrite(STDERR, $result->get_error_message()); exit(1); }
    $results['pluginInstalledViaCoreZip'] = true;
    $results['pluginActive'] = is_plugin_active('bixie-library/bixie-library.php');
}
echo wp_json_encode($results, JSON_PRETTY_PRINT) . "\n";
