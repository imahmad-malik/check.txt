<?php
$path=parse_url($_SERVER['REQUEST_URI'],PHP_URL_PATH);
$target=__DIR__.'/wordpress'.$path;
if ($path && (is_file($target) || (is_dir($target) && is_file(rtrim($target,'/').'/index.php')))) return false;
require __DIR__.'/wordpress/index.php';
