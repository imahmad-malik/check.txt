#!/usr/bin/env python3
"""Prepare a separate local noindex final-asset QA site; retain the earlier site."""
from pathlib import Path
import getpass
import json
import os
import re
import shutil
import subprocess
import time
import urllib.request

EXISTING = Path('/workspace/wp-test')
FINAL = Path('/workspace/wp-final-test')
PACKAGE = Path(__file__).resolve().parents[1]
PORT = 8767
DATABASE = 'bixie_final_qa_20261007'


def main():
    runtime = EXISTING / 'runtime'
    core = EXISTING / 'wordpress'
    if not (core / 'wp-includes/version.php').is_file() or not (EXISTING / 'db/mysql.sock').exists():
        raise RuntimeError('The previously verified isolated runtime and database socket are required.')
    FINAL.mkdir(exist_ok=True)
    for folder in ['logs', 'tmp', 'wordpress']:
        (FINAL / folder).mkdir(exist_ok=True)
    for source in core.iterdir():
        if source.name.startswith('.') or source.name in {'wp-content', 'wp-config.php'}:
            continue
        target = FINAL / 'wordpress' / source.name
        if source.is_dir():
            shutil.copytree(source, target, dirs_exist_ok=True)
        elif source.is_file():
            shutil.copy2(source, target)
    config = FINAL / 'wordpress/wp-config.php'
    if not config.exists():
        text = (core / 'wp-config.php').read_text()
        text, count = re.subn(r"(define\(\s*['\"]DB_NAME['\"]\s*,\s*)['\"][^'\"]+['\"]", lambda m: m[1] + "'" + DATABASE + "'", text)
        if count != 1:
            raise RuntimeError('Could not scope the copied private QA configuration to its new database.')
        text = text.replace(str(EXISTING / 'logs'), str(FINAL / 'logs'))
        config.write_text(text)
        config.chmod(0o600)
    credentials = FINAL / 'qa-credentials.json'
    if not credentials.exists():
        shutil.copy2(EXISTING / credentials.name, credentials)
        credentials.chmod(0o600)
    # Credential values/configuration are never printed or included in packages.
    env = dict(os.environ, LD_LIBRARY_PATH=str(runtime / 'usr/lib/x86_64-linux-gnu'))
    configured_user = re.search(r"define\(\s*['\"]DB_USER['\"]\s*,\s*(['\"])(.*?)\1\s*\)", config.read_text())
    if not configured_user:
        raise RuntimeError('The existing private QA database account could not be identified.')
    account = configured_user[2].replace('\\', '\\\\').replace("'", "''")
    sql = 'CREATE DATABASE IF NOT EXISTS `' + DATABASE + '` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci; GRANT ALL PRIVILEGES ON `' + DATABASE + "`.* TO '" + account + "'@'localhost';"
    subprocess.run([str(runtime / 'usr/bin/mariadb'), '--no-defaults', '--socket=' + str(EXISTING / 'db/mysql.sock'), '-u' + getpass.getuser()], input=sql, text=True, check=True, capture_output=True, env=env)
    (FINAL / 'php.ini').write_text((EXISTING / 'php.ini').read_text().replace(str(EXISTING / 'logs'), str(FINAL / 'logs')).replace(str(EXISTING / 'tmp'), str(FINAL / 'tmp')))
    (FINAL / 'php').write_text((EXISTING / 'php').read_text().replace(str(EXISTING / 'php.ini'), str(FINAL / 'php.ini')))
    (FINAL / 'php').chmod(0o755)
    install = (EXISTING / 'install-site.php').read_text().replace('8766', str(PORT)).replace('Bixie Haircut isolated QA', 'Bixie Haircut final asset QA')
    (FINAL / 'install-site.php').write_text(install)
    result = subprocess.run([str(FINAL / 'php'), str(FINAL / 'install-site.php')], text=True, check=True, capture_output=True)
    site = json.loads(result.stdout)
    if not site['installed'] or int(site['public']) != 0:
        raise RuntimeError('Fresh final QA installation did not remain isolated/noindex.')
    for kind, slug in [('theme', 'bixie-editorial'), ('plugin', 'bixie-library')]:
        destination = FINAL / 'wordpress/wp-content' / ('themes' if kind == 'theme' else 'plugins') / slug
        shutil.copytree(PACKAGE / kind / slug, destination, dirs_exist_ok=True)
    activation = FINAL / 'activate-site.php'
    activation.write_text("<?php require __DIR__.'/wordpress/wp-load.php'; require_once ABSPATH.'wp-admin/includes/plugin.php'; switch_theme('bixie-editorial'); $r=activate_plugin('bixie-library/bixie-library.php'); if(is_wp_error($r)){exit(1);} echo json_encode(['theme'=>get_stylesheet(),'plugin'=>is_plugin_active('bixie-library/bixie-library.php'),'visibility'=>get_option('blog_public')]);")
    active = json.loads(subprocess.check_output([str(FINAL / 'php'), str(activation)], text=True))
    shutil.copy2(EXISTING / 'router.php', FINAL / 'router.php')
    expected = [str(runtime / 'usr/bin/php8.4'), '-S', '127.0.0.1:' + str(PORT), '-t', str(FINAL / 'wordpress'), str(FINAL / 'router.php')]
    owned = []
    for proc in Path('/proc').iterdir():
        if not proc.name.isdigit():
            continue
        try:
            args = [x.decode() for x in (proc / 'cmdline').read_bytes().split(b'\0') if x]
            if all(value in args for value in expected):
                owned.append(int(proc.name))
        except (OSError, UnicodeError):
            continue
    if len(owned) > 1:
        raise RuntimeError('Multiple exact owned final QA HTTP processes; none stopped.')
    if owned:
        pid = owned[0]
    else:
        with (FINAL / 'logs/http-service.log').open('ab') as log:
            process = subprocess.Popen([str(FINAL / 'php'), *expected[1:]], stdout=log, stderr=log, start_new_session=True)
        pid = process.pid
    (FINAL / 'http.pid').write_text(str(pid) + '\n')
    ready = False
    for _ in range(30):
        try:
            with urllib.request.urlopen('http://127.0.0.1:' + str(PORT) + '/', timeout=2) as response:
                body = response.read()
                ready = response.status == 200 and b'Bixie' in body and b'noindex' in body
            if ready:
                break
        except Exception:
            pass
        time.sleep(.2)
    report = {'separateFinalSitePrepared': ready, 'oldSiteDatabaseAndUploadsPreserved': True, 'wordpress': site['wordpress'], 'theme': active['theme'], 'plugin': active['plugin'], 'visibility': active['visibility'], 'httpOwnedPid': pid, 'credentialsRemainPrivate': True, 'assetImport': 'Not executed by this environment preparation helper.'}
    (PACKAGE / 'tests/wp-final-environment-report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    if not ready:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
