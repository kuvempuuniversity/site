KUVEMPU — RESTORED ORIGINAL COMPOSITION, COMPLETE SITE

This is a full replacement release, not a patch.

INSTALL
1. Copy your current site folder to a backup OUTSIDE the repository, or commit the existing working state.
2. In the working site repository, remove the old website files and folders (index.html, events.html, event.html, assets/, data/, departments/, and obsolete installation/photo manifests). Do NOT delete the repository folder, the hidden .git directory, or unrelated repository configuration. Preserve any CNAME or .github configuration you use.
3. Extract this ZIP and copy its CONTENTS into the repository root, not into a nested folder.
4. Commit: Restore original homepage composition with two campus photos
5. Push origin. Pages remains main / (root).

RESTORED BASELINE
Split hero proportions 1.1fr / 1fr; original main section order; student shortcuts; subject explorer; application steps; two-column campus-life section; research/careers tiles; agreed events feed; notices/support; text-only university introduction; footer.
Exactly two homepage photographs replace illustration areas. No classroom insert, extra galleries, carousel, or photo override stylesheet.
Mobile stacks the same sections. Photo framing is cropped to existing slots, not the other way around.

COMPLETE CONTENTS
index.html, events.html, event.html, departments/applied-botany.html
assets/css/style.css
assets/js/site.js, assets/js/events.js
assets/img/campus/ (responsive WebP images)
data/events.json
.nojekyll

UPDATES
Public events: data/events.json. All supplied records are fictional. Do not add private drafts, secrets or personal data. Department feed displays up to 3 matching events; homepage displays up to 3 featured upcoming scheduled events. Past/upcoming uses end time at page load, Asia/Kolkata display. Refresh open pages to recalculate.
For future photo replacements use the existing source paths and responsive sizes, or update the img references consistently. Headers and footers remain repeated in static HTML; a template migration is not included in this repair.

LIMITATIONS
This is an independent prototype, not an official admissions or registration service. Academic content is unverified. Event detail and feeds require JavaScript and HTTP hosting (GitHub Pages); file:// testing may block JSON loading. University photo permissions require confirmation. No photo is presented as a department-specific or fictional-event image.

CHECKS
Internal file paths and fragment links, unique page IDs, image decoding/dimensions, JavaScript syntax where a local Node runtime is available, JSON and archive integrity are checked. Browser rendering and accessibility audit are not claimed.
