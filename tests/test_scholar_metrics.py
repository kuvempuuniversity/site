import copy
import importlib.util
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

spec = importlib.util.spec_from_file_location('scholar_metrics', Path(__file__).resolve().parents[1] / 'scripts/sync_scholar_metrics.py')
s = importlib.util.module_from_spec(spec)
spec.loader.exec_module(s)
URL = 'https://scholar.google.com/citations?user=TEST123&hl=en'
STAMP = '2026-10-24T02:00:00+00:00'

def payload():
    return {'search_metadata': {'status': 'Success', 'google_scholar_author_url': URL}, 'search_parameters': {'engine': 'google_scholar_author', 'author_id': 'TEST123'}, 'author': {'name': 'Test Author'}, 'cited_by': {'table': [{'citations': {'all': 1200, 'since_2021': 900}}, {'h_index': {'all': 20, 'since_2021': 12}}, {'i10_index': {'all': 30, 'since_2021': 20}}]}}

def document():
    return {'faculty': [{'id': 'rakesh-tiwari', 'name': 'Test Author', 'scholar_url': URL, 'biography': 'Preserve this'}, {'id': 'other', 'scholar_url': URL, 'email': 'keep@example.org'}]}

class ScholarTests(unittest.TestCase):
    def test_all_time_not_recent(self):
        m = s.parse_metrics(payload(), URL, STAMP)
        self.assertEqual((m['total_citations'], m['h_index'], m['i10_index']), (1200, 20, 30))
        self.assertEqual(m['retrieved_at'], STAMP)
    def test_wrong_author(self):
        p = payload(); p['search_parameters']['author_id'] = 'WRONG'
        with self.assertRaises(ValueError): s.parse_metrics(p, URL, STAMP)
    def test_wrong_source_url(self):
        p = payload(); p['search_metadata']['google_scholar_author_url'] = URL.replace('TEST123', 'WRONG')
        with self.assertRaises(ValueError): s.parse_metrics(p, URL, STAMP)
    def test_missing_or_recent_only(self):
        for change in ('missing', 'recent'):
            p = payload()
            if change == 'missing': p['cited_by']['table'].pop()
            else: del p['cited_by']['table'][0]['citations']['all']
            with self.assertRaises(ValueError): s.parse_metrics(p, URL, STAMP)
    def test_invalid_values(self):
        for value in (-1, True, 1.5, '1.5', '', None, 9007199254740992):
            with self.subTest(value=value):
                p = payload(); p['cited_by']['table'][0]['citations']['all'] = value
                with self.assertRaises(ValueError): s.parse_metrics(p, URL, STAMP)
    def test_formatted_counts_and_real_zero(self):
        self.assertEqual(s.count('1,234'), 1234)
        p = payload()
        for row in p['cited_by']['table']:
            for value in row.values(): value['all'] = 0
        self.assertEqual(s.parse_metrics(p, URL, STAMP)['h_index'], 0)
    def test_inconsistent_and_duplicate(self):
        p = payload(); p['cited_by']['table'][1]['h_index']['all'] = 100
        with self.assertRaises(ValueError): s.parse_metrics(p, URL, STAMP)
        p = payload(); p['cited_by']['table'].append(copy.deepcopy(p['cited_by']['table'][0]))
        with self.assertRaises(ValueError): s.parse_metrics(p, URL, STAMP)
    def test_provider_error(self):
        p = payload(); p['error'] = 'Provider error'
        with self.assertRaises(ValueError): s.parse_metrics(p, URL, STAMP)
    def test_failure_retains_original_date(self):
        d = document(); old = s.parse_metrics(payload(), URL, '2026-10-01T00:00:00+00:00'); d['faculty'][0]['scholar_metrics'] = old
        proposed, report = s.audit(d, Mock(side_effect=RuntimeError('SECRET')), stamp=STAMP)
        m = proposed['faculty'][0]['scholar_metrics']
        self.assertEqual(m['retrieved_at'], old['retrieved_at'])
        self.assertEqual(m['total_citations'], 1200)
        self.assertEqual(m['status'], 'failed')
        self.assertNotIn('SECRET', str(report))
        self.assertEqual(d['faculty'][0]['scholar_metrics']['status'], 'success')
    def test_no_cache_failure_is_not_zero(self):
        proposed, _ = s.audit(document(), Mock(side_effect=RuntimeError()), stamp=STAMP)
        self.assertNotIn('total_citations', proposed['faculty'][0]['scholar_metrics'])
    def test_pilot_preserves_other_data(self):
        d = document(); original = copy.deepcopy(d)
        proposed, report = s.audit(d, lambda _: payload(), stamp=STAMP)
        self.assertEqual(proposed['faculty'][1], d['faculty'][1])
        self.assertEqual(proposed['faculty'][0]['biography'], 'Preserve this')
        self.assertEqual(d, original)
        self.assertEqual(report['selected'], 1)
    def test_duplicate_author_fetched_once(self):
        fetch = Mock(return_value=payload())
        _, report = s.audit(document(), fetch, faculty='all', stamp=STAMP)
        self.assertEqual(fetch.call_count, 1)
        self.assertEqual(report['success'], 2)
    def test_changed_profile_does_not_keep_wrong_cache(self):
        d = document(); d['faculty'][0]['scholar_metrics'] = {'source': 'Google Scholar', 'scope': 'all-time', 'scholar_url': URL.replace('TEST123', 'OLD'), 'total_citations': 999}
        proposed, _ = s.audit(d, Mock(side_effect=RuntimeError()), stamp=STAMP)
        self.assertNotIn('total_citations', proposed['faculty'][0]['scholar_metrics'])
    def test_bad_urls_never_requested(self):
        for url in ('http://scholar.google.com/citations?user=A', 'https://evil.example/citations?user=A', URL + '&user=OTHER'):
            d = document(); d['faculty'][0]['scholar_url'] = url; fetch = Mock()
            _, report = s.audit(d, fetch, stamp=STAMP)
            fetch.assert_not_called(); self.assertEqual(report['failed'], 1)
    def test_no_key_never_requests(self):
        with patch.dict('os.environ', {}, clear=True), patch.object(s, 'urlopen') as request:
            with self.assertRaises(RuntimeError): s.retrieve('TEST123')
            request.assert_not_called()
    def test_duplicate_faculty_ids_rejected(self):
        d = document(); d['faculty'][1]['id'] = 'rakesh-tiwari'
        with self.assertRaises(ValueError): s.audit(d, lambda _: payload())

if __name__ == '__main__': unittest.main()
