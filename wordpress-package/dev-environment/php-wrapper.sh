#!/bin/sh
export LD_LIBRARY_PATH='/workspace/wp-test/runtime/usr/lib/x86_64-linux-gnu'${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}
export PHP_INI_SCAN_DIR=''
exec '/workspace/wp-test/runtime/usr/bin/php8.4' -c '/workspace/wp-test/php.ini' "$@"
