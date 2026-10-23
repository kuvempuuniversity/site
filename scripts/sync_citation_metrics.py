#!/usr/bin/env python3
"""Audit DOI-matched OpenAlex citation counts; dry-run by default."""
import argparse
import copy
import json
import os
import re
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

def normalise_doi(value):
    text=re.sub(r'^(?:https?://(?:dx\.)?doi\.org/|doi\s*:\s*)','',str(value or '').strip(),flags=re.I).lower()
    return text if re.fullmatch(r'10\.\d{4,9}/\S+',text) else ''

def read(path,default):
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else copy.deepcopy(default)

def write(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    fd,name=tempfile.mkstemp(dir=path.parent,prefix='.'+path.name)
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as stream:
            json.dump(data,stream,ensure_ascii=False,indent=2,sort_keys=True);stream.write('\n')
        os.replace(name,path)
    finally:
        if os.path.exists(name):os.unlink(name)

def retrieve(doi):
    url='https://api.openalex.org/works/https://doi.org/'+quote(doi,safe='')+'?select=id,doi,cited_by_count'
    headers={'Accept':'application/json','User-Agent':'KUWebsite-Citations/1.0'}
    if os.environ.get('OPENALEX_API_KEY'):headers['Authorization']='Bearer '+os.environ['OPENALEX_API_KEY']
    for attempt in range(3):
        time.sleep(.15)
        try:
            with urlopen(Request(url,headers=headers),timeout=30) as response:return json.load(response)
        except HTTPError as error:
            if error.code==404:return None
            if error.code not in (429,500,502,503,504) or attempt==2:raise RuntimeError('OpenAlex HTTP '+str(error.code)) from None
            delay=error.headers.get('Retry-After','') if error.headers else ''
            time.sleep(min(int(delay),60) if delay.isdigit() else 2**(attempt+1))
        except (URLError,TimeoutError,OSError):
            if attempt==2:raise RuntimeError('OpenAlex network request failed') from None
            time.sleep(2**(attempt+1))

def audit(publications,prior,fetch=retrieve,stamp=None):
    stamp=stamp or datetime.now(timezone.utc).isoformat(timespec='seconds')
    entries={};stats={'matched':0,'not_found':0,'failed':0,'without_doi':0}
    dois=set()
    for paper in publications:
        doi=normalise_doi(paper.get('doi'))
        if doi:dois.add(doi)
        else:stats['without_doi']+=1
    for doi in sorted(dois):
        previous=prior.get('entries',{}).get(doi,{})
        entry=copy.deepcopy(previous) if previous.get('source')=='OpenAlex' and previous.get('doi')==doi else {}
        entry.update({'doi':doi,'source':'OpenAlex','last_attempt':stamp})
        try:
            work=fetch(doi)
            if work is None:
                entry.update({'status':'not_found','message':'No exact DOI record returned.'});stats['not_found']+=1
            else:
                if not isinstance(work,dict) or normalise_doi(work.get('doi'))!=doi:raise ValueError('Returned DOI does not match; review required')
                count=work.get('cited_by_count');identifier=work.get('id','')
                if type(count) is not int or count<0:raise ValueError('Invalid citation count')
                if not isinstance(identifier,str) or not re.fullmatch(r'https://openalex.org/W\d+',identifier):raise ValueError('Invalid OpenAlex work identifier')
                entry.update({'status':'success','count':count,'source_url':identifier,'retrieved_at':stamp,'message':''});stats['matched']+=1
        except Exception as error:
            message=str(error) if isinstance(error,(ValueError,RuntimeError)) else 'Invalid response or request failure'
            entry.update({'status':'failed','message':message[:180]});stats['failed']+=1
        entries[doi]=entry
    return {'schema_version':1,'source':'OpenAlex','last_attempt':stamp,'entries':entries},{'last_attempt':stamp,'publications':len(publications),'unique_dois':len(dois),**stats}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=Path('.'));p.add_argument('--out',type=Path,default=Path('citation-audit'));p.add_argument('--apply',action='store_true');a=p.parse_args()
    papers=read(a.root/'data/publications.json',{})['publications']
    prior=read(a.root/'data/citation-metrics.json',{'entries':{}})
    data,report=audit(papers,prior)
    write(a.out/'citation-metrics.proposed.json',data);write(a.out/'citation-audit-status.json',report)
    if a.apply:
        if report['failed']:raise SystemExit('Refresh failures: proposed data saved for review, published file unchanged.')
        write(a.root/'data/citation-metrics.json',data)
    print(json.dumps(report,indent=2))
    return 2 if report['failed'] else 0
if __name__=='__main__':raise SystemExit(main())
