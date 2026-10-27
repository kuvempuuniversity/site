# Research student profiles

The shared profile is students/profile.html?id=student-id. The Environmental Science directory is departments/environmental-science.html#students.

Add records to data/research-students.json inside the students array. No real or fictional student records are included initially.

Fields:
- id: unique lowercase hyphenated identifier, e.g. firstname-lastname.
- published: true only after the student details and permission to publish have been confirmed; false records are not rendered. Do not commit private drafts to a public repository: this flag is not access control.
- name: public display name.
- department_id: environmental-science (or applied-botany for the reusable profile template; its directory integration is not included in this stage).
- programme: supplied programme/status, e.g. PhD Research Scholar.
- supervisor, co_supervisor: supplied public names.
- registration_year: optional year.
- biography: brief introduction.
- research_topic, research_interests, academic_journey, research_summary: optional plain text.
- photo_url: optional approved photo URL, or ../assets/img/students/filename.jpg. Supply a photo before adding the path; no placeholder person is invented.
- email: optional public contact address, only with permission.
- orcid: optional ORCID number.
- scholar_url, personal_website, linkedin_url: optional links.
- publications: optional array of objects with title, link, year, authors and venue.

Empty descriptive fields and absent links are hidden. Missing publications show a neutral pending message, not a zero-output claim. Publication entries are supplied explicitly in this stage. The faculty ORCID/OpenAlex automation is not changed or automatically extended to students.

The student page reuses faculty-profile.css for its responsive portrait/details layout. Directory cards open the shared profile using the record id. Unpublished or unknown ids show a not-available page without exposing the record.

Before publishing a record, check the unique id, name, department, supervisor, photo and contact permissions, link destinations and publication authorship. Verify the department card and individual profile after deployment.
