#!/usr/bin/env python3
"""Install the reviewed ORCID display snapshot. Defaults to check-only."""
import argparse, hashlib, json, os, shutil, tempfile
from pathlib import Path

def blob(raw):
    return hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--site',type=Path,required=True)
p.add_argument('--apply',action='store_true')
a=p.parse_args()
root=a.site.expanduser().resolve()
if not (root/'.git').exists() or not (root/'index.html').is_file():
    raise SystemExit('STOP: destination must be the existing site Git repository.')
bundle=Path(__file__).resolve().parent
manifest=json.loads((bundle/'manifest.json').read_text())
changes=[]
for relative,item in manifest['files'].items():
    src=bundle/'payload'/relative; dst=root/relative
    raw=src.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=item['sha256']:
        raise SystemExit('STOP: package integrity check failed: '+relative)
    existing=dst.read_bytes() if dst.exists() else None
    if existing==raw:
        print('Already current: '+relative);continue
    current=blob(existing) if existing is not None else None
    if current!=item['expected_git_blob']:
        raise SystemExit('STOP: local file differs from reviewed baseline: '+relative+'; no files changed.')
    changes.append((relative,src,dst,existing))
    print('Ready: '+relative)
if not a.apply:
    print('CHECK ONLY: '+str(len(changes))+' files ready. Nothing changed.');raise SystemExit(0)
if not changes:
    print('Nothing to change.');raise SystemExit(0)
backup=Path(tempfile.mkdtemp(prefix='ku-orcid-display-backup-'))
for relative,src,dst,existing in changes:
    if existing is not None:
        b=backup/relative;b.parent.mkdir(parents=True,exist_ok=True);b.write_bytes(existing)
written=[]
try:
    for relative,src,dst,existing in changes:
        dst.parent.mkdir(parents=True,exist_ok=True)
        fd,name=tempfile.mkstemp(dir=dst.parent,prefix='.'+dst.name)
        try:
            with os.fdopen(fd,'wb') as out:out.write(src.read_bytes())
            os.replace(name,dst)
        finally:
            if os.path.exists(name):os.unlink(name)
        written.append((dst,existing))
except Exception:
    for dst,existing in reversed(written):
        if existing is None:dst.unlink(missing_ok=True)
        else:dst.write_bytes(existing)
    raise
print('Installed '+str(len(changes))+' files. Backup: '+str(backup))
print('No commit, push, schedule activation or deployment was performed.')
