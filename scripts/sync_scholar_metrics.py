#!/usr/bin/env python3
"""Review-first Google Scholar metrics retrieval through SerpApi."""
import argparse
import copy
import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlsplit
from urllib.request import Request, urlopen
from urllib.error import HTTPError

FIELDS = {'citations': 'total_citations', 'h_index': 'h_index', 'i10_index': 'i10_index'}

def author_id(value):
    if not isinstance(value, str):
        raise ValueError('Missing Scholar profile URL')
    u = urlsplit(value)
    ids = parse_qs(u.query).get('user', [])
    if u.scheme != 'https' or u.netloc != 'scholar.google.com' or u.path != '/citations' or u.fragment or len(ids) != 1 or not re.fullmatch(r'[A-Za-z0-9_-]{1,64}', ids[0]):
        raise ValueError('Invalid Scholar profile URL')
    return ids[0]

def count(value):
    if type(value) is int and 0 <= value <= 9007199254740991:
        return value
    if isinstance(value, str) and re.fullmatch(r'(?:0|[1-9][0-9]*|[1-9][0-9]{0,2}(?:,[0-9]{3})+)', value):
        n = int(value.replace(',', ''))
        if n <= 9007199254740991:
            return n
    raise ValueError('Invalid metric value')

def parse_metrics(payload, url, stamp):
    expected = author_id(url)
    if not isinstance(payload, dict) or payload.get('error') or payload.get('search_metadata', {}).get('status') != 'Success':
        raise ValueError('Provider did not return a successful result')
    params = payload.get('search_parameters', {})
    if params.get('engine') != 'google_scholar_author' or params.get('author_id') != expected:
        raise ValueError('Returned author identifier does not match')
    source_url = payload.get('search_metadata', {}).get('google_scholar_author_url')
    if source_url and author_id(source_url) != expected:
        raise ValueError('Returned Scholar URL does not match')
    name = payload.get('author', {}).get('name')
    if not isinstance(name, str) or not name.strip():
        raise ValueError('Missing author name for review')
    rows = payload.get('cited_by', {}).get('table')
    if not isinstance(rows, list):
        raise ValueError('Missing metrics table')
    result = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError('Invalid metrics table')
        for source, target in FIELDS.items():
            if source in row:
                if target in result or not isinstance(row[source], dict) or 'all' not in row[source]:
                    raise ValueError('Missing or duplicated all-time metric')
                result[target] = count(row[source]['all'])
    if len(result) != 3:
        raise ValueError('Incomplete all-time metrics')
    if result['h_index'] ** 2 > result['total_citations'] or 10 * result['i10_index'] > result['total_citations']:
        raise ValueError('Inconsistent metric values')
    result.update(source='Google Scholar', provider='SerpApi', scope='all-time', scholar_url=url, author_id=expected, author_name=name.strip(), retrieved_at=stamp, last_attempt=stamp, status='success')
    return result

def retrieve(identifier):
    key = os.environ.get('SCHOLAR_SERPAPI_KEY', '').strip()
    if not key:
        raise RuntimeError('Missing SCHOLAR_SERPAPI_KEY')
    query = urlencode({'engine': 'google_scholar_author', 'author_id': identifier, 'hl': 'en', 'api_key': key, 'output': 'json'})
    request = Request('https://serpapi.com/search.json?' + query, headers={'Accept': 'application/json', 'User-Agent': 'KUWebsite-ScholarMetrics/1.0'})
    try:
        with urlopen(request, timeout=60) as response:
            return json.load(response)
    except HTTPError as error:
        raise RuntimeError('Provider HTTP ' + str(error.code)) from None
    except Exception:
        raise RuntimeError('Provider request or response failed') from None

def audit(document, fetch=retrieve, faculty='rakesh-tiwari', stamp=None):
    stamp = stamp or datetime.now(timezone.utc).isoformat(timespec='seconds')
    proposed = copy.deepcopy(document)
    rows = proposed.get('faculty')
    if not isinstance(rows, list) or any(not isinstance(f, dict) or not isinstance(f.get('id'), str) for f in rows):
        raise ValueError('Invalid faculty dataset')
    if len({f['id'] for f in rows}) != len(rows):
        raise ValueError('Duplicate faculty identifiers')
    selected = rows if faculty == 'all' else [f for f in rows if f['id'] == faculty]
    if not selected:
        raise ValueError('Requested faculty record not found')
    report = {'source': 'Google Scholar', 'provider': 'SerpApi', 'scope': 'all-time', 'last_attempt': stamp, 'selected': len(selected), 'success': 0, 'failed': 0, 'faculty': {}}
    responses = {}
    for f in selected:
        url = f.get('scholar_url')
        previous = f.get('scholar_metrics', {})
        try:
            identifier = author_id(url)
            if identifier not in responses:
                try:
                    responses[identifier] = (fetch(identifier), None)
                except Exception:
                    responses[identifier] = (None, 'Provider unavailable or not configured')
            payload, error = responses[identifier]
            if error:
                raise RuntimeError(error)
            metrics = parse_metrics(payload, url, stamp)
            f['scholar_metrics'] = metrics
            report['success'] += 1
            report['faculty'][f['id']] = {'status': 'success', 'author_id': identifier, 'author_name': metrics['author_name'], 'retrieved_at': stamp}
        except Exception as error:
            retained = isinstance(previous, dict) and previous.get('source') == 'Google Scholar' and previous.get('scope') == 'all-time' and previous.get('scholar_url') == url
            metrics = copy.deepcopy(previous) if retained else {'source': 'Google Scholar', 'scope': 'all-time', 'scholar_url': url}
            message = str(error) if isinstance(error, ValueError) else 'Provider unavailable or not configured'
            metrics.update(status='failed', last_attempt=stamp, message=message)
            f['scholar_metrics'] = metrics
            report['failed'] += 1
            report['faculty'][f['id']] = {'status': 'failed', 'message': message, 'last_success': metrics.get('retrieved_at')}
    return proposed, report

def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(dir=path.parent, prefix='.' + path.name)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            json.dump(data, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, default=Path('.'))
    p.add_argument('--out', type=Path, default=Path('scholar-audit'))
    p.add_argument('--faculty', default='rakesh-tiwari')
    p.add_argument('--live', action='store_true', help='Explicitly approve provider requests; may consume API quota')
    a = p.parse_args()
    if not a.live:
        p.error('Live retrieval disabled: use --live only after approval')
    if not os.environ.get('SCHOLAR_SERPAPI_KEY', '').strip():
        p.error('Missing SCHOLAR_SERPAPI_KEY; no provider requests made')
    document = json.loads((a.root / 'data/faculty.json').read_text(encoding='utf-8'))
    proposed, report = audit(document, faculty=a.faculty)
    write(a.out / 'faculty.proposed.json', proposed)
    write(a.out / 'scholar-sync-status.json', report)
    print(json.dumps({'selected': report['selected'], 'success': report['success'], 'failed': report['failed']}))
    return 2 if report['failed'] else 0

if __name__ == '__main__':
    raise SystemExit(main())
