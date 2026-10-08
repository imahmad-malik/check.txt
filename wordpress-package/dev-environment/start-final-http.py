#!/usr/bin/env python3
"""Restore only the retained noindex QA HTTP process; never copy code or reset data."""
import argparse
import json
from pathlib import Path
import subprocess
import time
import urllib.request


BASE = Path('/workspace/wp-final-test')
RUNTIME = Path('/workspace/wp-test')
EXPECTED = [str(RUNTIME / 'runtime/usr/bin/php8.4'), '-S', '127.0.0.1:8767',
            '-t', str(BASE / 'wordpress'), str(BASE / 'router.php')]


def healthy():
    try:
        with urllib.request.urlopen('http://127.0.0.1:8767/', timeout=5) as response:
            body = response.read()
            return response.status == 200 and b'Bixie' in body and b'noindex' in body
    except Exception:
        return False


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--status', action='store_true')
    args = parser.parse_args()
    owned = []
    for process in Path('/proc').iterdir():
        if not process.name.isdigit():
            continue
        try:
            command = [value.decode() for value in (process / 'cmdline').read_bytes().split(b'\0') if value]
            if all(value in command for value in EXPECTED):
                owned.append(int(process.name))
        except (OSError, UnicodeError):
            continue
    if len(owned) > 1:
        raise RuntimeError('Multiple exact owned QA HTTP processes; none changed.')
    started = False
    if not owned and not args.status:
        required = [BASE / 'php', BASE / 'php.ini', BASE / 'router.php',
                    BASE / 'wordpress/wp-config.php', RUNTIME / 'db/mysql.sock']
        if not all(path.exists() for path in required):
            raise RuntimeError('Retained QA runtime/site and running database socket are required.')
        (BASE / 'logs').mkdir(exist_ok=True)
        with (BASE / 'logs/http-service.log').open('ab') as log:
            process = subprocess.Popen([str(BASE / 'php'), *EXPECTED[1:]],
                                       stdout=log, stderr=log, start_new_session=True)
        owned = [process.pid]
        (BASE / 'http.pid').write_text(str(process.pid) + '\n')
        started = True
    ready = healthy()
    if owned and not args.status:
        # The local single-worker PHP server can be busy with a source import.
        # Observe readiness briefly without stopping or replacing that process.
        for _ in range(4):
            if ready:
                break
            time.sleep(.2)
            ready = healthy()
    result = {'http': ready, 'ownedPid': owned[0] if owned else None,
              'startedMissingOwnedHTTP': started, 'retainsDatabase': True,
              'doesNotCopyThemePluginOrCatalog': True, 'requiresRetainedRuntime': True}
    print(json.dumps(result))
    if not ready or not owned:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
