KUVEMPU WEBSITE — ORIGINAL HOMEPAGE + EVENTS

INSTALL
1. Back up your current repository folder outside the repository.
2. Extract this ZIP. Copy its CONTENTS directly into your existing site repository.
3. Replace index.html. Merge the assets folder (do not delete existing unrelated files).
4. Commit all changes and Push origin in GitHub Desktop.
5. Keep Pages publishing from main / (root).

Homepage: original design, content sections, illustrations and subject explorer retained; shared styles and scripts extracted into assets. Added Events navigation, featured events section, Applied Botany link and shared page navigation. Pasted non-breaking-space markup and Markdown-style hrefs corrected.

PAGES
index.html
events.html
event.html?id=demo-botany-seminar
departments/applied-botany.html

EVENTS
Edit data/events.json centrally. No CMS or backend is included. The file is public: keep drafts, personal data, credentials, and private joining information out of it.
All sample records are fictional and explicitly labelled. No registration functionality exists.
Unique ids are required. Department slugs are applied-botany, environmental-science and english. The department page displays applied-botany records. Joint events may have multiple departments.
ISO timestamps include +05:30. All display times use Asia/Kolkata. Upcoming/past derives from the event end time when the page loads. Refresh to update a page left open.
featured=true controls the homepage; cancelled and postponed records are excluded from homepage selection, but retained in the directory with visible status.
Adding new department names to the dropdown and labels currently requires editing events.html and assets/js/events.js.
Use GitHub Pages to test: file:// loading of JSON may be blocked. No external assets or libraries are required.

VALIDATION
Local links, anchor targets, JSON and required file presence checked during generation. Browser appearance, interactions and accessibility require testing.
