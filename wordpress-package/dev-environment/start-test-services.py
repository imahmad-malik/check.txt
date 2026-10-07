#!/usr/bin/env python3
"""Idempotently start/restart only this isolated QA site's owned services.

Keeps the database and WordPress configuration/content. Never initializes or
resets the database, kills another service, or replaces repository files.
"""
from pathlib import Path
import argparse, getpass, json, os, signal, subprocess, time, urllib.request

ROOT=Path(__file__).resolve().parent
RUNTIME=ROOT/'runtime'
PORT=8766
PIDFILES={'db':ROOT/'db/mysql.pid','http':ROOT/'http.pid'}
EXPECTED={
 'db':[str(RUNTIME/'usr/sbin/mariadbd'),f'--datadir={ROOT}/db',f'--socket={ROOT}/db/mysql.sock','--skip-networking'],
 'http':[str(RUNTIME/'usr/bin/php8.4'),'-S',f'127.0.0.1:{PORT}','-t',str(ROOT/'wordpress'),str(ROOT/'router.php')],
}

def owned(kind,pid):
    try:
        argv=Path(f'/proc/{pid}/cmdline').read_bytes().split(b'\0')
        argv=[value.decode() for value in argv if value]
        return all(value in argv for value in EXPECTED[kind])
    except (OSError,UnicodeError):
        return False

def get_pid(kind):
    try:
        pid=int(PIDFILES[kind].read_text().strip())
        if owned(kind,pid):return pid
    except (OSError,ValueError):pass
    # Adopt only an exact command belonging to our directory, never by port/name.
    matches=[int(p.name) for p in Path('/proc').iterdir() if p.name.isdigit() and owned(kind,int(p.name))]
    if len(matches)>1:raise RuntimeError(f'Multiple owned {kind} processes; will not choose or kill one.')
    if matches:
        PIDFILES[kind].write_text(str(matches[0])+'\n')
        return matches[0]
    return None

def readiness():
    db=False;http=False
    env=os.environ.copy();env['LD_LIBRARY_PATH']=str(RUNTIME/'usr/lib/x86_64-linux-gnu')
    try:
        r=subprocess.run([str(RUNTIME/'usr/bin/mariadb-admin'),'--no-defaults',f'--socket={ROOT}/db/mysql.sock',f'-u{getpass.getuser()}','ping'],capture_output=True,env=env,timeout=3)
        db=r.returncode==0
    except (OSError,subprocess.TimeoutExpired):pass
    try:
        with urllib.request.urlopen(f'http://127.0.0.1:{PORT}/',timeout=3) as r:
            http=r.status==200 and bool(r.read(100))
    except Exception:pass
    return {'db':db,'http':http}

def stop(kind):
    pid=get_pid(kind)
    if pid is None:return
    if not owned(kind,pid):raise RuntimeError(f'{kind} PID does not belong to this QA site; refusing to stop it.')
    os.kill(pid,signal.SIGTERM)
    deadline=time.monotonic()+10
    while time.monotonic()<deadline:
        if not owned(kind,pid):
            PIDFILES[kind].unlink(missing_ok=True)
            return
        time.sleep(.1)
    raise RuntimeError(f'Owned {kind} did not stop gracefully; no forced kill performed.')

def start(kind):
    if get_pid(kind):return
    env=os.environ.copy();env['LD_LIBRARY_PATH']=str(RUNTIME/'usr/lib/x86_64-linux-gnu')
    if kind=='db':
        if not (ROOT/'db/mysql').is_dir():raise RuntimeError('QA database is not initialized. Run initial setup; service starter will not initialize/reset it.')
        cmd=[str(RUNTIME/'usr/sbin/mariadbd'),'--no-defaults',f'--basedir={RUNTIME}/usr',f'--datadir={ROOT}/db',f'--socket={ROOT}/db/mysql.sock',f'--pid-file={ROOT}/db/mysql.pid','--skip-networking',f'--plugin-dir={RUNTIME}/usr/lib/mysql/plugin',f'--lc-messages-dir={RUNTIME}/usr/share/mariadb','--innodb-buffer-pool-size=128M','--max-connections=30',f'--log-error={ROOT}/logs/mariadb.log']
    else:
        cmd=[str(ROOT/'php'),'-S',f'127.0.0.1:{PORT}','-t',str(ROOT/'wordpress'),str(ROOT/'router.php')]
    with (ROOT/'logs'/f'{kind}-service.log').open('ab') as log:
        p=subprocess.Popen(cmd,stdout=log,stderr=log,env=env,start_new_session=True)
    PIDFILES[kind].write_text(str(p.pid)+'\n')

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--restart',action='store_true')
    parser.add_argument('--status',action='store_true')
    args=parser.parse_args()
    if not args.status:
        if args.restart:
            stop('http');stop('db')
        start('db')
        # Wait for socket readiness before starting PHP/WordPress requests.
        deadline=time.monotonic()+15
        while not readiness()['db']:
            if time.monotonic()>deadline:raise RuntimeError('Owned QA MariaDB did not become ready; inspect logs/mariadb.log.')
            time.sleep(.2)
        start('http')
        deadline=time.monotonic()+15
        while not readiness()['http']:
            if time.monotonic()>deadline:raise RuntimeError('Owned QA PHP/WordPress did not become ready; inspect logs/http-service.log.')
            time.sleep(.2)
    state=readiness();state['ownedPids']={kind:get_pid(kind) for kind in PIDFILES}
    state['retainsDatabase']=True
    print(json.dumps(state))
    if not all(state[kind] for kind in ['db','http']):raise SystemExit(1)

if __name__=='__main__':main()
