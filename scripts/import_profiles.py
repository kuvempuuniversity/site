"""Merge the approved form source into the existing website datasets."""
import ast
import hashlib
import html
import json
from pathlib import Path
import re
import unicodedata
from urllib.parse import urlparse, parse_qs

SOURCE_BLOB = 'f8c0fe9d84cd79159bc1fd16d80a88cc4947f4f5'
ROUTES = {'computer-science': 'computer-sciences', 'tourism-administration': 'tourism'}
PHOTO_ALIASES = {
'reenaroyprasad@gmail.com':'ab-reena-roy-d', 'shankarsaralap@gmail.com':'ab-sarala-p',
'sathishbryol@gmail.com':'ab-sathisha-am', 'drshrishailc@gmail.com':'ab-shrishaila',
'mrvikasrajvr@gmail.com':'ab-vikas-r', 'rajscbz@gmail.com':'ab-shashiraj-kn',
'narasimhanarasimhatb@gmail.com':'ab-narasimha-tb', 'venkateshjugal079@gmail.com':'ab-venkatesh',
'ignitedclawz001@gmail.com':'ab-jasmine-a', 'rashmichandrashekar16@gmail.com':'ab-rashmi-dc',
'shashi083@gmail.com':'bt-shashikumar-r', 'divakarabdvt@gmail.com':'bt-divakara-r', 'sanbioinfo@gmail.com':'bt-sandeep-telkar',
'skdde.ku11@gmail.com':'bt-shankaramurthy-k', 'ravibioinfotech@gmail.com':'bt-ravikumar-s',
'mcmaruthimc@gmail.com':'kn-maruthi-manjappa-chelavadhi', 'nellikattesiddesh@gmail.com':'kn-nellikatte-siddesh',
'dr.m.ravinaik@gmail.com':'kn-ravi-naik-m', 'preethiyabaduku@gmail.com':'kn-prashantha-nayaka',
'puruhitlu@gmail.com':'kn-purushotama-sv', 'raghuskkannada24@gmail.com':'kn-raghu-sk',
'sridharsrinivas2018@gmail.com':'kn-shridhara-s', 'rangaswamyhg9@gmail.com':'kn-rangaswamy-hg',
'tobalesha@gmail.com':'kn-obalesha-t', 'manjumt94@gmail.com':'kn-manjunatha-t',
'ashikkoppa1912@gmail.com':'kn-ashik', 'kavanak9353@gmail.com':'kn-kavana-k',
'gaganaj991@gmail.com':'kn-gagana-j', 'nagaraja.ngkvb1@gmail.com':'kn-nagaraja-g',
'shilpakalarguna@gmail.com':'kn-shilpakala-mathod', 'abhijithb736@gmail.com':'kn-abhijith-b',
'harishmn2002@gmail.com':'kn-harish-mn', 'msudeep056@gmail.com':'kn-sudeepa-m',
'suprajarprasad@gmail.com':'ic-supraja-r-prasad', 'mhbhavani1998@gmail.com':'ic-bhavani-mh',
'anushahyanushahy31@gmail.com':'ic-anusha-hy'}
WITHHELD_ORCIDS = {'venkateshjugal079@gmail.com', 'megha2rao@gmail.com'}

def norm(value):
    return re.sub(r'[^a-z0-9]', '', str(value or '').lower())

def slug(value):
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode()
    return re.sub(r'[^a-z0-9]+', '-', value.lower()).strip('-')

def read(root, path):
    return json.loads((root / path).read_text(encoding='utf-8'))

def useful(value):
    return isinstance(value, str) and bool(value.strip()) and not re.fullmatch(
        r'(?i)(?:tba|n/?a|none|nil+l?|nothing|no|yes|[-.]+|will.*|wil be later|fill.*|to be.*|previo\w* updated|added through qr|through qr)', value.strip())

def scholar(value):
    if not useful(value):
        return ''
    u = urlparse(value if '://' in value else 'https://' + value)
    author = parse_qs(u.query).get('user', [''])[0]
    if u.hostname not in ('scholar.google.com', 'scholar.google.co.in') or not re.fullmatch(r'[A-Za-z0-9_-]{6,}', author):
        return ''
    return 'https://scholar.google.com/citations?user=' + author + '&hl=en'

def scholar_id(value):
    return parse_qs(urlparse(value or '').query).get('user', [''])[0]

def linkedin(value):
    if not useful(value):
        return ''
    value = value if '://' in value else 'https://' + value
    u = urlparse(value)
    return value if u.scheme in ('https', 'http') and u.hostname in ('linkedin.com', 'www.linkedin.com') and u.path.startswith('/in/') and not u.username and not u.password else ''

def build(root, expected=(140,109,64,33), source_blob=SOURCE_BLOB):
    root = Path(root)
    raw = (root / 'data/source.json').read_bytes()
    digest = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
    if source_blob and digest != source_blob:
        raise ValueError('source.json changed after review; stop for fresh approval')
    source = json.loads(raw)
    people = source['people']
    counts = (len(people), sum(p['faculty'] for p in people), sum(p['student'] for p in people), sum(p['faculty'] and p['student'] for p in people))
    if counts != expected or len({p['email'].strip().lower() for p in people}) != len(people):
        raise ValueError('Unexpected source totals or duplicate primary emails')
    faculty_data = read(root, 'data/faculty.json')
    student_data = read(root, 'data/research-students.json')
    journeys = read(root, 'data/academic-journeys.json')
    groups = {'faculty': faculty_data['faculty'], 'students': student_data['students']}
    redirects = read(root, 'data/profile-redirects.json') if (root / 'data/profile-redirects.json').exists() else {}
    migrated = 0
    legacy = root / 'assets/js/portrait-profiles.js'
    if legacy.exists():
        code = legacy.read_text(encoding='utf-8')
        names = {'ic': ('industrial-chemistry','Industrial Chemistry'), 'jrnl': ('journalism-and-mass-communication','Journalism and Mass Communication'), 'kn': ('kannada','Kannada')}
        for role in groups:
            match = re.search(r'const ' + role + r'=(\{[^\n]+\});', code)
            if not match:
                raise ValueError('Unrecognised legacy portrait manifest')
            manifest = ast.literal_eval(re.sub(r'\b([a-z]+):', r"'\1':", match.group(1)))
            for prefix, entries in manifest.items():
                for stem, name in entries:
                    identity = prefix + '-' + stem
                    if any(r['id'] == identity for r in groups[role]):
                        continue
                    item = {'id':identity,'name':name,'department_id':names[prefix][0],'department':names[prefix][1], 'biography':'Profile information will be added here.', 'research_interests':'Information to be added.'}
                    if role == 'faculty':
                        item.update(designation='Position to be added.', photo=identity+'.png')
                    else:
                        item.update(published=True, programme='', photo_url='../assets/img/students/'+identity+'.png', publications=[])
                    groups[role].append(item)
                    migrated += 1
    report = []
    def find(person, role):
        records = groups[role]
        emails = {person['email'].lower(), *[e.lower() for e in person.get('email_aliases', [])]}
        found = [r for r in records if str(r.get('email','')).lower() in emails]
        if not found and person.get('orcid'):
            found = [r for r in records if r.get('orcid') == person['orcid']]
        photo = PHOTO_ALIASES.get(person['email'])
        if not found and photo:
            found = [r for r in records if r['id'] == photo or Path(r.get('photo') or r.get('photo_url') or '').stem == photo]
        if not found:
            found = [r for r in records if norm(re.sub(r'^(Prof\.?|Dr\.?|Mr\.?|Mrs\.?|Ms\.?)\s+', '', r['name'], flags=re.I)) == norm(person['name']) and r['department_id'] == ROUTES.get(person['department_id'], person['department_id'])]
        if len(found) > 1:
            raise ValueError('Ambiguous match for ' + person['email'] + ' in ' + role)
        return found[0] if found else None
    for person in people:
        if not person['faculty'] and not person['student']:
            raise ValueError('Person has neither category')
        original = {role:find(person, role) for role in groups}
        chosen = {}
        department_id = ROUTES.get(person['department_id'], person['department_id'])
        if not re.fullmatch(r'[a-z0-9-]+', department_id):
            raise ValueError('Invalid department identifier')
        for role, flag in [('faculty','faculty'), ('students','student')]:
            if not person[flag]:
                continue
            item = original[role]
            is_new = item is None
            if item is None:
                peer = original['students' if role == 'faculty' else 'faculty']
                identity = peer['id'] if peer else PHOTO_ALIASES.get(person['email']) or slug(person['name'])
                identity = identity or slug(person['email'].split('@')[0])
                if any(r['id'] == identity for r in groups[role]):
                    raise ValueError('ID collision: ' + identity)
                item = {'id':identity}
                groups[role].append(item)
            chosen[role] = item['id']
            name = person['name'].strip()
            title = person.get('title','').strip()
            item.update(name=(title+' '+name).strip() if title and not name.lower().startswith(title.lower()) else name,
                        last_name=person.get('last_name') or name.split()[-1], department_id=department_id,
                        department=person['department'], email=person['email'], teaches=bool(person['teaches']))
            for field in ['biography','research_interests','academic_journey','research_summary']:
                if useful(person.get(field)):
                    item[field] = person[field].strip()
            if person.get('modules_taught'):
                item['modules_taught'] = [v.strip() for v in person['modules_taught'] if useful(v)]
            if useful(person.get('supervisor')):
                item['phd_supervisor' if role == 'faculty' else 'supervisor'] = person['supervisor']
            if person.get('email_aliases'):
                item['email_aliases'] = person['email_aliases']
            if person.get('additional_roles'):
                item['additional_roles'] = list(dict.fromkeys(item.get('additional_roles', []) + person['additional_roles']))
            if person['email'] in WITHHELD_ORCIDS:
                item['orcid'] = ''
            elif re.fullmatch(r'\d{4}-\d{4}-\d{4}-\d{3}[\dX]', person.get('orcid','')):
                item['orcid'] = person['orcid']
            candidate = scholar(person.get('scholar_url'))
            if candidate and (not item.get('scholar_url') or scholar_id(candidate) != scholar_id(item.get('scholar_url'))):
                item['scholar_url'] = candidate
            candidate = linkedin(person.get('linkedin_url'))
            if candidate:
                item['linkedin_url'] = candidate
            if person.get('social_links'):
                item['social_links'] = {**item.get('social_links', {}), **person['social_links']}
            stem = PHOTO_ALIASES.get(person['email'])
            photo = None
            if stem:
                for folder in [role, 'students' if role == 'faculty' else 'faculty']:
                    for ext in ['png','jpg','jpeg','webp']:
                        path = root / ('assets/img/'+folder+'/'+stem+'.'+ext)
                        if path.exists():
                            photo = path.relative_to(root).as_posix()
                            break
                    if photo:
                        break
            if role == 'faculty':
                item['designation'] = person['position'] + (' (teaching)' if person['position'] in ['PhD candidate','Research Fellow'] and person['teaches'] else '')
                if photo:
                    item['photo'] = Path(photo).name if '/faculty/' in photo else '../students/'+Path(photo).name
                if useful(person.get('academic_journey')):
                    journeys[item['id']] = person['academic_journey']
            else:
                item.update(published=True, programme='PhD candidate' + (' (Research Fellow)' if person['position'] == 'Research Fellow' else ''))
                item.setdefault('publications', [])
                if photo:
                    item['photo_url'] = '../'+photo
            report.append({'email':person['email'],'role':role,'id':item['id'],'action':'added' if is_new else 'updated'})
        for role, flag in [('faculty','faculty'),('students','student')]:
            old = original[role]
            if old and not person[flag]:
                groups[role].remove(old)
                other = 'students' if role == 'faculty' else 'faculty'
                redirects[role+':'+old['id']] = {'role':other,'id':chosen[other]}
    for role, records in groups.items():
        if len({r['id'] for r in records}) != len(records):
            raise ValueError('Duplicate IDs in '+role)
        records.sort(key=lambda r:(r['department_id'],str(r.get('last_name') or r['name'].split()[-1]).casefold(),r['name'].casefold()))
    names = {r['department_id']:r.get('department') or r['department_id'].replace('-',' ').title() for role in groups.values() for r in role}
    names.update({ROUTES.get(p['department_id'],p['department_id']):p['department'] for p in people})
    pending = {}
    def write_json(path, value):
        pending[path] = json.dumps(value,ensure_ascii=False,indent=2)+'\n'
    faculty_data['updated'] = '2026-10-31'
    student_data['updated'] = '2026-10-31'
    write_json('data/faculty.json',faculty_data)
    write_json('data/research-students.json',student_data)
    write_json('data/academic-journeys.json',journeys)
    write_json('data/profile-redirects.json',redirects)
    write_json('data/profile-import-status.json',{'source_blob':digest,'source_people':counts[0],'source_faculty':counts[1],'source_students':counts[2],'source_both':counts[3],'faculty_total':len(groups['faculty']),'student_total':len(groups['students']),'migrated_portrait_entries':migrated,'records':report})
    student_script = (root/'assets/js/research-students.js').read_text(encoding='utf-8')
    student_script, n = re.subn(r'const directoryMatch=location\.pathname\.match\([^\n]+\);',r"const directoryMatch=location.pathname.match(/\\/departments\\/([a-z0-9-]+)\\.html$/);",student_script,count=1)
    if n != 1:
        raise ValueError('Student directory loader pattern changed')
    student_script, n = re.subn(r'const departments=\{[^\n]+\};',lambda m:'const departments='+json.dumps(names,ensure_ascii=False)+';',student_script,count=1)
    if n != 1:
        raise ValueError('Student department map pattern changed')
    pending['assets/js/research-students.js'] = student_script
    for path in (root/'departments').glob('*.html'):
        text = path.read_text(encoding='utf-8')
        text = re.sub(r'<script\b[^>]*src=["\'][^"\']*(?:portrait-profiles|portrait-profile-guard)\.js["\'][^>]*></script>','',text)
        if 'department-profile-loader.js' not in text:
            text = text.replace('</head>','<script defer src="../assets/js/department-profile-loader.js"></script></head>')
        pending[path.relative_to(root).as_posix()] = text
    for person in people:
        department_id = ROUTES.get(person['department_id'],person['department_id'])
        path = 'departments/'+department_id+'.html'
        if (root/path).exists() or path in pending:
            continue
        name = html.escape(person['department'],quote=True)
        pending[path] = '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>'+name+' — Kuvempu University</title><link rel="stylesheet" href="../assets/css/style.css"><script defer src="../assets/js/site.js"></script><script defer src="../assets/js/department-profile-loader.js"></script></head><body data-base="../" data-department-page="'+department_id+'" data-department-name="'+name+'"><main id="main"><h1>'+name+'</h1><p id="department-description">Department information will be added here.</p></main><noscript>Enable JavaScript to view department profiles.</noscript></body></html>\n'
    for path in ['faculty/profile.html','students/profile.html']:
        text = (root/path).read_text(encoding='utf-8')
        text = re.sub(r'<script\b[^>]*src=["\'][^"\']*(?:portrait-profiles|portrait-profile-guard)\.js["\'][^>]*></script>','',text)
        if 'department-profile-loader.js' not in text:
            text = text.replace('</head>','<script defer src="../assets/js/department-profile-loader.js"></script></head>')
        pending[path] = text
    catalogue_path = 'assets/js/department-catalogue.js'
    catalogue = (root/catalogue_path).read_text(encoding='utf-8')
    if "['Sociology','sociology','arts']" not in catalogue:
        if 'const entries=[' not in catalogue:
            raise ValueError('Department catalogue pattern changed')
        catalogue = catalogue.replace('const entries=[',"const entries=[['Sociology','sociology','arts'],",1)
    pending[catalogue_path] = catalogue
    for path, content in pending.items():
        dest = root/path
        dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_text(content,encoding='utf-8')
    return {'counts':counts,'faculty_total':len(groups['faculty']),'student_total':len(groups['students']),'files':len(pending)}

if __name__ == '__main__':
    print(json.dumps(build(Path(__file__).resolve().parents[1]),indent=2))
