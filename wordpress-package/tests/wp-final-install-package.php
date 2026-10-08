<?php
/** Actual core ZIP acceptance, scoped to the separate local noindex final QA site. */
if (PHP_SAPI !== 'cli' || empty($argv[1]) || empty($argv[2])) { exit(2); }
$qa_url = $argv[4] ?? 'http://127.0.0.1:8767';
$url = parse_url($qa_url);
if (!$url || ($url['scheme'] ?? '') !== 'http' || ($url['host'] ?? '') !== '127.0.0.1' || (int) ($url['port'] ?? 0) !== 8767 || !empty($url['user']) || !empty($url['pass'])) { exit(2); }
$_SERVER['HTTP_HOST'] = $url['host'] . ':' . $url['port'];
$_SERVER['SERVER_NAME'] = $url['host'];
$_SERVER['REQUEST_URI'] = '/';
require $argv[1];
if (wp_get_environment_type() !== 'local' || (int) get_option('blog_public') !== 0 || untrailingslashit(home_url('/')) !== $qa_url) {
    fwrite(STDERR, "Requires the separate localhost:8767 local noindex QA site.\n"); exit(2);
}
require_once ABSPATH . 'wp-admin/includes/admin.php';
require_once ABSPATH . 'wp-admin/includes/class-wp-upgrader.php';
$user = get_user_by('login', 'bixie_qa_admin');
if (!$user || !user_can($user, 'install_plugins')) { exit(2); }
wp_set_current_user($user->ID);
$engineering = ($argv[5] ?? '') === 'engineering';
$report = ['scope' => 'Actual delivered core ZIP installation on a separate local noindex WordPress site.', 'release_scope' => $engineering ? 'engineering_installable_media_incomplete' : 'full_media_acceptance_not_implied_by_code_install', 'checks' => [], 'archives' => []];
foreach (['theme' => $argv[2], 'plugin' => $argv[3] ?? ''] as $kind => $archive) {
    if (!$archive) { continue; }
    if (!is_file($archive)) { exit(2); }
    $report['archives'][$kind] = ['filename' => basename($archive), 'bytes' => filesize($archive), 'sha256' => hash_file('sha256', $archive)];
    ob_start();
    $skin = new Automatic_Upgrader_Skin();
    $upgrader = $kind === 'theme' ? new Theme_Upgrader($skin) : new Plugin_Upgrader($skin);
    $result = $upgrader->install($archive, ['overwrite_package' => true]);
    ob_end_clean();
    if (is_wp_error($result) || !$result) { fwrite(STDERR, "Core ZIP installation failed.\n"); exit(1); }
    if ($kind === 'theme') { switch_theme('bixie-editorial'); $ok = get_stylesheet() === 'bixie-editorial'; }
    else { $result = activate_plugin('bixie-library/bixie-library.php'); $ok = !is_wp_error($result) && is_plugin_active('bixie-library/bixie-library.php'); }
    $report['checks'][$kind . 'InstalledAndActivatedViaCoreZIP'] = $ok;
}
$report['passed'] = !in_array(false, $report['checks'], true);
$report['runtime'] = ['wordpress' => get_bloginfo('version'), 'php' => PHP_VERSION];
file_put_contents(__DIR__ . ($engineering ? '/wp-engineering-core-zip-report.json' : '/wp-final-core-zip-report.json'), wp_json_encode($report, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES) . "\n");
echo wp_json_encode($report, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES) . "\n";
exit($report['passed'] ? 0 : 1);
