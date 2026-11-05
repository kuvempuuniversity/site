"""Publish only validated metrics from the uploaded 3 November audit proposals."""
import copy
import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit, parse_qs

EXPECTED = {
'data/faculty.json':'ec074a1550c86f8c74a62ca2afd337a0d45201ea',
'data/citation-metrics.json':'5818f4d71fe01b69096268307c4f1588988279dc',
'data/publications.json':'c848630a5d48586a43870e4cf2cda6f40895213f',
'data/faculty.proposed.json':'fff9411c35cf2fd927e5fef510472a0629b7e1d0',
'data/scholar-sync-status.json':'c51ee06218b75956a31e9a74b8017685c6cf4b30',
'data/citation-metrics.proposed.json':'b3aa7aa3e21dfeaf386cd57a88239f1532ff4de0',
'data/citation-audit-status.json':'bf6ad1f7ee05afd1ac0b95861aa847d08849cf9d'}
DESTINATIONS = ['data/faculty.json','data/citation-metrics.json']
REPORT = 'data/research-refresh-apply-status.json'

def blob(raw):
    return hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()

def author(url):
    u = urlsplit(url or '')
    values = parse_qs(u.query).get('user',[])
    if u.scheme!='https' or u.netloc!='scholar.google.com' or u.path!='/citations' or u.fragment or len(values)!=1 or not re.fullmatch('[A-Za-z0-9_-]{1,64}',values[0]):
        raise ValueError('Invalid Scholar URL in successful result')
    return values[0]

def timestamp(value):
    date = datetime.fromisoformat(value)
    if date.tzinfo is None or date > datetime.now(timezone.utc):
        raise ValueError('Invalid retrieval date')
    return value

def doi(value):
    return re.sub(r'^(?:https?://(?:dx\.)?doi\.org/|doi\s*:\s*)','',str(value or '').strip(),flags=re.I).lower()

def apply(root, enforce=True):
    root = Path(root)
    manifest = hashlib.sha256(json.dumps(EXPECTED,sort_keys=True).encode()).hexdigest()
    report_path = root/REPORT
    if report_path.exists():
        previous = json.loads(report_path.read_text())
        if previous.get('manifest_sha256')!=manifest:
            raise ValueError('Different refresh batch; review required')
        checks = {k:v for k,v in EXPECTED.items() if k not in DESTINATIONS}
        checks.update(previous['output_blobs'])
        if any(blob((root/k).read_bytes())!=v for k,v in checks.items()):
            raise ValueError('Inputs or published data changed after this refresh')
        return previous
    if enforce and any(blob((root/k).read_bytes())!=v for k,v in EXPECTED.items()):
        raise ValueError('A reviewed input changed; no files updated')
    read = lambda name: json.loads((root/'data'/name).read_text())
    current = read('faculty.json')
    original = copy.deepcopy(current)
    proposed = read('faculty.proposed.json')
    sr = read('scholar-sync-status.json')
    cache = read('citation-metrics.json')
    cp = read('citation-metrics.proposed.json')
    cr = read('citation-audit-status.json')
    publications = read('publications.json')['publications']
    rows = {r['id']:r for r in current['faculty']}
    incoming = {r['id']:r for r in proposed['faculty']}
    if len(rows)!=len(current['faculty']) or len(incoming)!=len(proposed['faculty']) or set(rows)!=set(incoming) or set(rows)!=set(sr['faculty']) or sr['selected']!=len(rows):
        raise ValueError('Profile roster mismatch or duplicate IDs')
    statuses = Counter(v['status'] for v in sr['faculty'].values())
    if statuses.get('success',0)!=sr['success'] or statuses.get('failed',0)!=sr['failed'] or sr['success']+sr['failed']!=sr['selected']:
        raise ValueError('Scholar audit totals do not agree')
    mapped = []
    skipped = []
    for identity, row in rows.items():
        status = sr['faculty'][identity]
        if status['status']!='success':
            skipped.append({'id':identity,'reason':status.get('message'),'previous_metrics_retained':'scholar_metrics' in row})
            continue
        m = copy.deepcopy(incoming[identity].get('scholar_metrics',{}))
        aid = author(row.get('scholar_url'))
        if not (m.get('source')=='Google Scholar' and m.get('provider')=='SerpApi' and m.get('scope')=='all-time' and m.get('status')=='success' and author(m.get('scholar_url'))==aid and m.get('author_id')==aid and status.get('author_id')==aid and m.get('author_name') and m.get('retrieved_at')==status.get('retrieved_at')==sr['last_attempt']):
            raise ValueError('Scholar identity/source/date mismatch: '+identity)
        timestamp(m['retrieved_at'])
        if not all(type(m.get(k)) is int and 0<=m[k]<=9007199254740991 for k in ['total_citations','h_index','i10_index']) or m['h_index']**2>m['total_citations'] or 10*m['i10_index']>m['total_citations']:
            raise ValueError('Invalid Scholar metric values: '+identity)
        m['scholar_url'] = row['scholar_url']
        row['scholar_metrics'] = m
        mapped.append({'id':identity,'database_name':row['name'],'department_id':row['department_id'],'author_id':aid,'returned_author_name':m['author_name'],'retrieved_at':m['retrieved_at']})
    strip = lambda doc: [{k:v for k,v in r.items() if k!='scholar_metrics'} for r in doc['faculty']]
    if strip(original)!=strip(current) or {k:v for k,v in original.items() if k!='faculty'}!={k:v for k,v in current.items() if k!='faculty'}:
        raise ValueError('Unexpected non-metric profile change')
    ds = {doi(p.get('doi')) for p in publications if re.fullmatch(r'10\.\d{4,9}/\S+',doi(p.get('doi')))}
    entries = cp['entries']
    counts = Counter(e['status'] for e in entries.values())
    if cp.get('source')!='OpenAlex' or cp.get('last_attempt')!=cr['last_attempt'] or set(entries)!=ds or len(ds)!=cr['unique_dois'] or len(publications)!=cr['publications'] or counts.get('success',0)!=cr['matched'] or counts.get('failed',0)!=cr['failed'] or counts.get('not_found',0)!=cr['not_found']:
        raise ValueError('Citation report and publication inputs do not agree')
    updated = []
    exceptions = []
    cache.setdefault('entries',{})
    for key, entry in entries.items():
        if doi(key)!=key or entry.get('doi')!=key or entry.get('source')!='OpenAlex':
            raise ValueError('Invalid citation identity/source: '+key)
        if entry['status']!='success':
            exceptions.append({'doi':key,'status':entry['status'],'message':entry.get('message'),'previous_entry_retained':key in cache['entries']})
            continue
        if type(entry.get('count')) is not int or entry['count']<0 or not re.fullmatch(r'https://openalex\.org/W\d+',entry.get('source_url','')) or entry.get('retrieved_at')!=cr['last_attempt']:
            raise ValueError('Invalid successful citation record: '+key)
        timestamp(entry['retrieved_at'])
        cache['entries'][key] = copy.deepcopy(entry)
        updated.append(key)
    cache.update(source='OpenAlex',last_attempt=cr['last_attempt'])
    outputs = {'data/faculty.json':current,'data/citation-metrics.json':cache}
    serialized = {k:(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode() for k,v in outputs.items()}
    report = {'manifest_sha256':manifest,'applied_at':datetime.now(timezone.utc).isoformat(timespec='seconds'),'scholar_selected':sr['selected'],'scholar_updated':len(mapped),'scholar_not_updated':len(skipped),'scholar_mappings':mapped,'scholar_exceptions':skipped,'citation_updated':len(updated),'citation_exceptions':exceptions,'publications_unchanged':len(publications),'papers_without_doi':cr['without_doi'],'output_blobs':{k:blob(v) for k,v in serialized.items()},'notes':['Only successful validated metrics are mapped. Failed attempts do not replace existing values or become zero.','Names, photos, identifiers, roles, department assignments and publications are preserved. Returned Scholar author names are retained only inside metric provenance for review.','Google Scholar profile totals and OpenAlex paper counts remain separate sources.','Student datasets, the Environmental Science Scholar paper snapshot, and static showcase rankings are not modified.','No new provider requests are performed.']}
    for name, raw in serialized.items():
        (root/name).write_bytes(raw)
    report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return report

if __name__=='__main__':
    r = apply(Path(__file__).resolve().parents[1])
    print(json.dumps({k:r[k] for k in ['scholar_selected','scholar_updated','scholar_not_updated','citation_updated','citation_exceptions','publications_unchanged']},indent=2))
