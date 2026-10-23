import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('sync', Path(__file__).resolve().parents[1] / 'scripts/sync_orcid_publications.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

F = {'id': 'rakesh-tiwari', 'orcid': '0000-0002-2191-769X', 'department_id': 'environmental-science'}
G = {'id': 'colleague', 'orcid': '0000-0001-8652-8444', 'department_id': 'environmental-science'}
TITLE = 'A sufficiently descriptive title for a tropical forest research article'

def work(code=1, title=TITLE, doi='10.1234/example', year='2025', kind='journal-article'):
    return {'put-code': code, 'visibility': 'public', 'title': {'title': {'value': title}},
        'publication-date': {'year': {'value': year}} if year else None,
        'journal-title': {'value': 'Ecology'}, 'type': kind,
        'external-ids': {'external-id': [{'external-id-type': 'doi', 'external-id-value': doi,
            'external-id-relationship': 'self'}] if doi else []},
        'source': {'source-name': {'value': 'Publisher'}},
        'contributors': {'contributor': [{'credit-name': {'value': 'A Author'}}]}}

def record(f=F, code=1, **kwargs):
    return m.work_record(work(code=code, **kwargs), f, '2026-10-23T00:00:00+00:00')

class Fake:
    def __init__(self, works=(), fail=False, malformed=False):
        self.works, self.fail, self.malformed = list(works), fail, malformed
    def get(self, path):
        if self.fail:
            raise RuntimeError('ORCID HTTP 503')
        if path.endswith('/works'):
            if self.malformed:
                return {'unexpected': []}
            return {'group': [{'work-summary': [{'visibility': 'public', 'put-code': w['put-code']}]} for w in self.works]}
        return next(copy.deepcopy(w) for w in self.works if str(w['put-code']) == path.rsplit('/', 1)[1])

class Tests(unittest.TestCase):
    def test_orcid_checksum(self):
        self.assertTrue(m.valid_orcid(F['orcid']))
        self.assertTrue(m.valid_orcid(G['orcid']))
        self.assertFalse(m.valid_orcid('0000-0002-2191-7690'))
        self.assertFalse(m.valid_orcid('../../etc/passwd'))
    def test_normalise_doi(self):
        self.assertEqual(m.doi('https://doi.org/10.1234/ABC'), '10.1234/abc')
        self.assertEqual(m.doi('doi: 10.1234/ABC'), '10.1234/abc')
        self.assertEqual(m.doi('not a doi'), '')
    def test_public_only(self):
        w = work(); w['visibility'] = 'limited'
        with self.assertRaises(ValueError): m.work_record(w, F, 'now')
    def test_missing_fields(self):
        w = work(doi='', year=None)
        w.pop('contributors'); w.pop('journal-title')
        row = m.work_record(w, F, 'now')
        self.assertIsNone(row['year'])
        self.assertEqual(row['authors_display'], '')
        self.assertEqual(row['journal'], '')
    def test_skip_nonpublication(self):
        self.assertIsNone(m.work_record(work(kind='data-set'), F, 'now'))
    def test_parent_doi_not_used(self):
        w = work(); w['external-ids']['external-id'][0]['external-id-relationship'] = 'part-of'
        self.assertEqual(m.work_record(w, F, 'now')['doi'], '')
    def test_all_group_representations(self):
        client = Fake([work(1), work(2)])
        client.get_orig = client.get
        def get(path):
            if path.endswith('/works'):
                return {'group': [{'work-summary': [{'put-code': i, 'visibility': 'public'} for i in (1,2)]}]}
            return client.get_orig(path)
        client.get = get
        rows, count = m.fetch_faculty(client, F, 'now')
        self.assertEqual(count, 2)
        self.assertEqual(len(m.merge_records(rows)[0]), 1)
    def test_coauthored_dedup(self):
        rows, _ = m.merge_records([record(), record(G, 2)])
        self.assertEqual(len(rows), 1)
        self.assertEqual(set(rows[0]['faculty_ids']), {F['id'], G['id']})
        self.assertEqual(len(rows[0]['provenance']), 2)
    def test_distinct_dois_preserved(self):
        rows, warnings = m.merge_records([record(), record(code=2,doi='10.1234/other')])
        self.assertEqual(len(rows), 2)
        self.assertTrue(warnings)
    def test_cautious_no_doi_merge(self):
        rows, _ = m.merge_records([record(doi=''), record(G,2,doi='')])
        self.assertEqual(len(rows), 1)
        a,b = record(doi='',title='Short title'),record(G,2,doi='',title='Short title')
        self.assertEqual(len(m.merge_records([a,b])[0]), 2)
    def test_unicode_names_not_collapsed(self):
        self.assertNotEqual(m.title_key('ಕನ್ನಡ'), m.title_key('हिन्दी'))
    def test_no_doi_stable_id(self):
        a = record(doi='')
        b = copy.deepcopy(a); b['provenance'][0]['retrieved_at'] = 'tomorrow'
        self.assertEqual(m.merge_records([a])[0][0]['id'], m.merge_records([b])[0][0]['id'])
    def test_failed_retains_records_and_last_success(self):
        prior_row = m.merge_records([record()])[0][0]
        old = {'publications':[prior_row]}
        prior = {'faculty':{F['id']:{'last_success':'yesterday'}}}
        data, report = m.sync([F], old, prior, Fake(fail=True))
        self.assertEqual(len(data['publications']),1)
        self.assertEqual(report['faculty'][F['id']]['last_success'],'yesterday')
        self.assertFalse(report['all_successful'])
    def test_malformed_not_empty(self):
        data, report = m.sync([F], {'publications':[]}, {}, Fake(malformed=True))
        self.assertEqual(report['faculty'][F['id']]['status'],'failed')
    def test_success_replaces_metadata(self):
        old = {'publications':m.merge_records([record()])[0]}
        data, report = m.sync([F],old,{},Fake([work(title='Corrected title')]))
        self.assertTrue(report['all_successful'])
        self.assertEqual(data['publications'][0]['title'],'Corrected title')
    def test_empty_first_import(self):
        _, report = m.sync([F],{'publications':[]},{},Fake())
        self.assertEqual(report['faculty'][F['id']]['status'],'no_public_publications')
    def test_large_drop_review(self):
        old = {'publications':m.merge_records([record()])[0]}
        data, report = m.sync([F],old,{},Fake())
        self.assertEqual(len(data['publications']),1)
        self.assertEqual(report['faculty'][F['id']]['status'],'failed')
        self.assertTrue(report['faculty'][F['id']]['review_required'])
    def test_confirmed_removal(self):
        old = {'publications':m.merge_records([record()])[0]}
        data, report = m.sync([F],old,{},Fake(),True)
        self.assertEqual(data['publications'],[])
        self.assertTrue(report['all_successful'])
    def test_legacy_provenance_preserved(self):
        legacy={'id':'legacy','title':TITLE,'year':2025,'journal':'Ecology',
                'faculty_ids':[F['id']],'departments':['environmental-science'],
                'source_name':'Google Scholar','source_url':'https://scholar.google.com/example'}
        data, report = m.sync([F],{'publications':[legacy]}, {}, Fake([work()]))
        row=data['publications'][0]
        self.assertEqual(len(data['publications']),1)
        self.assertEqual({p['source_name'] for p in row['provenance']},{'ORCID','Google Scholar'})
    def test_failed_coauthor_retained_success_removed(self):
        old = {'publications':m.merge_records([record(),record(G,2)])[0]}
        client=Fake()
        def get(path):
            if G['orcid'] in path: raise RuntimeError('ORCID HTTP 503')
            return {'group':[]}
        client.get=get
        data, report=m.sync([F,G],old,{},client,True)
        self.assertEqual(data['publications'][0]['faculty_ids'],[G['id']])
    def test_safe_urls(self):
        self.assertEqual(m.safe_url('javascript:alert(1)'), '')
        self.assertEqual(m.safe_url('https://user:password@example.org/'), '')
        self.assertEqual(m.safe_url('https://example.org/a'), 'https://example.org/a')
    def test_atomic_output(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'data.json'; m.atomic_json(path,{'a':1})
            self.assertEqual(json.loads(path.read_text()),{'a':1})
    def test_default_cli_dry_run(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); (root/'data').mkdir()
            (root/'data/faculty.json').write_text(json.dumps({'faculty':[F]}))
            original=json.dumps({'publications':[]})
            (root/'data/publications.json').write_text(original)
            with patch.object(m,'Client',return_value=Fake([work()])), patch('sys.argv',['sync','--root',d,'--out',str(root/'audit')]), patch('builtins.print'):
                self.assertEqual(m.main(),0)
            self.assertEqual((root/'data/publications.json').read_text(),original)
            self.assertTrue((root/'audit/publications.proposed.json').exists())

if __name__ == '__main__': unittest.main()
