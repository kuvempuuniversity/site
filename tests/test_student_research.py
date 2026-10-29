import copy
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import audit_student_research as a

OID = '0000-0002-2191-769X'
URL = 'https://scholar.google.com/citations?user=MTpM3HwAAAAJ&hl=en'
STAMP = '2026-10-29T12:57:30+00:00'

def person(sid='s'):
    return {'id':sid, 'published':True, 'name':'Test', 'department_id':'microbiology', 'orcid':OID}

def paper(fid='f'):
    return {'id':'p', 'title':'A sufficiently long publication title for the test', 'year':2024,
            'doi':'10.1234/test', 'journal':'Journal', 'type':'journal-article',
            'faculty_ids':[fid], 'departments':['microbiology'], 'source_name':'ORCID',
            'provenance':[{'source_name':'ORCID','faculty_id':fid,'orcid':OID,
                           'put_code':1,'retrieved_at':STAMP,'source_url':'https://orcid.org/'+OID}]}

class Tests(unittest.TestCase):
    def run_audit(self, students, faculty=None, pubs=None, status=None, metrics=None, **kwargs):
        return a.audit(students, faculty or [], pubs or {'publications':[]}, status or {},
                       metrics or {'students':{}}, object(), stamp=STAMP, **kwargs)

    def test_no_network_by_default(self):
        with patch.object(a.orcid,'fetch_faculty',side_effect=AssertionError('network')):
            out, report, _ = self.run_audit([person()])
        self.assertEqual(report['students']['s']['status'],'disabled')

    def test_missing_identifiers_are_not_failures(self):
        s=person();s.pop('orcid')
        _,report,_=self.run_audit([s])
        self.assertEqual(report['students']['s']['status'],'not_configured')
        self.assertEqual(report['failed'],0)

    def test_identity_is_not_profile_id(self):
        p=paper('s')
        out,_,_=self.run_audit([dict(person(),orcid='')],pubs={'publications':[p]})
        self.assertEqual(out['publications'][0].get('student_ids',[]),[])
        self.assertEqual(out['publications'][0]['faculty_ids'],['s'])

    def test_reuse_orcid_snapshot_preserves_links(self):
        p=paper();base={'publications':[p]};original=copy.deepcopy(base)
        prior={'faculty':{'f':{'orcid':OID,'status':'success','last_success':STAMP,'eligible_records':1}}}
        out,report,_=self.run_audit([person()],faculty=[dict(person('f'))],pubs=base,status=prior)
        self.assertEqual(out['publications'][0]['faculty_ids'],['f'])
        self.assertEqual(out['publications'][0]['student_ids'],['s'])
        self.assertEqual(base,original)
        self.assertEqual(report['students']['s']['retrieval_mode'],'cached_faculty')

    def test_multiple_students_share_one_retrieval(self):
        with patch.object(a.orcid,'fetch_faculty',return_value=([paper('student:s')],1)) as f:
            out,_,_=self.run_audit([person(),person('s2')],live_orcid=True)
        self.assertEqual(f.call_count,1)
        self.assertEqual(out['publications'][0]['student_ids'],['s','s2'])

    def test_failure_retains_existing_student_publications(self):
        p=paper();p['student_ids']=['s']
        with patch.object(a.orcid,'fetch_faculty',side_effect=ValueError('conflict')):
            out,report,_=self.run_audit([person()],pubs={'publications':[p]},live_orcid=True)
        self.assertEqual(out['publications'][0]['student_ids'],['s'])
        self.assertEqual(report['students']['s']['status'],'failed')

    def test_empty_response_does_not_delete_existing(self):
        p=paper();p['student_ids']=['s']
        with patch.object(a.orcid,'fetch_faculty',return_value=([],0)):
            out,report,_=self.run_audit([person()],pubs={'publications':[p]},live_orcid=True)
        self.assertEqual(len(out['publications']),1)
        self.assertEqual(report['students']['s']['status'],'no_public_publications')

    def test_duplicate_ids_rejected(self):
        with self.assertRaises(ValueError):self.run_audit([person(),person()])

    def test_unpublished_excluded(self):
        _,report,_=self.run_audit([dict(person(),published=False)])
        self.assertEqual(report['students'],{})

    def test_metrics_reused_and_timestamp_preserved(self):
        m={'source':'Google Scholar','scope':'all-time','status':'success','scholar_url':URL,
           'author_id':'MTpM3HwAAAAJ','retrieved_at':STAMP,'total_citations':10,'h_index':2,'i10_index':1}
        s=dict(person(),scholar_url=URL)
        _,report,metrics=self.run_audit([s],faculty=[{'id':'f','scholar_metrics':m}])
        self.assertEqual(report['students']['s']['scholar_status'],'success')
        self.assertEqual(metrics['students']['s']['retrieved_at'],STAMP)

    def test_metrics_from_other_identity_rejected(self):
        self.assertFalse(a.valid_metrics({'status':'success'},URL))

    def test_no_changes_to_existing_when_no_imports(self):
        p=paper();out,_,_=self.run_audit([],pubs={'publications':[p]})
        self.assertEqual(out['publications'],[p])

    def test_encoding_roundtrip(self):
        p=paper();p['student_ids']=['s'];p['provenance'].append({'source_name':'ORCID','student_id':'s','put_code':2})
        self.assertEqual(a.decode(a.encode(p)),p)

if __name__=='__main__':unittest.main()
