#!/usr/bin/env python3
"""Read public ORCID works. Default: dry run; --apply writes validated local data."""
import argparse
import copy
import hashlib
import json
import os
import re
import tempfile
import time
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlsplit, unquote
from urllib.request import Request, urlopen

API = 'https://pub.orcid.org/v3.0'
TYPES = {'journal-article', 'book', 'book-chapter', 'conference-paper',
         'conference-abstract', 'conference-poster', 'edited-book',
         'dissertation-thesis', 'preprint', 'report', 'review', 'working-paper'}


def now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def value(node):
    if isinstance(node, dict):
        return node.get('value') or ''
    return node if isinstance(node, str) else ''


def valid_orcid(identifier):
    if not isinstance(identifier, str) or not re.fullmatch(r'\d{4}-\d{4}-\d{4}-\d{3}[\dX]', identifier):
        return False
    total = 0
    for digit in identifier.replace('-', '')[:15]:
        total = (total + int(digit)) * 2
    check = (12 - total % 11) % 11
    return identifier[-1] == ('X' if check == 10 else str(check))


def doi(raw):
    raw = unquote(value(raw)).strip()
    raw = re.sub(r'^(?:https?://(?:dx\.)?doi\.org/|doi\s*:\s*)', '', raw, flags=re.I)
    if re.fullmatch(r'10\.\d{4,9}/\S+', raw, flags=re.I):
        return raw.lower()
    return ''


def safe_url(raw):
    raw = value(raw).strip()
    try:
        parsed = urlsplit(raw)
        return raw if parsed.scheme in ('https', 'http') and parsed.hostname and not parsed.username else ''
    except ValueError:
        return ''


def title_key(title):
    text = unicodedata.normalize('NFKC', title).casefold()
    return ' '.join(''.join(ch if ch.isalnum() else ' ' for ch in text).split())


def read_json(path, default):
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else copy.deepcopy(default)


def atomic_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(dir=path.parent, prefix='.' + path.name)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            json.dump(data, stream, ensure_ascii=False, indent=2, sort_keys=True)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


class Client:
    def __init__(self, token=None, sleep=time.sleep):
        self.token = token
        self.sleep = sleep

    def get(self, path):
        headers = {'Accept': 'application/json', 'User-Agent': 'KUWebsite-ORCID-Publications/1.0'}
        if self.token:
            headers['Authorization'] = 'Bearer ' + self.token
        for attempt in range(3):
            self.sleep(0.25)
            try:
                with urlopen(Request(API + path, headers=headers), timeout=30) as response:
                    payload = json.load(response)
                if not isinstance(payload, dict):
                    raise ValueError('ORCID response is not a JSON object')
                return payload
            except HTTPError as error:
                if error.code not in (429, 500, 502, 503, 504) or attempt == 2:
                    raise RuntimeError('ORCID HTTP ' + str(error.code)) from None
                delay = error.headers.get('Retry-After', '') if error.headers else ''
                self.sleep(min(int(delay), 60) if delay.isdigit() else 2 ** (attempt + 1))
            except (URLError, TimeoutError, OSError):
                if attempt == 2:
                    raise RuntimeError('ORCID network request failed') from None
                self.sleep(2 ** (attempt + 1))


def work_record(work, faculty, stamp):
    if work.get('visibility') != 'public':
        raise ValueError('Individual work did not explicitly confirm public visibility')
    title = value((work.get('title') or {}).get('title')).strip()
    if not title:
        raise ValueError('Public work has no usable title')
    kind = work.get('type') or ''
    if kind not in TYPES:
        return None
    identifiers = (work.get('external-ids') or {}).get('external-id') or []
    dois = sorted({doi(item.get('external-id-value')) for item in identifiers
                   if str(item.get('external-id-type', '')).lower() == 'doi'
                   and item.get('external-id-relationship') == 'self'
                   and doi(item.get('external-id-value'))})
    if len(dois) > 1:
        raise ValueError('Work has conflicting self DOIs; review required')
    date = work.get('publication-date') or {}
    raw_year = value(date.get('year'))
    year = int(raw_year) if re.fullmatch(r'\d{4}', raw_year) and 1000 <= int(raw_year) <= 9999 else None
    authors = []
    for contributor in (work.get('contributors') or {}).get('contributor') or []:
        attributes = contributor.get('contributor-attributes') or {}
        if attributes.get('contributor-role') not in (None, 'author'):
            continue
        name = value(contributor.get('credit-name')).strip()
        if name and name not in authors:
            authors.append(name)
    put_code = work.get('put-code')
    if not isinstance(put_code, int):
        raise ValueError('Missing work put-code')
    provenance = {'source_name': 'ORCID', 'orcid': faculty['orcid'],
                  'put_code': put_code, 'faculty_id': faculty['id'],
                  'source_url': 'https://orcid.org/' + faculty['orcid'],
                  'retrieved_at': stamp, 'record_source': value((work.get('source') or {}).get('source-name'))}
    paper_doi = dois[0] if dois else ''
    return {'title': title, 'year': year, 'type': kind,
            'journal': value(work.get('journal-title')),
            'reference': '', 'doi': paper_doi,
            'url': 'https://doi.org/' + paper_doi if paper_doi else safe_url(work.get('url')),
            'authors_display': ', '.join(authors), 'authors_truncated': False,
            'faculty_ids': [faculty['id']], 'departments': [faculty['department_id']],
            'source_name': 'ORCID', 'source_url': provenance['source_url'],
            'provenance': [provenance]}


def fetch_faculty(client, faculty, stamp):
    identifier = faculty.get('orcid', '')
    if not valid_orcid(identifier):
        raise ValueError('Invalid ORCID identifier/checksum')
    response = client.get('/' + identifier + '/works')
    if 'group' not in response or not isinstance(response['group'], list):
        raise ValueError('Invalid works collection; missing group array')
    rows, seen, count = [], set(), 0
    for group in response['group']:
        summaries = group.get('work-summary')
        if not isinstance(summaries, list) or not summaries:
            raise ValueError('Invalid work group')
        for summary in summaries:
            if summary.get('visibility') != 'public':
                raise ValueError('Unexpected non-public summary')
            code = summary.get('put-code')
            if not isinstance(code, int):
                raise ValueError('Invalid work summary put-code')
            if code in seen:
                continue
            seen.add(code)
            work = client.get('/' + identifier + '/work/' + str(code))
            if work.get('put-code') != code:
                raise ValueError('Work response identity mismatch')
            count += 1
            row = work_record(work, faculty, stamp)
            if row:
                rows.append(row)
    return rows, count


def legacy_sources(row):
    return [p for p in row.get('provenance', []) if p.get('source_name') != 'ORCID']


def normalise_old(rows):
    normalised = []
    for old in rows:
        row = copy.deepcopy(old)
        row.setdefault('doi', '')
        row['doi'] = doi(row['doi'])
        if 'provenance' not in row:
            row['provenance'] = [{'source_name': row.get('source_name', 'Legacy import'),
                'source_url': row.get('source_url', ''),
                'faculty_ids': list(row.get('faculty_ids', [])),
                'departments': list(row.get('departments', []))}]
        for p in row['provenance']:
            if p.get('source_name') != 'ORCID':
                p.setdefault('faculty_ids', list(row.get('faculty_ids', [])))
                p.setdefault('departments', list(row.get('departments', [])))
        normalised.append(row)
    return normalised


def rebase_old(rows, snapshots, faculty):
    departments = {f['id']: f['department_id'] for f in faculty}
    valid_refs = {fid: {p['put_code'] for row in fetched for p in row['provenance']}
                  for fid, fetched in snapshots.items()}
    kept = []
    for row in normalise_old(rows):
        row['provenance'] = [p for p in row['provenance']
            if p.get('source_name') != 'ORCID' or p.get('faculty_id') not in valid_refs
            or p.get('put_code') in valid_refs[p['faculty_id']]]
        if not row['provenance']:
            continue
        ids, depts = set(), set()
        for p in row['provenance']:
            if p.get('source_name') == 'ORCID':
                ids.add(p['faculty_id'])
                if p['faculty_id'] in departments:
                    depts.add(departments[p['faculty_id']])
            else:
                ids.update(p.get('faculty_ids', []))
                depts.update(p.get('departments', []))
        row['faculty_ids'], row['departments'] = sorted(ids), sorted(depts)
        # Successful sources are reconstructed using current metadata, not stale fields.
        surviving_failed = [p for p in row['provenance'] if p.get('source_name') == 'ORCID'
                            and p.get('faculty_id') not in snapshots]
        other = legacy_sources(row)
        if surviving_failed or other:
            row['provenance'] = surviving_failed + other
            ids = {p['faculty_id'] for p in surviving_failed}
            for p in other:
                ids.update(p.get('faculty_ids', []))
            row['faculty_ids'] = sorted(ids)
            row['departments'] = sorted({departments[i] for i in ids if i in departments}
                                       | {d for p in other for d in p.get('departments', [])})
            kept.append(row)
    return kept


def merge_records(rows):
    merged, warnings = [], []
    for incoming in rows:
        row = copy.deepcopy(incoming)
        row['doi'] = doi(row.get('doi', ''))
        key = (title_key(row['title']), row.get('year'))
        candidates = [p for p in merged if row['doi'] and p.get('doi') == row['doi']]
        if not candidates:
            possible = [p for p in merged if (title_key(p['title']), p.get('year')) == key]
            # Never title-merge distinct DOIs or records without sufficient identifying data.
            candidates = [p for p in possible if not (p.get('doi') and row['doi'])
                          and row.get('year') is not None and len(key[0]) >= 40
                          and p.get('journal') and row.get('journal')
                          and title_key(p['journal']) == title_key(row['journal'])
                          and (not p.get('type') or not row.get('type') or p['type'] == row['type'])]
            if possible and not candidates:
                warnings.append('Review possible duplicate: ' + row['title'])
        if len(candidates) == 1:
            target = candidates[0]
            target['faculty_ids'] = sorted(set(target['faculty_ids']) | set(row['faculty_ids']))
            target['departments'] = sorted(set(target['departments']) | set(row['departments']))
            for field in ('doi', 'url', 'authors_display', 'journal', 'reference', 'type'):
                if not target.get(field) and row.get(field):
                    target[field] = row[field]
            if target.get('doi'):
                target['url'] = 'https://doi.org/' + target['doi']
            sources = {(p.get('source_name'), p.get('faculty_id'), p.get('put_code'), p.get('source_url')): p
                       for p in target['provenance'] + row['provenance']}
            target['provenance'] = list(sources.values())
            target['source_name'] = ' + '.join(sorted({p['source_name'] for p in target['provenance']}))
        else:
            seed = row['doi'] or '|'.join([key[0], str(key[1]), json.dumps(row['provenance'], sort_keys=True)])
            # Provenance timestamp must not change no-DOI identifiers on each refresh.
            stable = re.sub(r'"retrieved_at": "[^"]*",? ?', '', seed)
            row.setdefault('id', 'pub-' + hashlib.sha256(stable.encode()).hexdigest()[:20])
            merged.append(row)
    merged.sort(key=lambda p: (-(p.get('year') or 0), title_key(p['title']), p['id']))
    return merged, sorted(set(warnings))


def sync(faculty, old, prior, client, confirmed_removals=False):
    stamp, snapshots, status = now(), {}, {}
    previous = normalise_old(old.get('publications', []))
    for f in faculty:
        fid = f['id']
        before = copy.deepcopy(prior.get('faculty', {}).get(fid, {}))
        before.update({'orcid': f.get('orcid', ''), 'last_attempt': stamp})
        try:
            rows, count = fetch_faculty(client, f, stamp)
            before.update({'status': 'success' if rows else 'no_public_publications',
                           'last_success': stamp, 'retrieved_records': count,
                           'eligible_records': len(rows), 'message': ''})
            old_refs = {p['put_code'] for row in previous for p in row['provenance']
                        if p.get('source_name') == 'ORCID' and p.get('faculty_id') == fid}
            new_refs = {p['put_code'] for row in rows for p in row['provenance']}
            missing = old_refs - new_refs
            # Confirm absence with a second complete read; failed confirmation retains old data.
            if missing:
                checked, checked_count = fetch_faculty(client, f, stamp)
                check_refs = {p['put_code'] for row in checked for p in row['provenance']}
                if check_refs != new_refs:
                    raise ValueError('Collection changed during removal verification')
                before['confirmed_missing_put_codes'] = sorted(missing)
                before['review_required'] = not rows or (old_refs and len(missing) / len(old_refs) >= 0.5)
                if before['review_required'] and not confirmed_removals:
                    raise ValueError('Large/empty reduction requires review and --confirm-removals')
            else:
                before.pop('confirmed_missing_put_codes', None)
                before['review_required'] = False
            snapshots[fid] = rows
        except Exception as error:
            # Do not expose tokens, request headers, or raw exception bodies in published status.
            message = str(error) if isinstance(error, (ValueError, RuntimeError)) else type(error).__name__
            before.update({'status': 'failed', 'message': message[:180]})
            before['last_success'] = prior.get('faculty', {}).get(fid, {}).get('last_success')
        status[fid] = before
    base = rebase_old(previous, snapshots, faculty)
    records, warnings = merge_records(base + [row for rows in snapshots.values() for row in rows])
    output = copy.deepcopy(old)
    output.update({'schema_version': 2, 'publications': records,
        'last_attempt': stamp, 'last_successful_sync': stamp if len(snapshots) == len(faculty) else old.get('last_successful_sync'),
        'coverage': 'Public ORCID publication metadata with preserved legacy source records. Not a complete or ranked bibliography.'})
    report = {'schema_version': 1, 'last_attempt': stamp, 'faculty': status,
              'warnings': warnings, 'all_successful': len(snapshots) == len(faculty),
              'successful_faculty': len(snapshots), 'faculty_count': len(faculty), 'publication_count': len(records)}
    return output, report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path('.'))
    parser.add_argument('--out', type=Path, default=Path('orcid-audit'))
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--confirm-removals', action='store_true')
    args = parser.parse_args()
    faculty = read_json(args.root / 'data/faculty.json', {})['faculty']
    if not faculty or len({f['id'] for f in faculty}) != len(faculty):
        raise ValueError('Faculty IDs must be non-empty and unique')
    old = read_json(args.root / 'data/publications.json', {'publications': []})
    prior = read_json(args.root / 'data/publication-sync-status.json', {})
    data, report = sync(faculty, old, prior, Client(os.environ.get('ORCID_ACCESS_TOKEN')), args.confirm_removals)
    # Always produce a dry-run review artifact; --apply is an explicit separate operation.
    atomic_json(args.out / 'publications.proposed.json', data)
    atomic_json(args.out / 'publication-sync-status.json', report)
    if args.apply:
        atomic_json(args.root / 'data/publications.json', data)
        atomic_json(args.root / 'data/publication-sync-status.json', report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report['all_successful'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
