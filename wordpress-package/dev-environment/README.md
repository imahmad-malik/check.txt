# Local cloud QA runtime helpers

These four reviewed source helpers contain no saved credentials or database.
They document the disposable development runtime used for package tests. They
are separate from the installable WordPress theme and plugin.

The current retained cloud runtime is `/workspace/wp-test`. Run its tested helper:

```sh
python /workspace/wp-test/start-test-services.py
python /workspace/wp-test/start-test-services.py --status
```

It starts missing services, retains the database, and checks both the local
socket MariaDB and a real WordPress HTTP response. `--restart` stops only exact
owned processes, waits for graceful exit, and starts them again. It never
initializes or resets the database and never force-kills another service.

Run a PHP WordPress API test through the dedicated wrapper:

```sh
/workspace/wp-test/php /workspace/check.txt/wordpress-package/tests/wp-import-test.php /workspace/wp-test/wordpress/wp-load.php state
```

For a fresh machine, copy `install-runtime.py` into a separate writable runtime
directory and execute it there. It verifies Debian InRelease signatures with
the installed official Debian archive keyring, verifies package-index SHA-256,
then verifies every extracted `.deb`. It requires `curl`, `sqv`, `dpkg`, Python
and the official Debian archive keyring. It does not change system packages.
Current tested versions were PHP 8.4.26 and MariaDB 11.8.6 on amd64.

The installer obtains runtime binaries only. A fresh machine still needs a
dedicated PHP ini/extensions, socket-only database initialization, an official
WordPress checkout, generated local configuration and a normal WordPress
installation before the service helper can work. Never copy QA credentials,
authentication state or a database into a public release. Do not overwrite an
existing owner WordPress installation. The retained-runtime startup path above
was tested; a completely fresh installation from just these four files has
not been independently reproduced.

Use the existing cloud checkout. Do not create a Git worktree unless requested.
Internal loopback requests are for QA; no public web preview is provided.
