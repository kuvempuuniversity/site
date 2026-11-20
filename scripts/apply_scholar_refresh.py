"""Publish only validated Google Scholar metrics from reviewed audit proposals.

Reusable: reads the reviewed files in data/citation-refresh-review/, merges only
successful, validated scholar_metrics into data/faculty.json, and leaves every
other profile field untouched.
"""
import argparse
import copy
import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit, parse_qs

REVIEW = 'data/citation-refresh-review/'
PROPOSED = REVIEW + 'faculty.proposed.json'
STATUS = REVIEW + 'scholar-sync-status.json'
FACULTY = 'data/faculty.json'
REPORT = 'data/scholar-refresh-apply-status.json'


def blob(raw):
    return hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()


def author(url):
    u = urlsplit(url or '')
    values = parse_qs(u.query).get('user', [])
    if u.scheme != 'https' or u.netloc != 'scholar.google.com' or u.path != '/citations' or u.fragment or len(values) != 1 or not re.fullmatch('[A-Za-z0-9_-]{1,64}', values[0]):
        raise ValueError('Invalid Scholar URL in successful result')
    return values[0]


def check_date(value):
    date = datetime.fromisoformat(value)
    if date.tzinfo is None or date > datetime.now(timezone.utc):
        raise ValueError('Invalid retrieval date')


def apply(root, expect_proposed, expect_status, hold):
    root = Path(root)
    raws = {k: (root / k).read_bytes() for k in (PROPOSED, STATUS)}
    blobs = {k: blob(v) for k, v in raws.items()}
    if blobs[PROPOSED] != expect_proposed or blobs[STATUS] != expect_status:
        raise ValueError('Reviewed input does not match the approved blob IDs; no files updated')
    report_path = root / REPORT
    if report_path.exists():
        previous = json.loads(report_path.read_text(encoding='utf-8'))
        if previous.get('review_blobs') == blobs and previous.get('held_back') == sorted(hold):
            if blob((root / FACULTY).read_bytes()) != previous['output_blob']:
                raise ValueError('Published faculty data changed after this refresh')
            return previous, False
    current_raw = (root / FACULTY).read_bytes()
    current = json.loads(current_raw)
    proposed = json.loads(raws[PROPOSED])
    sr = json.loads(raws[STATUS])
    rows = {r['id']: r for r in current['faculty']}
    incoming = {r['id']: r for r in proposed['faculty']}
    if len(rows) != len(current['faculty']) or len(incoming) != len(proposed['faculty']) or set(rows) != set(incoming) or set(rows) != set(sr['faculty']) or sr['selected'] != len(rows):
        raise ValueError('Profile roster mismatch or duplicate IDs')
    counts = Counter(v['status'] for v in sr['faculty'].values())
    if counts.get('success', 0) != sr['success'] or counts.get('failed', 0) != sr['failed'] or sr['success'] + sr['failed'] != sr['selected']:
        raise ValueError('Scholar audit totals do not agree')
    unknown = [h for h in hold if h not in rows or sr['faculty'][h]['status'] != 'success']
    if unknown:
        raise ValueError('Hold-back IDs must be successful profiles: ' + ', '.join(unknown))
    strip = lambda doc: [{k: v for k, v in r.items() if k != 'scholar_metrics'} for r in doc['faculty']]
    if strip(current) != strip(proposed) or {k: v for k, v in current.items() if k != 'faculty'} != {k: v for k, v in proposed.items() if k != 'faculty'}:
        raise ValueError('Profiles changed after the audit ran; rerun the audit')
    mapped, skipped, held = [], [], []
    for identity, row in rows.items():
        status = sr['faculty'][identity]
        if status['status'] != 'success':
            skipped.append({'id': identity, 'reason': status.get('message'), 'previous_metrics_retained': 'scholar_metrics' in row})
            continue
        m = copy.deepcopy(incoming[identity].get('scholar_metrics', {}))
        aid = author(row.get('scholar_url'))
        if not (m.get('source') == 'Google Scholar' and m.get('provider') == 'SerpApi' and m.get('scope') == 'all-time' and m.get('status') == 'success' and author(m.get('scholar_url')) == aid and m.get('author_id') == aid and status.get('author_id') == aid and m.get('author_name') and m.get('retrieved_at') == status.get('retrieved_at') == sr['last_attempt']):
            raise ValueError('Scholar identity/source/date mismatch: ' + identity)
        check_date(m['retrieved_at'])
        if not all(type(m.get(k)) is int and 0 <= m[k] <= 9007199254740991 for k in ['total_citations', 'h_index', 'i10_index']) or m['h_index'] ** 2 > m['total_citations'] or 10 * m['i10_index'] > m['total_citations']:
            raise ValueError('Invalid Scholar metric values: ' + identity)
        m['scholar_url'] = row['scholar_url']
        if identity in hold:
            held.append({'id': identity, 'returned_author_name': m['author_name'], 'proposed_citations': m['total_citations']})
            continue
        row['scholar_metrics'] = m
        mapped.append({'id': identity, 'database_name': row['name'], 'department_id': row['department_id'], 'author_id': aid, 'returned_author_name': m['author_name'], 'retrieved_at': m['retrieved_at']})
    out = (json.dumps(current, ensure_ascii=False, indent=2) + '\n').encode()
    reasons = Counter(s['reason'] for s in skipped)
    report = {'review_blobs': blobs, 'applied_at': datetime.now(timezone.utc).isoformat(timespec='seconds'), 'retrieved_at': sr['last_attempt'], 'scholar_selected': sr['selected'], 'scholar_updated': len(mapped), 'scholar_not_updated': len(skipped), 'not_updated_reasons': dict(reasons), 'held_back': sorted(hold), 'held_back_details': held, 'scholar_mappings': mapped, 'scholar_exceptions': skipped, 'output_blob': blob(out),
              'notes': ['Only successful validated Scholar metrics are mapped. Failed attempts never replace existing values or become zero.', 'Names, photos, identifiers, roles, departments and publications are preserved.', 'Held-back profiles keep their previous Scholar metrics until reviewed.', 'No new provider requests are performed.']}
    (root / FACULTY).write_bytes(out)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return report, True


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    p.add_argument('--proposed-blob', required=True)
    p.add_argument('--status-blob', required=True)
    p.add_argument('--hold', default='')
    a = p.parse_args()
    hold = sorted({h.strip() for h in a.hold.split(',') if h.strip()})
    r, changed = apply(a.root, a.proposed_blob.strip(), a.status_blob.strip(), hold)
    print(json.dumps({'changed': changed, 'selected': r['scholar_selected'], 'updated': r['scholar_updated'], 'not_updated': r['scholar_not_updated'], 'held_back': r['held_back']}, indent=2))


if __name__ == '__main__':
    main()
