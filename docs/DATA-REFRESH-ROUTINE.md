# Research data refresh routine

Every refresh follows the same four stages. Each stage is a separate manual action, and nothing overwrites live data without a review step.

| Stage | Action | Output | Live data changed? |
|---|---|---|---|
| 1. Retrieve | Run the audit workflow (ORCID publication audit, Citation metrics audit, Scholar metrics audit). | Artifact with proposed files | No |
| 2. Review | Download the artifact and check totals, failures, duplicate warnings and the largest changes. | Review notes | No |
| 3. Stage | Upload the proposed files to the matching `data/*-review/` folder. | Commit on `main` | No |
| 4. Apply | Run the matching apply workflow manually. | Live data, apply report, Pages rebuild | Yes |

## Publication refresh (ORCID)

1. Actions, ORCID publication audit, Run workflow.
2. Download artifact `orcid-publication-audit`. Review `publication-sync-status.json`.
3. Upload `publications.proposed.json` and `publication-sync-status.json` to `data/orcid-refresh-review/`.
4. Actions, Publish reviewed ORCID article extraction, Run workflow.
5. Check `data/orcid-refresh-apply-status.json`: counts, failed profiles, warnings.

The apply script stores fingerprints of the extraction it applied in `review_blobs`. It does not need editing between refreshes.

## Rules the apply script enforces

- The extraction must be newer than the last applied one, and its roster must match `data/faculty.json`.
- Re-running the same extraction changes nothing.
- Live publication files edited by hand since the last apply stop the run.
- Failed profiles keep their previous records, and a failure is never recorded as zero publications.
- No duplicate DOIs, no unknown profile links, no new non-ORCID sources.
- Names, portraits, identifiers, departments, citations and showcase data are not modified.

## Reading failures

A failed profile with a blank ORCID in `data/faculty.json` is a missing identifier, not a retrieval failure. Fix the profile data, then run a new audit.
