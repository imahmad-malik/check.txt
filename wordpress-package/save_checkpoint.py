#!/usr/bin/env python3
"""Save this authorized project to its Git branch without changing checkout/main/index."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent


def git(*arguments, env=None, input=None):
    return subprocess.check_output(['git', *arguments], cwd=REPO, env=env, input=input, text=True).strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--message', required=True)
    parser.add_argument('--include-relative-path', action='append', default=[])
    parser.add_argument('--branch', default='bixie-wordpress-project')
    args = parser.parse_args()
    if not re.fullmatch(r'bixie-[a-z0-9-]+', args.branch):
        raise ValueError('Only a dedicated bixie branch is supported; main is preserved.')
    paths = ['wordpress-package']
    for relative in args.include_relative_path:
        path = Path(relative)
        if path.is_absolute() or '..' in path.parts or path.parts[0] not in {'wordpress-pilot-release', 'wordpress-media-release', 'wordpress-release'}:
            raise ValueError('Only explicit project delivery files can be added.')
        resolved = (REPO / path).resolve(strict=True)
        if REPO not in resolved.parents or not resolved.is_file() or resolved.stat().st_size >= 95 * 1024 * 1024:
            raise ValueError('Delivery path must be a regular project file below 95 MiB.')
        paths.append(relative)
    existing = git('ls-remote', '--heads', 'origin', args.branch)
    if existing:
        parent = existing.split()[0]
        try:
            git('cat-file', '-e', parent + '^{commit}')
        except subprocess.CalledProcessError:
            git('fetch', 'origin', args.branch)
    else:
        parent = git('rev-parse', 'HEAD')
    head = git('rev-parse', 'HEAD')
    real_index = REPO / '.git/index'
    original_index = real_index.read_bytes() if real_index.is_file() else None
    with tempfile.TemporaryDirectory(prefix='bixie-checkpoint-', dir='/tmp') as temporary:
        env = dict(os.environ, GIT_INDEX_FILE=str(Path(temporary) / 'index'))
        git('read-tree', parent, env=env)
        git('add', '--', *paths, ':(exclude)**/__pycache__/**', ':(exclude)**/*.pyc', ':(exclude)**/*.tmp', env=env)
        tracked = git('ls-files', env=env).splitlines()
        for relative in tracked:
            if relative.startswith(('wordpress-package/', 'wordpress-pilot-release/', 'wordpress-media-release/', 'wordpress-release/')):
                if any(token in relative.lower() for token in ('wp-config', 'qa-credentials', 'auth-state', '.env', 'private-key')):
                    raise ValueError('Private runtime path cannot enter the project checkpoint.')
        tree = git('write-tree', env=env)
        commit = git('commit-tree', tree, '-p', parent, input=args.message + '\n')
        git('push', 'origin', commit + ':refs/heads/' + args.branch)
        git('update-ref', 'refs/heads/' + args.branch, commit)
    assert git('rev-parse', 'HEAD') == head
    assert (real_index.read_bytes() if real_index.is_file() else None) == original_index
    report = {'branch': args.branch, 'commit': commit, 'checkout_head_preserved': head,
              'normal_index_preserved': True, 'extra_delivery_paths': args.include_relative_path}
    (REPO / 'wordpress-checkpoint-publish.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
