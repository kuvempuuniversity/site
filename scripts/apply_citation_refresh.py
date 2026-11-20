"""Apply a reviewed DOI citation batch without new provider requests.

Routine: run the citation audit, upload its two review files to data/citation-refresh-review/,
then run the apply workflow manually. No file fingerprints are hard-coded: the script records
what it applied and uses that to detect repeats and unexpected edits to the live cache.
"""
import copy
import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote

REVIEW = ['data/citation-refresh-review/citation-metrics.proposed.json',
          'data/citation-refresh-review/citation-audit-status.json']
DEST = 'data/citation-metrics.json'
PUBLICATIONS = 'data/publications.json'
REPORT = 'data/citation-refresh-apply-status.json'
KEEP_HISTORY = 20


def blob(raw):
    return hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()


def doi(value):
    value = re.sub(r'^(?:https?://(?:dx\.)?doi\.org/|doi\s*:\s*)', '', unquote(str(value or '')).strip(), flags=re.I).lower()
    return value if re.fullmatch(r'10\.\d{4,9}/\S+', value) else ''


def dated(value):
    try:
        d = datetime.fromisoformat(value)
        return d.tzinfo is not None and d <= datetime.now(timezone.utc)
    except (TypeError, ValueError):
        return False


def valid(entry, key):
    return isinstance(entry, dict) and entry.get('doi') == key and entry.get('source') == 'OpenAlex' and type(entry.get('count')) is int and 0 <= entry['count'] <= 9007199254740991 and bool(re.fullmatch(r'https://openalex\.org/W\d+', entry.get('source_url', ''))) and dated(entry.get('retrieved_at'))


def apply(root):
    root = Path(root)
    rp = root / REPORT
    review_now = {k: blob((root / k).read_bytes()) for k in REVIEW}
    previous = json.loads(rp.read_text()) if rp.exists() else None
    if previous:
        if blob((root / DEST).read_bytes()) != previous['output_blob']:
            raise ValueError('Live citation cache changed since the last applied batch; review required')
        if previous.get('review_blobs') == review_now:
            return previous
    read = lambda path: json.loads((root / path).read_text())
    proposed = read(REVIEW[0])
    audit = read(REVIEW[1])
    papers = read(PUBLICATIONS)['publications']
    cache = read(DEST)
    stamp = audit['last_attempt']
    entries = proposed['entries']
    expected_dois = {doi(p.get('doi')) for p in papers if doi(p.get('doi'))}
    counts = Counter(e['status'] for e in entries.values())
    if not dated(stamp) or proposed.get('last_attempt') != stamp or proposed.get('source') != 'OpenAlex' or cache.get('source') != 'OpenAlex':
        raise ValueError('Invalid source or retrieval date')
    if previous and stamp <= previous['retrieved_at']:
        raise ValueError('Batch is not newer than the last applied batch')
    if set(entries) != expected_dois or len(expected_dois) != audit['unique_dois'] or len(papers) != audit['publications'] or sum(not doi(p.get('doi')) for p in papers) != audit['without_doi']:
        raise ValueError('Citation batch does not match the active publication collection')
    if set(counts) - {'success', 'not_found', 'failed'} or counts['success'] != audit['matched'] or counts['not_found'] != audit['not_found'] or counts['failed'] != audit['failed']:
        raise ValueError('Citation audit totals do not agree')
    updated = []
    exceptions = []
    cache.setdefault('entries', {})
    for key, entry in entries.items():
        if doi(key) != key or entry.get('doi') != key or entry.get('source') != 'OpenAlex' or entry.get('last_attempt') != stamp:
            raise ValueError('Invalid DOI, source or attempt date: ' + key)
        prior = cache['entries'].get(key)
        if entry['status'] == 'success':
            if not valid(entry, key) or entry.get('retrieved_at') != stamp:
                raise ValueError('Invalid successful citation result: ' + key)
            if valid(prior, key) and datetime.fromisoformat(prior['retrieved_at']) > datetime.fromisoformat(stamp):
                raise ValueError('Would overwrite a newer citation count: ' + key)
            cache['entries'][key] = copy.deepcopy(entry)
            updated.append(key)
        else:
            retained = valid(prior, key)
            kept = copy.deepcopy(prior) if retained else {'doi': key, 'source': 'OpenAlex'}
            kept.update(status=entry['status'], last_attempt=stamp, message=entry.get('message', 'Lookup unavailable'))
            cache['entries'][key] = kept
            exceptions.append({'doi': key, 'status': entry['status'], 'message': entry.get('message'), 'previous_count_retained': retained, 'retained_count': prior.get('count') if retained else None, 'retained_retrieved_at': prior.get('retrieved_at') if retained else None})
    cache['last_attempt'] = stamp
    raw = (json.dumps(cache, ensure_ascii=False, indent=2) + '\n').encode()
    history = list((previous or {}).get('history', []))
    if previous:
        history.append({k: previous.get(k) for k in ['applied_at', 'retrieved_at', 'publications', 'unique_dois', 'matched_published', 'not_found', 'failed', 'without_doi']})
    result = {'review_blobs': review_now, 'applied_at': datetime.now(timezone.utc).isoformat(timespec='seconds'), 'retrieved_at': stamp,
              'publications': len(papers), 'unique_dois': len(expected_dois), 'matched_published': len(updated),
              'not_found': counts['not_found'], 'failed': counts['failed'], 'without_doi': audit['without_doi'],
              'exceptions': exceptions, 'output_blob': blob(raw), 'history': history[-KEEP_HISTORY:],
              'notes': ['Successful DOI-matched OpenAlex counts are published.',
                        'For unsuccessful lookups, valid prior counts retain their original retrieval dates and latest lookup status is marked unavailable. Otherwise no count is assigned.',
                        'Names, portraits, publications, student datasets, Scholar profile metrics, the Environmental Science Scholar snapshot and static showcase rankings are unchanged.',
                        'No new provider requests are performed.']}
    (root / DEST).write_bytes(raw)
    rp.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return result


if __name__ == '__main__':
    r = apply(Path(__file__).resolve().parents[1])
    print(json.dumps({k: r[k] for k in ['publications', 'unique_dois', 'matched_published', 'not_found', 'failed', 'without_doi', 'exceptions']}, indent=2))
