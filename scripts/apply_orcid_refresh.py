"""Validate and publish a reviewed ORCID extraction without new provider requests.

Routine: run the audit workflow, upload its two review files to data/orcid-refresh-review/,
then run the apply workflow manually. No file fingerprints are hard-coded: the script
records the fingerprints of what it applied and uses them to detect repeats and drift.
"""
import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote

REVIEW = ['data/orcid-refresh-review/publications.proposed.json',
          'data/orcid-refresh-review/publication-sync-status.json']
DEST = ['data/publications.json', 'data/publication-sync-status.json']
REPORT = 'data/orcid-refresh-apply-status.json'
PROFILES = 'data/faculty.json'
KEEP_HISTORY = 20


def blob(raw):
    return hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()


def doi(value):
    d = re.sub(r'^(?:https?://(?:dx\.)?doi\.org/|doi\s*:\s*)', '', unquote(str(value or '')).strip(), flags=re.I).lower()
    return d if re.fullmatch(r'10\.\d{4,9}/\S+', d) else ''


def refs(papers):
    result = defaultdict(set)
    for p in papers:
        for v in p.get('provenance', []):
            if v.get('source_name') == 'ORCID':
                result[v.get('faculty_id')].add((v.get('orcid'), v.get('put_code')))
    return result


def digest(root, names):
    return {k: blob((root / k).read_bytes()) for k in names}


def apply(root):
    root = Path(root)
    report_path = root / REPORT
    review_now = digest(root, REVIEW)
    previous = json.loads(report_path.read_text()) if report_path.exists() else None
    if previous:
        if digest(root, DEST) != previous['output_blobs']:
            raise ValueError('Live publication files changed since the last applied extraction; review required')
        if previous.get('review_blobs') == review_now:
            return previous
    read = lambda name: json.loads((root / name).read_text())
    proposal = read(REVIEW[0])
    status = read(REVIEW[1])
    faculty = read(PROFILES)['faculty']
    old = read(DEST[0])['publications']
    people = {f['id']: f for f in faculty}
    outcomes = status['faculty']
    papers = proposal['publications']
    stamp = status['last_attempt']
    date = datetime.fromisoformat(stamp)
    if date.tzinfo is None or date > datetime.now(timezone.utc) or proposal.get('last_attempt') != stamp:
        raise ValueError('Extraction dates do not agree')
    if previous and stamp <= previous['retrieved_at']:
        raise ValueError('Extraction is not newer than the last applied extraction')
    if len(people) != len(faculty) or set(people) != set(outcomes) or status['faculty_count'] != len(people) or status['publication_count'] != len(papers):
        raise ValueError('Roster or publication totals do not agree')
    counts = Counter(s['status'] for s in outcomes.values())
    if set(counts) - {'success', 'no_public_publications', 'failed'} or status['successful_faculty'] != counts['success'] + counts['no_public_publications'] or bool(status['all_successful']) != (counts['failed'] == 0):
        raise ValueError('Invalid extraction summary')
    for fid, s in outcomes.items():
        if s.get('last_attempt') != stamp or s.get('orcid', '') != people[fid].get('orcid', ''):
            raise ValueError('Profile identifier or attempt date changed: ' + fid)
        if s['status'] != 'failed' and (s.get('last_success') != stamp or s.get('review_required')):
            raise ValueError('Successful source requires additional review: ' + fid)
    if any(not isinstance(p.get('id'), str) or not p['id'] for p in papers) or len({p['id'] for p in papers}) != len(papers):
        raise ValueError('Missing or duplicate publication IDs')
    old_refs = refs(old)
    allowed_legacy = {(v.get('source_name'), v.get('source_url')) for p in old for v in p.get('provenance', []) if v.get('source_name') != 'ORCID'}
    seen_dois = set()
    for p in papers:
        ids = p.get('faculty_ids', [])
        departments = p.get('departments', [])
        if not isinstance(p.get('title'), str) or not p['title'].strip() or not ids or len(set(ids)) != len(ids) or not set(ids) <= set(people):
            raise ValueError('Invalid title or profile links: ' + p['id'])
        d = doi(p.get('doi'))
        if d:
            if d in seen_dois:
                raise ValueError('Duplicate DOI requires review: ' + d)
            seen_dois.add(d)
        if not p.get('provenance'):
            raise ValueError('Missing publication provenance: ' + p['id'])
        for v in p['provenance']:
            if v.get('source_name') != 'ORCID':
                if (v.get('source_name'), v.get('source_url')) not in allowed_legacy:
                    raise ValueError('Unexpected new non-ORCID source')
                continue
            fid = v.get('faculty_id')
            if fid not in people or fid not in ids or type(v.get('put_code')) is not int:
                raise ValueError('Invalid ORCID-to-profile association')
            if outcomes[fid]['status'] == 'failed':
                if (v.get('orcid'), v.get('put_code')) not in old_refs[fid]:
                    raise ValueError('New unvalidated records for failed profile: ' + fid)
            elif v.get('orcid') != people[fid].get('orcid') or v.get('retrieved_at') != stamp or people[fid]['department_id'] not in departments:
                raise ValueError('Successful source provenance mismatch: ' + fid)
    new_refs = refs(papers)
    per_profile = []
    for fid, s in outcomes.items():
        if s['status'] == 'failed':
            if not old_refs[fid] <= new_refs[fid]:
                raise ValueError('Previous records lost for failed profile: ' + fid)
        elif len(new_refs[fid]) != s.get('eligible_records'):
            raise ValueError('Eligible ORCID records do not agree with paper provenance: ' + fid)
        per_profile.append({'id': fid, 'database_name': people[fid]['name'], 'department_id': people[fid]['department_id'], 'status': s['status'], 'eligible_records': s.get('eligible_records'), 'display_records': sum(fid in p['faculty_ids'] for p in papers), 'message': s.get('message', '')})
    if not papers:
        raise ValueError('Empty extraction cannot replace live publication data')
    outputs = {DEST[0]: proposal, DEST[1]: status}
    serialized = {k: (json.dumps(v, ensure_ascii=False, indent=2) + '\n').encode() for k, v in outputs.items()}
    history = list((previous or {}).get('history', []))
    if previous:
        history.append({k: previous.get(k) for k in ['applied_at', 'retrieved_at', 'new_publication_count', 'faculty_checked', 'profiles_with_eligible_works', 'profiles_with_no_public_works', 'profiles_failed', 'unique_dois']})
    report = {'review_blobs': review_now, 'applied_at': datetime.now(timezone.utc).isoformat(timespec='seconds'), 'retrieved_at': stamp,
              'old_publication_count': len(old), 'new_publication_count': len(papers),
              'new_record_ids': len({p['id'] for p in papers} - {p['id'] for p in old}),
              'faculty_checked': len(people), 'profiles_with_eligible_works': counts['success'],
              'profiles_with_no_public_works': counts['no_public_publications'], 'profiles_failed': counts['failed'],
              'unique_dois': len(seen_dois), 'warnings': status.get('warnings', []), 'profile_results': per_profile,
              'output_blobs': {k: blob(v) for k, v in serialized.items()}, 'history': history[-KEEP_HISTORY:],
              'notes': ['Fresh ORCID records and their matching status are published together.',
                        'All names, portraits, identifiers, profile roles and Scholar metrics are unchanged.',
                        'Shared DOI records link to multiple profiles without duplicating the publication.',
                        'Failed profiles retain previous ORCID records. No failure becomes a zero-publication claim.',
                        'No new provider calls, citation refreshes, student-only extractions or showcase ranking changes are performed. New DOI citation counts require a subsequent audit.']}
    for path, raw in serialized.items():
        (root / path).write_bytes(raw)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return report


if __name__ == '__main__':
    r = apply(Path(__file__).resolve().parents[1])
    print(json.dumps({k: r[k] for k in ['old_publication_count', 'new_publication_count', 'faculty_checked', 'profiles_with_eligible_works', 'profiles_with_no_public_works', 'profiles_failed', 'warnings']}, indent=2))
