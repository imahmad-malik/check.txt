#!/usr/bin/env python3
"""Extract a verified Debian PHP/MariaDB test runtime without system changes."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import hashlib, json, lzma, re, subprocess

ROOT = Path(__file__).resolve().parent
CACHE = ROOT / 'packages'
RUNTIME = ROOT / 'runtime'
CACHE.mkdir(exist_ok=True)
RUNTIME.mkdir(exist_ok=True)

def run(args, **kw):
    result = subprocess.run(args, capture_output=True, text=True, **kw)
    if result.returncode:
        raise RuntimeError(result.stderr[-1800:] or result.stdout[-1800:])
    return result.stdout.strip()

def fetch(url, destination):
    run(['curl','--fail','--silent','--show-error','--location','--max-time','90',url,'-o',str(destination)])

def index(repository, suite, label):
    signed = CACHE / (label + '-InRelease')
    release = CACHE / (label + '-Release')
    fetch(repository + '/dists/' + suite + '/InRelease', signed)
    release.unlink(missing_ok=True)
    run(['sqv','--keyring','/usr/share/keyrings/debian-archive-keyring.pgp','--output',str(release),'--cleartext',str(signed)])
    digest, size = re.search(r'^ ([a-f0-9]{64})\s+(\d+)\s+main/binary-amd64/Packages.xz$',release.read_text(),re.M).groups()
    compressed = CACHE / (label + '-Packages.xz')
    fetch(repository + '/dists/' + suite + '/main/binary-amd64/Packages.xz', compressed)
    assert compressed.stat().st_size == int(size)
    assert hashlib.sha256(compressed.read_bytes()).hexdigest() == digest
    result = {}
    for block in lzma.decompress(compressed.read_bytes()).decode().split('\n\n'):
        fields = {}
        key = None
        for line in block.splitlines():
            if line.startswith(' ') and key:
                fields[key] += ' ' + line.strip()
            elif ': ' in line:
                key, value = line.split(': ',1)
                fields[key] = value
        if 'Package' in fields:
            fields['Repository'] = repository
            result[fields['Package']] = fields
    return result

def version_ok(version, operation, required):
    return subprocess.run(['dpkg','--compare-versions',version,operation,required],capture_output=True).returncode == 0

def main():
    sources = [('https://deb.debian.org/debian','trixie','main'),
               ('https://security.debian.org/debian-security','trixie-security','security'),
               ('https://deb.debian.org/debian','trixie-updates','updates')]
    records = {}
    with ThreadPoolExecutor(max_workers=3) as pool:
        for candidates in pool.map(lambda args:index(*args),sources):
            for name, fields in candidates.items():
                if name not in records or version_ok(fields['Version'],'gt',records[name]['Version']):
                    records[name] = fields
    installed = {}
    for line in run(['dpkg-query','-W','-f=${Package}\t${Version}\t${Provides}\n']).splitlines():
        fields = line.split('\t')
        if len(fields) >= 2:
            installed[fields[0]] = fields[1]
            for provided in fields[2].split(',') if len(fields) >= 3 else []:
                match = re.match(r'\s*([\w+.-]+)(?:\s*\(=\s*([^\)]+)\))?',provided)
                if match:
                    alias, value = match.groups()
                    installed[alias] = value or fields[1]
    required = ['php8.4-cli','php8.4-common','php8.4-mysql','php8.4-gd','php8.4-xml',
                'php8.4-mbstring','php8.4-curl','php8.4-intl','php8.4-zip','php8.4-opcache',
                'php8.4-readline','mariadb-server','mariadb-server-core','mariadb-client-core']
    chosen = {}
    queue = list(required)
    while queue:
        name = queue.pop()
        if name in chosen:
            continue
        record = records[name]
        chosen[name] = record
        for group in (record.get('Pre-Depends','') + ',' + record.get('Depends','')).split(','):
            alternatives = []
            for alternative in group.split('|'):
                match = re.match(r'\s*([\w+.-]+)(?::\w+)?(?:\s*\((>=|<=|=|>>|<<)\s*([^\)]+)\))?',alternative)
                if match:
                    dep, op, minimum = match.groups()
                    alternatives.append((dep,op,minimum))
            satisfied = False
            for dep, op, minimum in alternatives:
                current = installed.get(dep) or installed.get(dep+':amd64')
                if current and (not op or version_ok(current,op,minimum)):
                    satisfied = True
                    break
                if dep in chosen:
                    satisfied = True
                    break
            if not satisfied and alternatives:
                possible = [dep for dep,op,minimum in alternatives if dep in records and (not op or version_ok(records[dep]['Version'],op,minimum))]
                if not possible:
                    for alias, op, minimum in alternatives:
                        for provider, fields in records.items():
                            for provided in fields.get('Provides','').split(','):
                                if re.match(r'\s*' + re.escape(alias) + r'(?:\s|$)',provided):
                                    possible.append(provider)
                                    break
                            if possible:
                                break
                        if possible:
                            break
                if not possible:
                    raise RuntimeError('Unresolved dependency: ' + group)
                queue.append(possible[0])
    def download(item):
        name, record = item
        file = CACHE / Path(record['Filename']).name
        if not file.exists() or hashlib.sha256(file.read_bytes()).hexdigest() != record['SHA256']:
            fetch(record['Repository'] + '/' + record['Filename'], file)
        assert hashlib.sha256(file.read_bytes()).hexdigest() == record['SHA256']
        assert file.stat().st_size == int(record['Size'])
        return name, file
    with ThreadPoolExecutor(max_workers=4) as pool:
        downloads = list(pool.map(download,chosen.items()))
    for name, file in downloads:
        run(['dpkg-deb','--extract',str(file),str(RUNTIME)])
    report = {name:{'version':record['Version'],'sha256':record['SHA256']} for name,record in chosen.items()}
    (ROOT/'runtime-packages.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'verified_packages':len(chosen),'php':chosen['php8.4-cli']['Version'],'mariadb':chosen['mariadb-server-core']['Version'],'runtime':str(RUNTIME)}))

if __name__ == '__main__':
    main()
