# ORCID publications: staged implementation

## Stage 1: read-only audit (this change)

The importer reads IDs from `data/faculty.json` and preserves the existing
`data/publications.json` during dry runs. No live publication counts have
been independently verified yet. The initial workflow has contents:read,
no schedule, no repository writes and no deployment. It runs after changes
to the importer/tests/workflow on main, or via Run workflow in GitHub Actions.
It produces an artifact containing proposed publications and faculty status.
A partial retrieval produces an artifact but marks the job failed.

Run locally:

```
python -m unittest discover -s tests -v
python scripts/sync_orcid_publications.py --out orcid-audit
```

No package installation or researcher passwords are needed. Anonymous public
requests are attempted first. An optional existing public-read access token
can be supplied as ORCID_ACCESS_TOKEN using a GitHub repository secret.
The script does not provision credentials. Check ORCID terms before institutional
production use. Never commit access tokens or include them in browser scripts.

## Behaviour

Read every public summary and its work detail; admit only the publication types
listed in TYPES. All publication years are eligible. Data sets, software and other
non-publication types are excluded. Counts distinguish retrieved representations
from eligible representations; proposed publication_count is deduplicated.

Match self DOIs first, never a parent journal/book DOI. Without a DOI, require
an exact normalised long title, a year and journal match, and compatible types.
Possible ambiguous matches remain separate with review warnings. Preserve
Unicode titles. Do not claim title matching proves identity.

Records retain per-faculty ORCID/put-code provenance and legacy source evidence.
Failed faculty imports retain their previous records and last-success timestamp.
A successful snapshot replaces that faculty's ORCID metadata. Missing work IDs
are checked by a second full read. Empty/50%-plus reductions require manual
review and --confirm-removals; review promptly for visibility withdrawals.
Independently sourced legacy records are not deleted solely because absent
from ORCID. No citation counts or impact metrics are fetched.

The script never modifies ORCID. It reads public data only. It generates
proposed records and per-faculty status with UTC timestamps, not raw API bodies.

## Stage 2: publication display and deployment (not enabled here)

After checking the audit, integrate source-aware rendering in both publication
views, including per-faculty failures/staleness, undated sorting, DOI links and
no-public-works versus failed/not-imported states. Replace the legacy hardcoded
Scholar wording without relabelling legacy records. Apply validated data with:

```
python scripts/sync_orcid_publications.py --out orcid-audit --apply
```

--apply writes validated local dataset/status files; it does not commit or deploy.
Each file uses atomic replacement. The two files are not a filesystem transaction;
publish them together in one repository commit. Record the complete deployment
method before enabling a weekly workflow. No Pages configuration was discovered
in the visible repository root; account-side Pages settings remain unverified.
A GITHUB_TOKEN commit alone must not be assumed to trigger Pages. Use an explicit
approved deployment step compatible with actual hosting. Keep the workflow
schedule off until the first live import and display have been verified.

## Review and maintenance

Compare returned counts and sample entries for all five faculty. ORCID is not
a complete author bibliography unless staff maintain their records. Inspect
duplicate warnings and large drops before release. Periodically review scheduled
workflow health (GitHub may disable inactive scheduled workflows). Maintain a
manual Run workflow option and monitor per-faculty last-success timestamps.

Official references:
- https://info.orcid.org/documentation/integration-guide/orcid-record/
- https://info.orcid.org/documentation/api-tutorials/api-tutorial-read-data-on-a-record/
- https://info.orcid.org/public-client-terms-of-service/
- https://docs.github.com/en/actions/concepts/security/github_token
