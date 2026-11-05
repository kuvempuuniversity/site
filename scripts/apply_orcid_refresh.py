"""Validate and publish the user-uploaded ORCID extraction without new requests."""
import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote

EXPECTED = {
'data/orcid-refresh-review/publications.proposed.json':'13e00689d6c4f962c5f278b2f32f0a577b0efa4a',
'data/orcid-refresh-review/publication-sync-status.json':'55e83633c93baff8d46af0af7696b03f9ce60f4d',
'data/publications.json':'c848630a5d48586a43870e4cf2cda6f40895213f',
'data/publication-sync-status.json':'badbb56bd3fb207346649ddd1d31d67b02c09e9c',
'data/faculty.json':'823b936397cb5ae87e6a39a830506931f972036d'}
DEST = ['data/publications.json','data/publication-sync-status.json']
REPORT = 'data/orcid-refresh-apply-status.json'

def blob(raw):
    return hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()

def doi(value):
    d = re.sub(r'^(?:https?://(?:dx\.)?doi\.org/|doi\s*:\s*)','',unquote(str(value or '')).strip(),flags=re.I).lower()
    return d if re.fullmatch(r'10\.\d{4,9}/\S+',d) else ''

def refs(papers):
    result = defaultdict(set)
    for p in papers:
        for v in p.get('provenance',[]):
            if v.get('source_name')=='ORCID':
                result[v.get('faculty_id')].add((v.get('orcid'),v.get('put_code')))
    return result

def apply(root, enforce=True):
    root = Path(root)
    manifest = hashlib.sha256(json.dumps(EXPECTED,sort_keys=True).encode()).hexdigest()
    report_path = root/REPORT
    if report_path.exists():
        previous = json.loads(report_path.read_text())
        checks = {k:v for k,v in EXPECTED.items() if k not in DEST}
        checks.update(previous['output_blobs'])
        if previous.get('manifest_sha256')!=manifest or any(blob((root/k).read_bytes())!=v for k,v in checks.items()):
            raise ValueError('Previously applied extraction or profile inputs changed; review required')
        return previous
    if enforce and any(blob((root/k).read_bytes())!=v for k,v in EXPECTED.items()):
        raise ValueError('A reviewed input changed; nothing published')
    read = lambda name: json.loads((root/name).read_text())
    proposal = read('data/orcid-refresh-review/publications.proposed.json')
    status = read('data/orcid-refresh-review/publication-sync-status.json')
    faculty = read('data/faculty.json')['faculty']
    old = read('data/publications.json')['publications']
    people = {f['id']:f for f in faculty}
    outcomes = status['faculty']
    papers = proposal['publications']
    stamp = status['last_attempt']
    date = datetime.fromisoformat(stamp)
    if date.tzinfo is None or date>datetime.now(timezone.utc) or proposal.get('last_attempt')!=stamp:
        raise ValueError('Extraction dates do not agree')
    if len(people)!=len(faculty) or set(people)!=set(outcomes) or status['faculty_count']!=len(people) or status['publication_count']!=len(papers):
        raise ValueError('Roster or publication totals do not agree')
    counts = Counter(s['status'] for s in outcomes.values())
    if set(counts)-{'success','no_public_publications','failed'} or status['successful_faculty']!=counts['success']+counts['no_public_publications'] or bool(status['all_successful'])!=(counts['failed']==0):
        raise ValueError('Invalid extraction summary')
    for fid,s in outcomes.items():
        if s.get('last_attempt')!=stamp or s.get('orcid','')!=people[fid].get('orcid',''):
            raise ValueError('Profile identifier or attempt date changed: '+fid)
        if s['status']!='failed' and (s.get('last_success')!=stamp or s.get('review_required')):
            raise ValueError('Successful source requires additional review: '+fid)
    if any(not isinstance(p.get('id'),str) or not p['id'] for p in papers) or len({p['id'] for p in papers})!=len(papers):
        raise ValueError('Missing or duplicate publication IDs')
    old_refs = refs(old)
    allowed_legacy = {(v.get('source_name'),v.get('source_url')) for p in old for v in p.get('provenance',[]) if v.get('source_name')!='ORCID'}
    seen_dois = set()
    for p in papers:
        ids = p.get('faculty_ids',[])
        departments = p.get('departments',[])
        if not isinstance(p.get('title'),str) or not p['title'].strip() or not ids or len(set(ids))!=len(ids) or not set(ids)<=set(people):
            raise ValueError('Invalid title or profile links: '+p['id'])
        d = doi(p.get('doi'))
        if d:
            if d in seen_dois:
                raise ValueError('Duplicate DOI requires review: '+d)
            seen_dois.add(d)
        if not p.get('provenance'):
            raise ValueError('Missing publication provenance: '+p['id'])
        for v in p['provenance']:
            if v.get('source_name')!='ORCID':
                if (v.get('source_name'),v.get('source_url')) not in allowed_legacy:
                    raise ValueError('Unexpected new non-ORCID source')
                continue
            fid = v.get('faculty_id')
            if fid not in people or fid not in ids or type(v.get('put_code')) is not int:
                raise ValueError('Invalid ORCID-to-profile association')
            if outcomes[fid]['status']=='failed':
                if (v.get('orcid'),v.get('put_code')) not in old_refs[fid]:
                    raise ValueError('New unvalidated records for failed profile: '+fid)
            elif v.get('orcid')!=people[fid].get('orcid') or v.get('retrieved_at')!=stamp or people[fid]['department_id'] not in departments:
                raise ValueError('Successful source provenance mismatch: '+fid)
    new_refs = refs(papers)
    per_profile = []
    for fid,s in outcomes.items():
        if s['status']=='failed':
            if not old_refs[fid]<=new_refs[fid]:
                raise ValueError('Previous records lost for failed profile: '+fid)
        elif len(new_refs[fid])!=s.get('eligible_records'):
            raise ValueError('Eligible ORCID records do not agree with paper provenance: '+fid)
        per_profile.append({'id':fid,'database_name':people[fid]['name'],'department_id':people[fid]['department_id'],'status':s['status'],'eligible_records':s.get('eligible_records'),'display_records':sum(fid in p['faculty_ids'] for p in papers),'message':s.get('message','')})
    if not papers:
        raise ValueError('Empty extraction cannot replace live publication data')
    outputs = {'data/publications.json':proposal,'data/publication-sync-status.json':status}
    serialized = {k:(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode() for k,v in outputs.items()}
    report = {'manifest_sha256':manifest,'applied_at':datetime.now(timezone.utc).isoformat(timespec='seconds'),'retrieved_at':stamp,'old_publication_count':len(old),'new_publication_count':len(papers),'new_record_ids':len({p['id'] for p in papers}-{p['id'] for p in old}),'faculty_checked':len(people),'profiles_with_eligible_works':counts['success'],'profiles_with_no_public_works':counts['no_public_publications'],'profiles_failed':counts['failed'],'unique_dois':len(seen_dois),'warnings':status.get('warnings',[]),'profile_results':per_profile,'output_blobs':{k:blob(v) for k,v in serialized.items()},'notes':['Fresh ORCID records and their matching status are published together.','All names, portraits, identifiers, profile roles and Scholar metrics are unchanged.','Shared DOI records link to multiple profiles without duplicating the publication.','Failed profiles retain previous ORCID records. No failure becomes a zero-publication claim.','No new provider calls, citation refreshes, student-only extractions or showcase ranking changes are performed. New DOI citation counts require a subsequent audit.']}
    for path,raw in serialized.items():
        (root/path).write_bytes(raw)
    report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return report

if __name__=='__main__':
    r = apply(Path(__file__).resolve().parents[1])
    print(json.dumps({k:r[k] for k in ['old_publication_count','new_publication_count','faculty_checked','profiles_with_eligible_works','profiles_with_no_public_works','profiles_failed','warnings']},indent=2))
