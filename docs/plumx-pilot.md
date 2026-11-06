# PlumX pilot: deferred activation

Prepared for KU-Website, 6 November 2026.

## Scope

- Isolated page: `plumx-pilot.html`. Not added to navigation or existing department/profile pages.
- Reuses `assets/js/publications.js` and its existing Environmental Science collection. No new extraction, API credentials, workflow, citation-cache changes or ranking changes.
- At most five distinct DOI-bearing publication cards receive widgets after explicit visitor interaction, and only after the approval gate is enabled.
- Uses the documented PlumX custom element, badge display, `hideWhenEmpty`, `hideCitations`, and `applyFiltersToMetricsPage`. Empty/error responses do not become zero.

## Activation gate

The body attribute `data-plumx-approved="false"` disables the pilot. The disabled page does not load the PlumX script or make PlumX metric requests. This gate has no query-string override.
Publishing the preview is not a claim of Elsevier approval.

Confirm university-site widget eligibility and applicable terms with Elsevier before proposing a separate reviewed commit to change the attribute to `true`. User approval of a repository change is not vendor approval.

After activation, visitors must click the load button. Their browsers then contact PlumX for live information. This information is not an archived, locally reviewed metric snapshot and must not be presented as one.

## Verification before wider rollout

1. With the gate false, verify no PlumX network requests and no enabled load button.
2. Confirm the shared publication collection and existing citation lines still render.
3. After eligibility is confirmed and activation separately approved, verify no PlumX requests before the visitor clicks.
4. Verify a maximum of five distinct DOIs, citation-category filtering, empty/error handling, and unchanged citation snapshots.
5. Check keyboard access, mobile layout, provider blocking, and actual coverage. Widget availability is not guaranteed.
6. Do not expand to department/profile pages until the pilot is reviewed. The future local R pipeline remains deferred.

No browser rendering or live metric coverage is claimed verified by this preparation commit.

## Provider documentation

- https://plumx.elsevier.com/plum/developers/widgets
- https://www.elsevier.com/en-in/insights/metrics/plumx/integrate
