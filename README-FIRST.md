# KU website checkpoint — 19 October 2026

## Scope and limitations
Built from HTML/CSS/JS supplied in the conversation. This is a checkpoint for the supplied pages, not a download of the entire repository. Unprovided pages/assets must remain in your repository. Header/footer shared visually but repeated in HTML; no framework migration.

## Upload using GitHub Desktop
1. First make sure current work is committed. Record the current commit as your rollback point.
2. Extract this ZIP. Copy the CONTENTS of ku-site into your existing repository folder. Merge folders and replace matching files; do not replace/delete the whole repository folder. Never remove .git or existing unprovided assets.
3. In GitHub Desktop inspect Changes. Expected replacements: index.html, events.html, departments/applied-botany.html, event.html, assets/css/style.css, assets/js/site.js, assets/js/events.js and data/events.json. New Environmental Science page, PNGs and documentation are included.
4. Commit with a descriptive message, then Push origin. Retain Pages main / root configuration.
5. Check the homepage, events page, both department pages and an old demonstration event link on desktop and mobile. Third-party iframes need network access.
6. If the release fails, use History in GitHub Desktop to revert this release commit and push the revert. Do not overwrite .git.

## Design
Homepage section order, SVG artwork, hero grid and existing base layout rules retained. Event section now uses a compact Teamup list; full events page uses the supplied embed settings. The Teamup URL is public read-only as described by the owner; actual permissions, timezone and calendar contents have not been independently verified. The calendar default timezone should be set to India time in Teamup. Public embeds may retain third-party branding or controls according to the plan.

Environmental Science uses supplied content in the existing typography, palette and department layout. Photos are clearly labelled PNG placeholders. The two homepage photo preparation files are not linked: SVG illustrations remain. No open-admissions claim, invented faculty, invented publications or unverified manuscript co-authorship claim is published.

## Event transition
Applied Botany remains a separate legacy demonstration page. Its fictional feed and event.html remain functional using data/events.json and a defensive legacy events.js. Fictional prose has been simplified while IDs/dates/department assignments/statuses remain. These files do not feed the Teamup embeds. events.html is now a university-wide Teamup calendar: old ?department= links do NOT filter it. Environmental Science explicitly labels its calendar university-wide until a department-specific read-only URL is supplied. No API keys or editor links are included.

## Future features — NOT active
Forms/review-sheet publishing; real faculty/student directory; ORCID import; weekly publication refresh; JIF sorting; live announcements; Kannada translation. Empty department sections are explicitly labelled as awaiting content, not populated with fictional records. No update automation is claimed.

## Validation
See VALIDATION.md. Structural checks are not visual browser testing. Do not call the layout visually verified until reviewed in a browser at desktop/mobile widths.
