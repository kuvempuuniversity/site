import importlib.util
import unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('citation_sync',Path(__file__).resolve().parents[1]/'scripts/sync_citation_metrics.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
D='10.1234/example'
class CitationTests(unittest.TestCase):
    def result(self,fetch,prior=None,doi=D):
        return m.audit([{'doi':doi}],prior or {'entries':{}},fetch,'2026-10-23T00:00:00+00:00')
    def work(self,count=4,doi=D):return {'id':'https://openalex.org/W123','doi':'https://doi.org/'+doi,'cited_by_count':count}
    def test_doi(self):
        self.assertEqual(m.normalise_doi('https://doi.org/10.1234/EXAMPLE'),D)
        self.assertEqual(m.normalise_doi('not a DOI'),'')
    def test_zero_is_valid(self):
        data,report=self.result(lambda d:self.work(0));self.assertEqual(data['entries'][D]['count'],0);self.assertEqual(report['matched'],1)
    def test_missing_not_zero(self):
        data,report=self.result(lambda d:None);self.assertNotIn('count',data['entries'][D]);self.assertEqual(report['not_found'],1)
    def test_mismatch(self):
        data,report=self.result(lambda d:self.work(4,'10.1234/wrong'));self.assertEqual(report['failed'],1);self.assertNotIn('count',data['entries'][D])
    def test_invalid_counts(self):
        for count in [-1,True,1.5,None,'4']:
            with self.subTest(count=count):self.assertEqual(self.result(lambda d:self.work(count))[1]['failed'],1)
    def test_invalid_url(self):
        work=self.work();work['id']='javascript:alert(1)';self.assertEqual(self.result(lambda d:work)[1]['failed'],1)
    def test_retention(self):
        prior={'entries':{D:{'doi':D,'source':'OpenAlex','count':8,'retrieved_at':'2026-10-01','source_url':'https://openalex.org/W123','status':'success'}}}
        def fail(d):raise RuntimeError('OpenAlex HTTP 503')
        for fetch in [fail,lambda d:None]:
            data,_=self.result(fetch,prior);self.assertEqual(data['entries'][D]['count'],8);self.assertEqual(data['entries'][D]['retrieved_at'],'2026-10-01');self.assertEqual(prior['entries'][D]['status'],'success')
    def test_no_doi(self):
        def fail(d):raise AssertionError('Should not request')
        data,report=self.result(fail,doi='');self.assertEqual(data['entries'],{});self.assertEqual(report['without_doi'],1)
    def test_one_request_per_doi(self):
        calls=[]
        def fetch(d):calls.append(d);return self.work()
        m.audit([{'doi':D},{'doi':'https://doi.org/'+D}],{'entries':{}},fetch);self.assertEqual(calls,[D])
if __name__=='__main__':unittest.main()
