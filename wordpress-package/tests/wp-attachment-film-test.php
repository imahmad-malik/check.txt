<?php
/** Actual local WordPress regression. Synthetic canvases/movie only, never release media. */
if (PHP_SAPI !== 'cli' || empty($argv[1])) { exit(2); }
$_SERVER['HTTP_HOST'] = '127.0.0.1:8766'; $_SERVER['SERVER_NAME'] = '127.0.0.1'; $_SERVER['REQUEST_URI'] = '/'; require $argv[1];
if (wp_get_environment_type() !== 'local' || (int) get_option('blog_public') !== 0 || !function_exists('bixie_project_attachment_target')) { fwrite(STDERR, "Latest plugin and isolated local noindex QA database required.\n"); exit(2); }
$fixtures = get_option('bixie_qa_fixture_state', []); $look = absint($fixtures['looks'][0] ?? 0); $sources = bixie_array_meta($look, 'bixie_images');
if (!$look || count($sources) !== 3 || !bixie_check_look($look)['complete']) { exit(2); }
$admin = get_user_by('login', 'bixie_qa_admin'); if (!$admin) { exit(2); } wp_set_current_user($admin->ID);
$tests = []; $failure = null; $attachments = []; $folder = wp_upload_dir()['basedir'] . '/isolated-attachment-film-' . wp_generate_uuid4(); wp_mkdir_p($folder);
$old_required_video = get_option('bixie_required_home_video', null); $old_attachment_setting = get_option('wp_attachment_pages_enabled', null);
function qf_assert(string $name, bool $passed, array $detail = []): void { global $tests; $tests[] = ['name' => $name, 'passed' => $passed, 'detail' => $detail]; if (!$passed) { throw new RuntimeException($name); } }
function qf_attachment(string $path, string $mime, string $title): int { global $attachments; $id = wp_insert_attachment(['post_title' => 'ISOLATED SYNTHETIC TEST ' . $title, 'post_mime_type' => $mime, 'post_status' => 'inherit', 'meta_input' => ['_bixie_qa_fixture' => 1]], $path); $attachments[] = $id; return $id; }
function qf_video_block(int $id, ?string $src = null): string { return '<!-- wp:video ' . wp_json_encode(['id' => $id]) . ' --><figure class="wp-block-video"><video controls src="' . esc_url($src ?? wp_get_attachment_url($id)) . '"></video></figure><!-- /wp:video -->'; }
function qf_film_errors(string $content): array { return array_values(array_filter(bixie_check_home(0, $content)['reasons'], static fn($reason) => stripos($reason, 'film') !== false)); }
try {
    $native = $folder . '/synthetic-native.png'; copy(bixie_original_source_path($sources[0]['id']), $native);
    $display = $folder . '/synthetic-display.webp'; $pixels = imagecreatefrompng($native); imagewebp($pixels, $display, 70); imagedestroy($pixels);
    $photo = qf_attachment($display, 'image/webp', 'optimized/native source'); update_post_meta($photo, '_bixie_asset_key', 'isolated-attachment-film-source');
    update_post_meta($photo, '_bixie_original_source_file', $native); update_post_meta($photo, '_bixie_original_source_url', str_replace(wp_upload_dir()['basedir'], wp_upload_dir()['baseurl'], $native)); update_post_meta($photo, '_bixie_delivery_file', get_attached_file($photo));
    qf_assert('Unattached project image targets the retained native source, not optimized display', bixie_project_attachment_target($photo) === bixie_original_source_url($photo) && bixie_project_attachment_target($photo) !== wp_get_attachment_url($photo));
    wp_update_post(['ID' => $photo, 'post_parent' => $look]); qf_assert('Project view targets complete published owning look', bixie_project_attachment_target($photo) === get_permalink($look));
    wp_update_post(['ID' => $photo, 'post_parent' => 0]); delete_post_meta($photo, '_bixie_asset_key'); update_post_meta($photo, '_bixie_import_key', 'isolated-old-import-marker');
    qf_assert('Import marker alone does not redirect or noindex ordinary owner attachment', !bixie_is_project_attachment($photo) && bixie_project_attachment_target($photo) === '');
    delete_post_meta($photo, '_bixie_import_key'); qf_assert('Ordinary owner media remains outside project redirect scope', bixie_project_attachment_target($photo) === '' && !bixie_is_project_attachment($photo));
    $movie_path = $folder . '/synthetic-three-view.mp4'; $command = '/usr/bin/ffmpeg -loglevel error -y';
    foreach ($sources as $source) { $command .= ' -loop 1 -t 0.5 -i ' . escapeshellarg(bixie_original_source_path($source['id'])); }
    $filter = ''; foreach ([0, 1, 2] as $i) { $filter .= '[' . $i . ':v]scale=320:240:force_original_aspect_ratio=decrease,pad=320:240:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=12[v' . $i . '];'; }
    $filter .= '[v0][v1][v2]concat=n=3:v=1:a=0[out]'; $command .= ' -filter_complex ' . escapeshellarg($filter) . ' -map ' . escapeshellarg('[out]') . ' -c:v libx264 -pix_fmt yuv420p -movflags +faststart ' . escapeshellarg($movie_path) . ' 2>&1'; exec($command, $output, $code);
    if ($code !== 0) { throw new RuntimeException('Synthetic three-angle movie generation failed.'); }
    $movie = qf_attachment($movie_path, 'video/mp4', 'three-view movie'); $fields = apply_filters('attachment_fields_to_edit', [], get_post($movie));
    qf_assert('Media Library MP4 exposes review and all three angle controls', isset($fields['bixie_review_approved'], $fields['bixie_multiview_declared'], $fields['bixie_film_front'], $fields['bixie_film_side'], $fields['bixie_film_back']));
    $save = ['bixie_asset_key' => 'isolated-reviewed-film', 'bixie_review_approved' => 1, 'bixie_multiview_declared' => 1]; foreach ($sources as $source) { $save['bixie_film_' . $source['angle']] = $source['id']; }
    apply_filters('attachment_fields_to_save', ['ID' => $movie], $save); qf_assert('Actual Media Library save qualifies explicit corresponding synthetic three-angle movie', bixie_check_film($movie));
    $fields = apply_filters('attachment_fields_to_edit', [], get_post($movie)); qf_assert('Selected angle photographs have accessible GUI source-review links', str_contains($fields['bixie_film_front']['html'], 'post=' . $sources[0]['id']) && str_contains($fields['bixie_film_back']['html'], 'action=edit'));
    $photo_fields = apply_filters('attachment_fields_to_edit', [], get_post($photo)); qf_assert('Source attachment GUI exposes independent review and native provenance controls', isset($photo_fields['bixie_review_approved'], $photo_fields['bixie_native_verified']));
    $wrong = $save; $wrong['bixie_film_front'] = $photo; apply_filters('attachment_fields_to_save', ['ID' => $movie], $wrong);
    qf_assert('Film review never automatically approves selected source photographs', !get_post_meta($photo, '_bixie_review_approved', true) && !get_post_meta($photo, '_bixie_native_verified', true) && !bixie_check_film($movie));
    apply_filters('attachment_fields_to_save', ['ID' => $movie], $save); update_option('bixie_required_home_video', 'isolated-missing-seeded-film');
    qf_assert('Owner-selected reviewed native video replaces seeded role without code editing', qf_film_errors(qf_video_block($movie)) === []);
    $unreviewed_path = $folder . '/unreviewed.mp4'; copy($movie_path, $unreviewed_path); $unreviewed = qf_attachment($unreviewed_path, 'video/mp4', 'unreviewed replacement');
    qf_assert('Native block replacement with unreviewed movie fails homepage film gate', count(qf_film_errors(qf_video_block($unreviewed))) > 0);
    qf_assert('Stale approved block ID cannot approve a different selected src', count(qf_film_errors(qf_video_block($movie, wp_get_attachment_url($unreviewed)))) > 0);
    $no_id = '<!-- wp:video --><figure class="wp-block-video"><video src="' . esc_url(wp_get_attachment_url($movie)) . '"></video></figure><!-- /wp:video -->'; qf_assert('Older native video block without ID resolves selected local attachment', qf_film_errors($no_id) === []);
    qf_assert('Missing or external movie fails required native film gate', count(qf_film_errors('<!-- wp:paragraph --><p>No film.</p><!-- /wp:paragraph -->')) > 0 && count(qf_film_errors(qf_video_block($movie, 'https://example.invalid/unreviewed.mp4'))) > 0);
    $old_file = get_post_meta($movie, '_wp_attached_file', true); update_post_meta($movie, '_wp_attached_file', get_post_meta($unreviewed, '_wp_attached_file', true));
    qf_assert('Same-ID movie path replacement clears film review and multiview declaration', !get_post_meta($movie, '_bixie_review_approved', true) && !get_post_meta($movie, '_bixie_multiview_declared', true) && !bixie_check_film($movie));
    update_post_meta($movie, '_wp_attached_file', $old_file); apply_filters('attachment_fields_to_save', ['ID' => $movie], $save); file_put_contents($movie_path, "\0\0\0\10free", FILE_APPEND); clearstatcache();
    qf_assert('Changed movie bytes cannot reuse old reviewed fingerprint even before metadata event', !bixie_check_film($movie));
    update_post_meta($movie, '_wp_attachment_metadata', ['qa_changed_movie_bytes' => 1]); qf_assert('Same-ID metadata event after byte replacement clears both movie review flags', !get_post_meta($movie, '_bixie_review_approved', true) && !get_post_meta($movie, '_bixie_multiview_declared', true));
    qf_assert('Attachment-page setting and owner privacy remain unchanged', get_option('wp_attachment_pages_enabled', null) === $old_attachment_setting && (int) get_option('blog_public') === 0);
} catch (Throwable $error) { $failure = $error->getMessage(); }
finally {
    if ($old_required_video === null) { delete_option('bixie_required_home_video'); } else { update_option('bixie_required_home_video', $old_required_video); }
    foreach (array_reverse($attachments) as $id) { wp_delete_attachment($id, true); }
    if (is_dir($folder)) { bixie_bundle_remove_stage($folder); }
}
$retained = count(array_filter($fixtures['looks'] ?? [], static fn($id) => get_post_status($id) === 'publish' && bixie_check_look($id)['complete']));
$report = ['environment' => ['wordpress' => get_bloginfo('version'), 'php' => PHP_VERSION], 'method' => 'Actual isolated WordPress attachment GUI filters/save, native video block resolution, film validation and review invalidation. Explicitly synthetic source canvases and generated three-scene TEST movie only; no production approvals.', 'passed' => $failure === null && $retained === count($fixtures['looks'] ?? []), 'checks' => $tests, 'failure' => $failure, 'retainedOriginalFixtures' => $retained, 'approvedProductionImages' => 0];
$json = wp_json_encode($report, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES) . "\n"; if (!empty($argv[2])) { file_put_contents($argv[2], $json); } echo $json; exit($report['passed'] ? 0 : 1);
