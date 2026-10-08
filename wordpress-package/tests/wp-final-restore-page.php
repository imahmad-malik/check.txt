<?php
/** Exact-ID fallback restoration for an owner edit acceptance check only. */
if (PHP_SAPI !== 'cli' || empty($argv[1]) || empty($argv[2])) { exit(2); }
$_SERVER['HTTP_HOST'] = '127.0.0.1:8767'; $_SERVER['SERVER_NAME'] = '127.0.0.1'; $_SERVER['REQUEST_URI'] = '/';
require $argv[1];
if (wp_get_environment_type() !== 'local' || (int) get_option('blog_public') !== 0 || untrailingslashit(home_url('/')) !== 'http://127.0.0.1:8767') { exit(2); }
$path = realpath($argv[2]);
if (!$path || !str_starts_with($path, '/workspace/wp-final-test/restore-backups/')) { exit(2); }
$data = json_decode(file_get_contents($path), true, 32, JSON_THROW_ON_ERROR);
$id = absint($data['id'] ?? 0); $content = (string) ($data['content']['raw'] ?? '');
if (!$id || get_post_type($id) !== 'page' || get_post_meta($id, '_bixie_import_key', true) !== 'about' || !hash_equals($data['contentSHA256'] ?? '', hash('sha256', $content)) || !in_array($data['status'] ?? '', ['publish', 'draft', 'private', 'pending'], true)) { exit(2); }
$result = wp_update_post(wp_slash(['ID' => $id, 'post_content' => $content, 'post_status' => $data['status']]), true);
if (is_wp_error($result) || hash('sha256', (string) get_post_field('post_content', $id)) !== $data['contentSHA256']) { exit(1); }
echo wp_json_encode(['exactAboutPageIDRestored' => $id, 'contentSHA256MatchesPrivateBackup' => true]) . "\n";
