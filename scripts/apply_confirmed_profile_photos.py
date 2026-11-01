"""Apply the user-confirmed 1 November portrait mappings and partial profiles."""
import hashlib
import json
import posixpath
import re
import struct
from pathlib import Path

REVISION='2026-11-01-confirmed-portraits'
EXPECTED={'faculty.json':'17e44d48eb00cc0c01c2064d99b29343b047dfe8','research-students.json':'77aed4bd07ef49518666f972eca517dc772e2ffb'}
NEW=[('faculty','dattatreya-m','Dattatreya M.','english','English'),('faculty','manjunatha-g-p','Manjunatha G. P.','english','English'),('faculty','premkumar-g','Premkumar G.','english','English'),('students','ramya-k','Ramya K.','electronics','Electronics'),('students','salma-n','Salma N.','electronics','Electronics')]
PHOTOS=[
('applied-geology','faculty/ag-govindaraju.png',['faculty:govindaraju']),
('chemistry','faculty/chm-talavara-venkatesh.png',['faculty:talavara-venkatesh']),
('english','faculty/en-aditya-j.png',['faculty:aditya-j','students:aditya-j']),
('english','faculty/en-dattatreya-m.png',['faculty:dattatreya-m']),
('english','faculty/en-doreobanna-e.png',['students:doreobanna-b']),
('english','faculty/en-jayadrata.png',['students:jaydrata']),
('english','faculty/en-manjunatha-gp.png',['faculty:manjunatha-g-p']),
('english','faculty/en-premkumar-g.png',['faculty:premkumar-g']),
('english','faculty/en-ramprasad-bv.png',['faculty:rama-prasad-b-v']),
('english','faculty/en-tabassum.png',['faculty:tabassum']),
('environmental-science','faculty/es-hina-kausar.png',['faculty:hina-kousar']),
('journalism-and-mass-communication','faculty/jrnl-sathish-kumar.png',['faculty:sathish-kumar']),
('journalism-and-mass-communication','faculty/jrnl-varghese-pa.png',['faculty:varghese-p-a-pulickal']),
('applied-botany','students/ab-apoorva-p.png',['faculty:apoorva-p','students:apoorva-p']),
('chemistry','students/chm-chandana-hp.png',['faculty:chandana-h-p','students:chandana-h-p']),
('chemistry','students/chm-kavana-s.png',['faculty:kavana-s','students:kavana-s']),
('chemistry','students/chm-sneha-ma.png',['faculty:sneha-m-a-anthony','students:sneha-m-a-anthony']),
('electronics','students/elec-ramya-k.png',['students:ramya-k']),
('electronics','students/elec-salma-n.png',['students:salma-n'])]

def blob(raw):
    return hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()

def norm(value):
    return re.sub('[^a-z0-9]','',str(value).casefold())

def apply(root,enforce_baseline=True):
    root=Path(root)
    report_path=root/'data/photo-profile-sync-status.json'
    manifest=hashlib.sha256(json.dumps([NEW,PHOTOS],sort_keys=True).encode()).hexdigest()
    previous=json.loads(report_path.read_text(encoding='utf-8')) if report_path.exists() else None
    if previous and (previous.get('revision')!=REVISION or previous.get('manifest_sha256')!=manifest):
        raise ValueError('A different photo-mapping batch exists; review before applying')
    if not previous and enforce_baseline:
        for filename,expected in EXPECTED.items():
            if blob((root/'data'/filename).read_bytes())!=expected:
                raise ValueError('Profile data changed after review: '+filename)
    faculty=json.loads((root/'data/faculty.json').read_text(encoding='utf-8'))
    students=json.loads((root/'data/research-students.json').read_text(encoding='utf-8'))
    groups={'faculty':faculty['faculty'],'students':students['students']}
    for role,rows in groups.items():
        if len({r['id'] for r in rows})!=len(rows):raise ValueError('Duplicate profile IDs in '+role)
    created=[]
    for role,identity,name,department,label in NEW:
        found=[r for r in groups[role] if r['id']==identity]
        if found:
            if found[0].get('department_id')!=department:raise ValueError('Profile ID belongs to another department: '+identity)
            continue
        if previous:raise ValueError('A previously created profile is missing: '+identity)
        if any(r.get('department_id')==department and norm(r.get('name',''))==norm(name) for r in groups[role]):
            raise ValueError('Name already exists under another ID: '+name)
        row={'id':identity,'name':name,'department_id':department,'department':label,'biography':'Profile information will be added here.','research_interests':'Information to be added.','academic_journey':'Information to be added.','profile_status':'partial','profile_source':'User-approved name and portrait mapping, 2026-11-01'}
        if role=='faculty':row['designation']='Position to be added.'
        else:row.update(published=True,programme='',publications=[])
        groups[role].append(row);created.append({'role':role,'id':identity,'name':name,'department_id':department})
    mappings=[];images=[]
    for department,filename,targets in PHOTOS:
        path='assets/img/'+filename;raw=(root/path).read_bytes()
        if len(raw)<24 or raw[:8]!=b'\x89PNG\r\n\x1a\n' or raw[12:16]!=b'IHDR':raise ValueError('Invalid PNG header: '+path)
        width,height=struct.unpack('>II',raw[16:24])
        if not width or not height:raise ValueError('Invalid image dimensions: '+path)
        images.append({'path':path,'width':width,'height':height,'sha256':hashlib.sha256(raw).hexdigest()})
        for target in targets:
            role,identity=target.split(':',1)
            found=[r for r in groups[role] if r['id']==identity]
            if len(found)!=1 or found[0].get('department_id')!=department:raise ValueError('Missing or mismatched target: '+target)
            row=found[0];field='photo' if role=='faculty' else 'photo_url'
            value=posixpath.relpath(path,'assets/img/faculty') if role=='faculty' else '../'+path
            if previous and row.get(field)!=value:raise ValueError('Photo mapping changed after approval: '+target)
            old=row.get(field);row[field]=value
            mappings.append({'role':role,'id':identity,'name':row['name'],'field':field,'previous':old,'value':value})
    student_path=root/'assets/js/research-students.js'
    code=student_path.read_text(encoding='utf-8')
    matches=list(re.finditer(r'const departments=(\{[^\n]+\});',code))
    if len(matches)!=1:raise ValueError('Student department map changed; stop for review')
    names=json.loads(matches[0].group(1));names['electronics']='Electronics'
    updated=code[:matches[0].start()]+'const departments='+json.dumps(names,ensure_ascii=False)+';'+code[matches[0].end():]
    if previous:
        if updated!=code:raise ValueError('Electronics support was changed after approval')
        return previous
    faculty['updated']=students['updated']='2026-11-01'
    report={'revision':REVISION,'manifest_sha256':manifest,'updated':'2026-11-01','created_profiles':created,'mapped_records':len(mappings),'unique_images':len(images),'faculty_total':len(groups['faculty']),'student_total':len(groups['students']),'mappings':mappings,'images':images,'notes':'User-confirmed aliases; existing profile details and roles preserved. New profiles are partial; no positions, qualifications, research or contact details inferred. Original image files retained.'}
    pending={'data/faculty.json':faculty,'data/research-students.json':students,'data/photo-profile-sync-status.json':report}
    for filename,value in pending.items():(root/filename).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    student_path.write_text(updated,encoding='utf-8')
    return report

if __name__=='__main__':
    result=apply(Path(__file__).resolve().parents[1])
    print(json.dumps({k:result[k] for k in ['mapped_records','unique_images','faculty_total','student_total']}))
