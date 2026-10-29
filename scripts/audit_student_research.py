#!/usr/bin/env python3
"""Review-only student research audit. Network requests require explicit flags."""
import argparse
import copy
import json
from pathlib import Path
import sync_orcid_publications as orcid
import sync_scholar_metrics as scholar
import sync_citation_metrics as citations

PREFIX = 'student:'

def valid_metrics(m, url):
    try:
        return (isinstance(m, dict) and m.get('source') == 'Google Scholar'
                and m.get('scope') == 'all-time' and m.get('status') == 'success'
                and scholar.author_id(m.get('scholar_url')) == scholar.author_id(url)
                and m.get('author_id') == scholar.author_id(url)
                and all(type(m.get(k)) is int and m[k] >= 0 for k in scholar.FIELDS.values())
                and m['h_index'] ** 2 <= m['total_citations']
                and 10 * m['i10_index'] <= m['total_citations']
                and bool(m.get('retrieved_at')))
    except (ValueError, TypeError, KeyError):
        return False

def encode(row):
    row = copy.deepcopy(row)
    row['faculty_ids'] = sorted(set(row.get('faculty_ids', [])) |
                                {PREFIX + sid for sid in row.get('student_ids', [])})
    for p in row.get('provenance', []):
        if p.get('student_id'):
            p['faculty_id'] = PREFIX + p.pop('student_id')
    return row

def decode(row):
    row = copy.deepcopy(row)
    ids = row.get('faculty_ids', [])
    row['student_ids'] = sorted(set(row.get('student_ids', [])) |
                               {i[len(PREFIX):] for i in ids if i.startswith(PREFIX)})
    row['faculty_ids'] = [i for i in ids if not i.startswith(PREFIX)]
    for p in row.get('provenance', []):
        if str(p.get('faculty_id', '')).startswith(PREFIX):
            p['student_id'] = p.pop('faculty_id')[len(PREFIX):]
    return row

def merge_students(existing, incoming):
    result = copy.deepcopy(existing)
    warnings = []
    for raw in incoming:
        row = decode(raw)
        d = orcid.doi(row.get('doi', ''))
        refs = {(p.get('orcid'), p.get('put_code')) for p in row.get('provenance', [])
                if p.get('source_name') == 'ORCID' and p.get('orcid') and p.get('put_code') is not None}
        candidates = [p for p in result if (d and orcid.doi(p.get('doi', '')) == d)
                      or refs.intersection({(v.get('orcid'), v.get('put_code'))
                                            for v in p.get('provenance', [])
                                            if v.get('source_name') == 'ORCID'})]
        if len(candidates) == 1:
            target = candidates[0]
            target['student_ids'] = sorted(set(target.get('student_ids', [])) | set(row['student_ids']))
            target['departments'] = sorted(set(target.get('departments', [])) | set(row.get('departments', [])))
            target.setdefault('provenance', [])
            for source in row.get('provenance', []):
                if source not in target['provenance']:
                    target['provenance'].append(source)
        else:
            row.pop('id', None)
            generated, notes = orcid.merge_records([encode(row)])
            new = decode(generated[0])
            if any(p.get('id') == new['id'] for p in result):
                raise ValueError('Publication ID collision; review required')
            result.append(new)
            warnings.extend(notes)
            if candidates:
                warnings.append('Ambiguous existing matches retained for review: ' + row['title'])
    return result, warnings

def audit(students, faculty, publications, prior_status, prior_metrics,
          client, live_orcid=False, live_scholar=False, fetch_scholar=None, stamp=None, faculty_publications=None):
    stamp = stamp or orcid.now()
    selected = [s for s in students if s.get('published') is True]
    if any(not isinstance(s.get('id'), str) or not s['id'] for s in selected):
        raise ValueError('Invalid student ID')
    if len({s['id'] for s in selected}) != len(selected):
        raise ValueError('Duplicate student IDs')
    report = {'last_attempt': stamp, 'students': {}, 'warnings': [],
              'network_enabled': {'orcid': live_orcid, 'scholar': live_scholar}}
    existing = publications.get('publications', [])
    faculty_rows = (faculty_publications or publications).get('publications', [])
    output = copy.deepcopy(publications)
    incoming = []
    metrics = copy.deepcopy(prior_metrics)
    metrics.setdefault('students', {})
    work_cache, scholar_cache = {}, {}
    for s in selected:
        sid, oid, url = s['id'], s.get('orcid', ''), s.get('scholar_url', '')
        previous = prior_status.get('students', {}).get(sid, {})
        entry = {'orcid': oid, 'last_attempt': stamp,
                 'last_success': previous.get('last_success')}
        if not oid:
            entry.update(status='not_configured', message='ORCID not configured')
        elif not orcid.valid_orcid(oid):
            entry.update(status='failed', message='Invalid ORCID identifier/checksum')
        else:
            try:
                if oid not in work_cache:
                    cached = None
                    for f in faculty:
                        fs = prior_status.get('faculty', {}).get(f['id'], {})
                        if (f.get('orcid') != oid or fs.get('orcid') != oid
                                or fs.get('status') not in ('success', 'no_public_publications')
                                or not fs.get('last_success')):
                            continue
                        works = []
                        for p in faculty_rows:
                            sources = [v for v in p.get('provenance', [])
                                       if v.get('source_name') == 'ORCID'
                                       and v.get('faculty_id') == f['id']
                                       and v.get('orcid') == oid
                                       and v.get('retrieved_at') == fs['last_success']]
                            if sources:
                                row = copy.deepcopy(p)
                                row['provenance'] = sources
                                works.append(row)
                        refs = {v['put_code'] for p in works for v in p['provenance']}
                        if len(refs) == fs.get('eligible_records'):
                            cached = (works, fs['last_success'], 'cached_faculty')
                            break
                    if cached is None and live_orcid:
                        pseudo = dict(s, id=PREFIX + sid)
                        works, _ = orcid.fetch_faculty(client, pseudo, stamp)
                        cached = (works, stamp, 'live_orcid')
                    work_cache[oid] = cached
                cached = work_cache[oid]
                if cached == 'failed':
                    raise ValueError('Cached ORCID failure')
                if cached is None:
                    entry.update(status='disabled', message='Live ORCID retrieval not approved')
                else:
                    works, retrieved, mode = cached
                    for p in works:
                        row = copy.deepcopy(p)
                        row['faculty_ids'] = [PREFIX + sid]
                        row['departments'] = [s['department_id']]
                        row.pop('student_ids', None)
                        for v in row['provenance']:
                            v['faculty_id'] = PREFIX + sid
                        incoming.append(row)
                    entry.update(status='success' if works else 'no_public_publications',
                                 last_success=retrieved, retrieval_mode=mode, message='',
                                 imported_entries=len(works))
            except Exception:
                work_cache[oid] = 'failed'
                entry.update(status='failed', message='ORCID retrieval or validation failed; existing records retained')
        report['students'][sid] = entry
        metric_status = 'not_configured'
        if url:
            try:
                aid = scholar.author_id(url)
                if aid not in scholar_cache:
                    reusable = next((f['scholar_metrics'] for f in faculty
                                     if valid_metrics(f.get('scholar_metrics'), url)), None)
                    if reusable:
                        scholar_cache[aid] = (copy.deepcopy(reusable), 'cached_faculty')
                    elif live_scholar:
                        fetch = fetch_scholar or scholar.retrieve
                        try:
                            scholar_cache[aid] = (scholar.parse_metrics(fetch(aid), url, stamp), 'live_scholar')
                        except Exception:
                            scholar_cache[aid] = (None, 'failed')
                    else:
                        scholar_cache[aid] = (None, 'disabled')
                m, mode = scholar_cache[aid]
                metric_status = 'success' if m else mode
                if m:
                    m = copy.deepcopy(m)
                    m['scholar_url'] = url
                    metrics['students'][sid] = m
            except (ValueError, TypeError):
                metric_status = 'failed'
        entry['scholar_status'] = metric_status
        old_metric = metrics['students'].get(sid)
        if old_metric and not valid_metrics(old_metric, url):
            metrics['students'].pop(sid, None)
        if metric_status in ('failed', 'disabled') and sid in metrics['students']:
            entry['scholar_retained_previous'] = True
    merged, warnings = merge_students(existing, incoming)
    output['publications'] = merged
    output['schema_version'] = max(output.get('schema_version', 2), 3)
    output['student_last_attempt'] = stamp
    report['warnings'] = warnings
    report['publication_count'] = len(output['publications'])
    report['failed'] = sum(v['status'] == 'failed' or v['scholar_status'] == 'failed'
                           for v in report['students'].values())
    metrics['last_attempt'] = stamp
    return output, report, metrics

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, default=Path('.'))
    p.add_argument('--out', type=Path, default=Path('student-research-audit'))
    p.add_argument('--live-orcid', action='store_true')
    p.add_argument('--live-scholar', action='store_true')
    p.add_argument('--live-citations', action='store_true')
    a = p.parse_args()
    read = lambda name, default: orcid.read_json(a.root / 'data' / name, default)
    students = read('research-students.json', {})['students']
    faculty = read('faculty.json', {})['faculty']
    prior = read('publication-sync-status.json', {})
    prior['students'] = read('student-publication-sync-status.json', {}).get('students', {})
    faculty_papers = read('publications.json', {'publications': []})
    publications = read('student-publications.json', {'publications': []})
    metrics = read('student-scholar-metrics.json', {'students': {}})
    out, report, sm = audit(students, faculty, publications, prior, metrics,
                           orcid.Client(__import__('os').environ.get('ORCID_ACCESS_TOKEN')),
                           a.live_orcid, a.live_scholar, faculty_publications=faculty_papers)
    combined_status = {}
    combined_status['students'] = report['students']
    combined_status['student_last_attempt'] = report['last_attempt']
    for name, obj in [('student-publications.proposed.json', out),
                      ('student-publication-sync-status.proposed.json', combined_status),
                      ('student-scholar-metrics.proposed.json', sm),
                      ('student-research-status.json', report)]:
        orcid.atomic_json(a.out / name, obj)
    if a.live_citations:
        prior_counts = read('citation-metrics.json', {'entries': {}})
        linked = [r for r in out['publications'] if r.get('student_ids')]
        manual = [p for s in students if s.get('published') is True
                  for p in s.get('publications', []) if isinstance(p, dict)]
        counts, cr = citations.audit(linked + manual, prior_counts)
        merged_counts = copy.deepcopy(prior_counts)
        merged_counts.setdefault('entries', {}).update(counts['entries'])
        merged_counts['last_attempt'] = counts['last_attempt']
        orcid.atomic_json(a.out / 'citation-metrics.proposed.json', merged_counts)
        orcid.atomic_json(a.out / 'student-citation-status.json', cr)
        report['failed'] += cr['failed']
    print(json.dumps({'students': len(report['students']), 'failed': report['failed']}))
    return 2 if report['failed'] else 0

if __name__ == '__main__':
    raise SystemExit(main())
