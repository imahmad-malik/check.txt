<?php
/** Bixie Library never deletes editorial content, attachments or saved site settings. */
if (!defined('WP_UNINSTALL_PLUGIN')) { exit; }
delete_transient('bixie_catalog_facets');
delete_option('bixie_import_lock');
delete_option('bixie_media_bundle_lock');
// Retain the resumable import state and settings, too: reinstalling remains safe.
