"""Apply the approved Physical Education portraits and dual-role profiles."""
import copy
import hashlib
import json
import posixpath
import re
import struct
from pathlib import Path

REVISION = '2026-11-03-physical-education-photos'
EXPECTED = {'faculty.json':'0202b5ccb8ea31c4d49c0cdf306ec0146d495806', 'research-students.json':'4a633047abb19c9b133fb6d2700fb242629b0a38'}
DEPARTMENT = 'physical-education'
MAPPINGS = [
('faculty','balakrishna-puttur','faculty/pe-balakrishna-k.png'),
('faculty','basavaraja-m-magalda','faculty/pe-basavaraja-magalda.png'),
('faculty','c-p-bopanna','faculty/pe-bopanna-cp.png'),
('faculty','deekshith-babu','faculty/pe-deekshith-b.png'),
('faculty','govindaraju-kammaragatte-anjaneya','faculty/pe-govindaraju-ka.png'),
('faculty','ravindra-gouda-s-m','faculty/pe-ravindra-gowda-sm.png'),
('faculty','vasanthanaik-papanaik','faculty/pe-vasantha-naik-p.png'),
('faculty','vasudha-s-s','students/pe-vasudha-ss.png'),
('students','basavaraja-m-magalda','students/pe-basavaraja-magalda.png'),
('students','c-p-bopanna','students/pe-bopanna-cp.png'),
('students','govindaraju-kammaragatte-anjaneya','students/pe-govindaraju-ka.png'),
('students','dileepkumar-s-c','students/pe-dileepkumar-sc.png'),
('students','pavithra-m','students/pe-pavithra-m.png'),
('students','vasudha-s-s','students/pe-vasudha-ss.png')]
NEW = [('faculty','basavaraja-m-magalda',None), ('students','c-p-bopanna',None), ('students','govindaraju-kammaragatte-anjaneya',None), ('students','dileepkumar-s-c','Dileepkumar S. C.'), ('students','pavithra-m','Pavithra M.')]
COPY_FIELDS = ['name','last_name','email','institutional_email','orcid','scholar_url','personal_website','linkedin_url','social_links','biography','research_interests','academic_journey','research_summary','modules_taught','additional_notes','qualifications']

def blob(raw):
    return hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()

def norm(name):
    name = re.sub(r'^(?:Prof|Dr|Mr|Mrs|Ms)\.?\s+', '', name, flags=re.I)
    return re.sub('[^a-z0-9]', '', name.casefold())

def apply(root, enforce_baseline=True):
    root = Path(root)
    report_path = root/'data/physical-education-photo-sync-status.json'
    manifest = hashlib.sha256(json.dumps([MAPPINGS,NEW],sort_keys=True).encode()).hexdigest()
    previous = json.loads(report_path.read_text()) if report_path.exists() else None
    if previous and (previous.get('revision') != REVISION or previous.get('manifest_sha256') != manifest):
        raise ValueError('Different Physical Education mapping batch; review required')
    if not previous and enforce_baseline:
        for name, expected in EXPECTED.items():
            if blob((root/'data'/name).read_bytes()) != expected:
                raise ValueError('Profile data changed after review: '+name)
    faculty = json.loads((root/'data/faculty.json').read_text())
    students = json.loads((root/'data/research-students.json').read_text())
    groups = {'faculty':faculty['faculty'], 'students':students['students']}
    index = {}
    for role, rows in groups.items():
        if len({r['id'] for r in rows}) != len(rows):
            raise ValueError('Duplicate IDs in '+role)
        index[role] = {r['id']:r for r in rows}
    created = []
    for role, identity, supplied_name in NEW:
        if identity in index[role]:
            continue
        if previous:
            raise ValueError('Previously created profile is missing: '+identity)
        other = 'students' if role == 'faculty' else 'faculty'
        peer = index[other].get(identity)
        if supplied_name is None and peer is None:
            raise ValueError('Missing existing peer profile: '+identity)
        if peer and peer.get('department_id') not in ['education',DEPARTMENT]:
            raise ValueError('Peer belongs to another department: '+identity)
        name = supplied_name or peer['name']
        if any(norm(r['name']) == norm(name) for r in groups[role]):
            raise ValueError('Name already exists under another ID: '+name)
        if supplied_name and any(norm(r['name']) == norm(name) for r in groups[other]):
            raise ValueError('New name has an existing identity requiring review: '+name)
        row = {k:copy.deepcopy(peer[k]) for k in COPY_FIELDS if peer and k in peer}
        row.update(id=identity,name=name,department_id=DEPARTMENT,department='Physical Education',profile_status='partial',profile_source='User-approved portrait and role mapping, 2026-11-03')
        row.setdefault('biography','Profile information will be added here.')
        row.setdefault('research_interests','Information to be added.')
        row.setdefault('academic_journey','Information to be added.')
        if role == 'faculty':
            row['designation'] = 'Position to be added.'
        else:
            row.update(published=True,programme='',publications=[])
            if peer and peer.get('phd_supervisor'):
                row['supervisor'] = peer['phd_supervisor']
        groups[role].append(row)
        index[role][identity] = row
        created.append({'role':role,'id':identity,'name':name,'url':('faculty' if role=='faculty' else 'students')+'/profile.html?id='+identity})
    mappings = []
    corrections = []
    images = {}
    for role, identity, filename in MAPPINGS:
        row = index[role].get(identity)
        if row is None or row.get('department_id') not in ['education',DEPARTMENT]:
            raise ValueError('Missing or mismatched profile: '+role+':'+identity)
        path = 'assets/img/'+filename
        raw = (root/path).read_bytes()
        if len(raw)<24 or raw[:8]!=b'\x89PNG\r\n\x1a\n' or raw[12:16]!=b'IHDR':
            raise ValueError('Invalid PNG header: '+path)
        width,height = struct.unpack('>II',raw[16:24])
        if not width or not height:
            raise ValueError('Invalid portrait dimensions: '+path)
        images[path] = {'path':path,'width':width,'height':height,'sha256':hashlib.sha256(raw).hexdigest()}
        field = 'photo' if role=='faculty' else 'photo_url'
        value = posixpath.relpath(path,'assets/img/faculty') if role=='faculty' else '../'+path
        if previous and (row.get(field)!=value or row.get('department_id')!=DEPARTMENT or role=='students' and row.get('published') is not True):
            raise ValueError('Approved profile mapping changed: '+role+':'+identity)
        if row.get('department_id') != DEPARTMENT:
            corrections.append({'role':role,'id':identity,'from':row.get('department_id'),'to':DEPARTMENT})
        mappings.append({'role':role,'id':identity,'name':row['name'],'field':field,'previous':row.get(field),'value':value,'url':('faculty' if role=='faculty' else 'students')+'/profile.html?id='+identity})
        row.update(department_id=DEPARTMENT,department='Physical Education')
        row[field] = value
        if role=='students':
            row['published'] = True
    if previous:
        return previous
    faculty['updated'] = students['updated'] = '2026-11-03'
    report = {'revision':REVISION,'manifest_sha256':manifest,'updated':'2026-11-03','mapped_records':len(mappings),'unique_images':len(images),'created_profiles':created,'department_corrections':corrections,'mappings':mappings,'images':list(images.values()),'faculty_total':len(groups['faculty']),'student_total':len(groups['students']),'notes':['Repeated people intentionally remain in both faculty and student categories.','Balakrishna K portrait assigned to existing Balakrishna Puttur profile using the user-approved tentative match; existing name preserved.','New roles do not establish a qualification or appointment; unknown fields remain placeholders.','Source form submissions and research metrics are not modified. Future source re-imports must retain the confirmed department and dual-role corrections.']}
    pending = {'data/faculty.json':faculty,'data/research-students.json':students,'data/physical-education-photo-sync-status.json':report}
    for filename,value in pending.items():
        (root/filename).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return report

if __name__=='__main__':
    report = apply(Path(__file__).resolve().parents[1])
    print(json.dumps({k:report[k] for k in ['mapped_records','unique_images','created_profiles','department_corrections']},indent=2))
