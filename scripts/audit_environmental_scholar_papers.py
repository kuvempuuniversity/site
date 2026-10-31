#!/usr/bin/env python3
"""One-off, review-only Environmental Science Scholar paper audit."""
import argparse
import csv
import hashlib
import json
import os
import re
import subprocess
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlsplit
from urllib.request import Request, urlopen
from sync_scholar_metrics import author_id, count, write

DEPARTMENT = 'environmental-science'
LIMIT = 20
EXPECTED = {'faculty.json': '17e44d48eb00cc0c01c2064d99b29343b047dfe8', 'research-students.json': '77aed4bd07ef49518666f972eca517dc772e2ffb'}

def norm(value):
    return ' '.join(re.sub(r'[^\w]+', ' ', unicodedata.normalize('NFKC', str(value or '')).casefold()).replace('_', ' ').split())

def candidates(article, papers):
    title = norm(article.get('title'))
    if len(title) < 40:
        return []
    matches = [i for i, p in enumerate(papers) if norm(p.get('title')) == title and str(p.get('year')) == str(article.get('year'))]
    if len(matches) != 1:
        return []
    i = matches[0]
    p = papers[i]
    authors = p.get('authors_display') or p.get('authors') or ''
    if isinstance(authors, list):
        authors = ' '.join(str(a) for a in authors)
    tokens = {t for t in norm(authors).split() if len(t) >= 4}
    if not tokens.intersection(norm(article.get('authors')).split()):
        return []
    return [i]

def observation(article, identifier):
    cid = article.get('citation_id', '')
    if not isinstance(cid, str) or not re.fullmatch(re.escape(identifier) + r':[A-Za-z0-9_-]+', cid):
        raise ValueError('Invalid article identity')
    cited = article.get('cited_by') or {}
    value = count(cited.get('value'))
    url = cited.get('link', '')
    u = urlsplit(url)
    clusters = parse_qs(u.query).get('cites', [])
    if u.scheme != 'https' or u.netloc != 'scholar.google.com' or u.path != '/scholar' or len(clusters) != 1 or not re.fullmatch(r'\d+(?:,\d+)*', clusters[0]):
        raise ValueError('Missing valid citing-document source link')
    return {'count': value, 'citation_id': cid, 'citing_url': url, 'clusters': sorted(clusters[0].split(',')), 'title': article.get('title'), 'year': article.get('year'), 'authors': article.get('authors'), 'publication': article.get('publication')}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live', action='store_true')
    parser.add_argument('--out', type=Path, default=Path('scholar-paper-audit'))
    args = parser.parse_args()
    if not args.live:
        parser.error('Provider calls require explicit --live approval')
    report = {'department_id': DEPARTMENT, 'source': 'Google Scholar', 'provider': 'SerpApi', 'review_only': True, 'request_limit': LIMIT, 'requests_attempted': 0, 'retrieved_at': datetime.now(timezone.utc).isoformat(timespec='seconds'), 'profiles': [], 'missing_profiles': [], 'unmatched_articles': [], 'papers': []}
    for filename, expected in EXPECTED.items():
        raw = (Path('data') / filename).read_bytes()
        actual = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
        if actual != expected:
            raise SystemExit('Researcher directory changed; review scope again before retrieval')
    faculty = json.loads(Path('data/faculty.json').read_text())['faculty']
    students = json.loads(Path('data/research-students.json').read_text())['students']
    members = [('faculty', p) for p in faculty if p.get('department_id') == DEPARTMENT]
    members += [('student', p) for p in students if p.get('department_id') == DEPARTMENT and p.get('published') is True]
    profiles = {}
    for role, person in members:
        info = {'role': role, 'id': person['id'], 'name': person.get('name'), 'scholar_url': person.get('scholar_url')}
        try:
            identifier = author_id(person.get('scholar_url'))
        except ValueError:
            report['missing_profiles'].append(info)
            continue
        profiles.setdefault(identifier, []).append(info)
    node = """const fs=require('fs');require('./assets/js/department-research.js');const files={faculty:'faculty.json',students:'research-students.json',publications:'publications.json',studentPublications:'student-publications.json',citations:'citation-metrics.json',studentCitations:'student-citation-metrics.json',status:'publication-sync-status.json',studentStatus:'student-publication-sync-status.json',phds:'department-phds.json'};const data=Object.fromEntries(Object.entries(files).map(([k,f])=>[k,JSON.parse(fs.readFileSync('data/'+f,'utf8'))]));const r=globalThis.KUDepartmentResearch.aggregate(data,'environmental-science');console.log(JSON.stringify({papers:r.papers,entries:r.metrics.entries}));"""
    collection = json.loads(subprocess.check_output(['node', '-e', node], text=True))
    papers = collection['papers']
    matches = [[] for p in papers]
    key = os.environ.get('SCHOLAR_SERPAPI_KEY', '').strip()
    if not key:
        report['error'] = 'Missing SCHOLAR_SERPAPI_KEY; no provider requests made'
    for identifier, people in profiles.items():
        entry = {'author_id': identifier, 'researchers': people, 'pages': 0, 'articles': 0, 'complete': False}
        report['profiles'].append(entry)
        if not key:
            entry['status'] = 'not_requested_missing_secret'
            continue
        offset = 0
        seen = set()
        for page in range(3):
            if report['requests_attempted'] >= LIMIT:
                entry['status'] = 'request_limit_reached'
                break
            params = {'engine': 'google_scholar_author', 'author_id': identifier, 'hl': 'en', 'num': 100, 'start': offset, 'api_key': key, 'output': 'json'}
            report['requests_attempted'] += 1
            try:
                request = Request('https://serpapi.com/search.json?' + urlencode(params), headers={'Accept': 'application/json', 'User-Agent': 'KUWebsite-ScholarPaperAudit/1.0'})
                with urlopen(request, timeout=60) as response:
                    payload = json.load(response)
                if payload.get('error') or payload.get('search_metadata', {}).get('status') != 'Success':
                    raise ValueError('Provider did not return success')
                returned = payload.get('search_parameters', {})
                if returned.get('engine') != 'google_scholar_author' or returned.get('author_id') != identifier:
                    raise ValueError('Provider returned a different profile')
                articles = payload.get('articles')
                if not isinstance(articles, list) or not payload.get('author', {}).get('name'):
                    raise ValueError('Incomplete profile response')
                entry['returned_name'] = payload['author']['name']
                entry['returned_affiliation'] = payload['author'].get('affiliations')
                entry['pages'] += 1
                for article in articles:
                    if not isinstance(article, dict):
                        continue
                    cid = article.get('citation_id')
                    if not cid or cid in seen:
                        continue
                    seen.add(cid)
                    entry['articles'] += 1
                    try:
                        obs = observation(article, identifier)
                        indices = candidates(article, papers)
                        if len(indices) == 1:
                            obs['author_id'] = identifier
                            matches[indices[0]].append(obs)
                        else:
                            report['unmatched_articles'].append({'author_id': identifier, 'citation_id': cid, 'title': article.get('title'), 'year': article.get('year'), 'reason': 'No unique exact-title/year match with supporting author overlap'})
                    except (ValueError, TypeError):
                        report['unmatched_articles'].append({'author_id': identifier, 'citation_id': cid, 'title': article.get('title'), 'reason': 'Citation count or provenance unavailable/invalid'})
                next_url = payload.get('serpapi_pagination', {}).get('next')
                if not next_url:
                    entry['complete'] = True
                    entry['status'] = 'retrieved'
                    break
                next_query = parse_qs(urlsplit(next_url).query)
                next_values = next_query.get('start') or next_query.get('cstart') or []
                if len(next_values) != 1 or not next_values[0].isdigit() or int(next_values[0]) <= offset:
                    entry['status'] = 'pagination_requires_review'
                    break
                offset = int(next_values[0])
                entry['status'] = 'profile_page_limit_reached'
            except Exception:
                entry['status'] = 'provider_failure_stopped_remaining_requests'
                key = ''
                report['error'] = 'Provider request or validation failed; remaining requests stopped. No credentials or raw provider responses saved.'
                break
    for paper, observations in zip(papers, matches):
        values = {o['count'] for o in observations}
        clusters = {tuple(o['clusters']) for o in observations}
        consistent = bool(observations) and len(values) == 1 and len(clusters) == 1
        old = collection['entries'].get(paper.get('doi'), {})
        report['papers'].append({'id': paper.get('id'), 'doi': paper.get('doi'), 'title': paper['title'], 'year': paper.get('year'), 'openalex_count': old.get('count'), 'openalex_retrieved_at': old.get('retrieved_at'), 'scholar_candidate_count': next(iter(values)) if consistent else None, 'status': 'candidate_needs_human_review' if consistent else 'conflicting_observations_needs_review' if observations else 'unmatched', 'observations': observations})
    good = [p for p in report['papers'] if p['scholar_candidate_count'] is not None]
    report['summary'] = {'eligible_papers': len(papers), 'candidate_matched_papers': len(good), 'candidate_scholar_sum_not_for_publication': sum(p['scholar_candidate_count'] for p in good) if good else None, 'openalex_sum_for_same_candidate_papers': sum(p['openalex_count'] for p in good if p['openalex_count'] is not None) if any(p['openalex_count'] is not None for p in good) else None, 'openalex_coverage_of_candidate_papers': sum(p['openalex_count'] is not None for p in good), 'profile_retrieval_complete': all(p['complete'] for p in report['profiles']) and bool(report['profiles'])}
    write(args.out / 'environmental-science-scholar-review.json', report)
    with (args.out / 'paper-comparison.csv').open('w', newline='', encoding='utf-8') as stream:
        fields = ['doi', 'title', 'year', 'openalex_count', 'openalex_retrieved_at', 'scholar_candidate_count', 'status']
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(report['papers'])
    print(json.dumps({'requests_attempted': report['requests_attempted'], **report['summary']}))
    return 2 if report.get('error') else 0

if __name__ == '__main__':
    raise SystemExit(main())
