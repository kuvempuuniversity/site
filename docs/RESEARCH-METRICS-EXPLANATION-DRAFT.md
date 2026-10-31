# Website concept and research-metrics explanation — draft

Status: preserved for collaborative editing, not a final central website page. The user asked to return to this wording later. Do not treat this draft as approval to publish the full central explanation.

## Proposed central page title
About this website and research metrics

## Wording to revisit together
Research paper and citation figures summarise the publicly available scholarly records associated with the teaching staff and research students listed on this website. These records may include work completed before a researcher joined Kuvempu University or while affiliated with another institution.

The figures therefore represent the combined scholarly records of the listed researchers; they should not be interpreted as totals of research conducted exclusively at Kuvempu University or during their period of affiliation with the University.

Shared papers are counted once within each department. Publication and citation coverage may be incomplete and depends on the available source records. Citation figures identify their source and retrieval date.

PhDs awarded are reported separately from verified departmental records and are not calculated from researchers’ qualifications or current student profiles.

## Initial implementation scope
- Combine the teaching team and published PhD-student profiles; avoid duplicate papers across their lists.
- Research paper count: source-classified journal articles, reviews and full conference papers. Exclude preprints, books, chapters, theses, posters, abstracts and flagged unpublished outputs from this counter. Keep other outputs in the publication list.
- Sum available validated OpenAlex counts for the same counted papers. Do not add author-level Google Scholar totals.
- Missing citation counts are not zero. Use the freshest valid cached DOI count and show coverage and retrieval dates.
- Reconcile known researcher IDs with current department assignments; disclose legacy department-tag fallback.
- PhDs awarded remain unavailable until an administrator supplies a nonnegative count, verified_through date and source in data/department-phds.json, under departments[department_id].
- No new scraping, paid API calls or scheduled refresh is enabled by this structure.
- Keep the research summary and department publication view on one shared collection. Other outputs are displayed but excluded from the paper/citation summary counters.
