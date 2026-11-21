#!/usr/bin/env python3
"""Build a review copy of the university-wide research showcase from data/faculty.json.

Reads only cached Scholar profile metrics (no provider requests). Writes a proposed
page and a summary to data/research-showcase-review/; the live draft is not touched.
"""
import argparse
import html
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

MIN_PROFILES = 3
TOP_RESEARCHERS = 5
TOP_DEPARTMENTS = 3
OUT = 'data/research-showcase-review/'


def esc(value):
    return html.escape(str(value), quote=True)


def fmt(number):
    return f'{number:,}' if float(number).is_integer() else f'{number:,.2f}'


def collect(document):
    rows = document['faculty']
    stamps = [r['scholar_metrics']['retrieved_at'] for r in rows if r.get('scholar_metrics', {}).get('status') == 'success']
    if not stamps:
        raise ValueError('No successful Scholar metrics found')
    latest = max(stamps)
    people = []
    for r in rows:
        m = r.get('scholar_metrics') or {}
        if m.get('status') == 'success' and m.get('retrieved_at') == latest:
            people.append({'id': r['id'], 'name': r['name'], 'department': r['department'], 'author_id': m['author_id'], 'citations': m['total_citations'], 'h_index': m['h_index']})
    totals = defaultdict(int)
    for r in rows:
        totals[r['department']] += 1
    return latest, people, dict(totals)


def select(people):
    best = {}
    for p in people:
        if p['author_id'] not in best or p['citations'] > best[p['author_id']]['citations']:
            best[p['author_id']] = p
    researchers = sorted(best.values(), key=lambda p: (-p['citations'], p['name']))[:TOP_RESEARCHERS]
    per_department = defaultdict(dict)
    for p in people:
        per_department[p['department']][p['author_id']] = p
    table = []
    for department, members in per_department.items():
        values = [m['citations'] for m in members.values()]
        table.append({'department': department, 'profiles': len(values), 'sum': sum(values), 'mean': sum(values) / len(values), 'members': sorted(members.values(), key=lambda m: (-m['citations'], m['name']))})
    ranked = sorted([t for t in table if t['profiles'] >= MIN_PROFILES], key=lambda t: (-t['mean'], t['department']))[:TOP_DEPARTMENTS]
    table.sort(key=lambda t: (-t['profiles'], -t['mean'], t['department']))
    return researchers, ranked, table, len(best)


CSS = """.showcase-draft .draft-status{padding:14px 18px;border-left:4px solid var(--purple);background:#fffdf7;font:400 14px/1.6 Arial,Helvetica,sans-serif;margin:20px 0 28px}
.showcase-draft .showcase-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:20px;margin:24px 0}
.showcase-draft .showcase-card{min-width:0;padding:24px;border:1px solid var(--line);background:#fffdf7}
.showcase-draft .showcase-card h2{font-size:clamp(23px,2.4vw,30px);line-height:1.2;margin:8px 0 16px}
.showcase-draft .draft-kicker{font:600 11px/1.4 Arial,Helvetica,sans-serif;letter-spacing:.06em;text-transform:uppercase;color:var(--purple);margin:0}
.showcase-draft .showcase-card p{line-height:1.65}
.showcase-draft .draft-rule{font:400 13px/1.65 Arial,Helvetica,sans-serif;color:var(--muted)}
.showcase-draft .pending-selection{padding:16px;margin-top:20px;border:1px dashed var(--line);font:400 14px/1.6 Arial,Helvetica,sans-serif;color:var(--muted)}
.showcase-draft .example-list{list-style:none;padding:0;margin:20px 0 0}
.showcase-draft .example-list li{padding:16px 0;border-top:1px solid var(--line)}
.showcase-draft .example-list h3{margin:0 0 8px;font:600 16px/1.5 Arial,Helvetica,sans-serif;overflow-wrap:anywhere}
.showcase-draft .example-list p{margin:6px 0;font:400 14px/1.65 Arial,Helvetica,sans-serif}
.showcase-draft .example-value{color:var(--purple);font:600 18px/1.5 Arial,Helvetica,sans-serif}
.showcase-draft .draft-method{max-width:85ch}
.showcase-draft .draft-method li{margin-bottom:12px;line-height:1.7}
.showcase-draft .draft-method details{margin:18px 0;padding:16px;border:1px solid var(--line)}
.showcase-draft .draft-method summary{cursor:pointer;font:600 14px/1.5 Arial,Helvetica,sans-serif}
.showcase-draft .draft-links{display:flex;flex-wrap:wrap;gap:16px;margin:24px 0}
.showcase-draft .coverage-scroll{overflow-x:auto;margin:20px 0}
.showcase-draft .coverage-table{border-collapse:collapse;width:100%;font:400 14px/1.6 Arial,Helvetica,sans-serif}
.showcase-draft .coverage-table caption{text-align:left;margin-bottom:12px}
.showcase-draft .coverage-table th,.showcase-draft .coverage-table td{padding:12px;text-align:left;border-bottom:1px solid var(--line);vertical-align:top}
@media(max-width:760px){.showcase-draft .showcase-grid{grid-template-columns:1fr}.showcase-draft .showcase-card{padding:20px}}"""

PAPERS = """<section class="showcase-card" aria-labelledby="cited-papers-heading"><p class="draft-kicker">Illustrative placeholders · Existing paper-level records</p><h2 id="cited-papers-heading">Highly cited papers and their researchers</h2><p>Examples showing how papers and their associated university researchers will appear. These are not a university-wide top three.</p>
<ul class="example-list">
<li><h3>Carbon Sequestration Potential of Agroforestry Systems in India</h3><p>2013 · Associated university researcher: Prof. Rakesh Tiwari · Environmental Science</p><p><span class="example-value">349 citations</span> · Cached Google Scholar count</p></li>
<li><h3>Climate change vulnerability profiles for North East India</h3><p>2011 · Associated university researcher: Prof. Rakesh Tiwari · Environmental Science</p><p><span class="example-value">308 citations</span> · Cached Google Scholar count</p></li>
<li><h3>MGNREGA for environmental service enhancement and vulnerability reduction: rapid appraisal in Chitradurga district, Karnataka</h3><p>2011 · Associated university researcher: Prof. Rakesh Tiwari · Environmental Science</p><p><span class="example-value">143 citations</span> · Cached Google Scholar count</p></li>
</ul><p class="draft-rule">These are multi-author publications; the named person is the associated university researcher in the imported records, not the sole author. Source: Google Scholar via SerpApi, cached on 31 October 2026 at approximately 20:11 IST. This paper-level snapshot is separate from the profile-summary batch and was not refreshed in November.</p></section>"""

PEER = """<section class="showcase-card" aria-labelledby="peer-review-heading"><p class="draft-kicker">Planned university-wide category</p><h2 id="peer-review-heading">Recorded peer-review contributions</h2><p>Recognise contributions to scholarly evaluation using publicly recorded ORCID peer-review activities.</p><div class="pending-selection">Data pending. No peer-review activity dataset has been collected for this showcase. Names and review counts are intentionally left unassigned rather than invented.</div><p class="draft-rule">Planned basis: distinct public peer-review activities, not published review articles or the number of journal groups. No peer-review retrieval is triggered by this page.</p></section>"""


def page(latest, researchers, ranked, table, unique, listed, total_records):
    when = datetime.fromisoformat(latest).astimezone(timezone.utc).strftime('%d %B %Y at %H:%M UTC')
    day = datetime.fromisoformat(latest).astimezone(timezone.utc).strftime('%d %B %Y')
    r_items = ''.join(f'<li><h3>{i}. {esc(p["name"])}</h3><p>{esc(p["department"])}</p><p><span class="example-value">{fmt(p["citations"])} profile citations</span></p></li>' for i, p in enumerate(researchers, 1))
    d_items = ''.join(f'<li><h3>{i}. {esc(t["department"])}</h3><p><span class="example-value">{fmt(round(t["mean"], 2))} citations per retrieved profile</span></p><p>Sum of profile counts: {fmt(t["sum"])} ÷ {t["profiles"]} retrieved profiles.</p></li>' for i, t in enumerate(ranked, 1))
    rows = ''.join(f'<tr><th scope="row">{esc(t["department"])}</th><td>{t["profiles"]}</td><td>{fmt(round(t["mean"], 2))}</td><td>{"Ranked" if t["profiles"] >= MIN_PROFILES else "Not ranked (fewer than %d)" % MIN_PROFILES}</td></tr>' for t in table)
    inputs = ''.join(f'<li>{esc(t["department"])}: ' + '; '.join(f'{esc(m["name"])} {fmt(m["citations"])}' for m in t['members']) + '.</li>' for t in sorted(table, key=lambda t: t['department']))
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow"><meta name="description" content="University-wide research showcase working draft, generated from cached Scholar profile metrics. Not verified university-wide rankings.">
<title>Research showcase — Working draft — Kuvempu University</title>
<link rel="stylesheet" href="assets/css/style.css">
<style>
{CSS}
</style>
</head>
<body class="showcase-draft">
<a class="skip" href="#main">Skip to content</a>
<header class="wrap brandrow"><a class="brand" href="index.html" aria-label="Kuvempu University homepage"><img src="assets/img/placeholders/kulogo.png" alt="" width="48" height="56"><span class="brandname">Kuvempu University</span></a><nav aria-label="Draft page navigation"><a href="about-research-metrics.html">About research metrics →</a></nav></header>
<main id="main" class="wrap page-pad">
<p class="breadcrumb"><a href="index.html">Home</a> / Research showcase / Working draft</p>
<div class="page-intro"><p class="eyebrow">University-wide research · Working draft</p><h1>Research showcase</h1><p>Recognising research influence, scholarly service and departmental contributions across Kuvempu University.</p></div>
<p class="draft-status" role="note">Illustrative selections from cached Google Scholar profile totals—not verified university-wide rankings. Generated from the profile-summary batch retrieved on {when}: {unique} unique Scholar profiles across {len(table)} departments, from {total_records} profile records on the website ({listed} with a retrieved Scholar profile in this batch). Profiles without a usable Scholar link are not assigned zero. No fresh retrieval was performed for this page.</p>
<div class="showcase-grid">
{PAPERS}
<section class="showcase-card" aria-labelledby="researcher-highlights-heading"><p class="draft-kicker">Top {TOP_RESEARCHERS} within the cached profile batch</p><h2 id="researcher-highlights-heading">Researcher highlights</h2><p>Ordered by cached all-time Google Scholar profile citations across all {unique} unique profiles in the batch—not by citations per research paper.</p>
<ul class="example-list">
{r_items}
</ul><p class="draft-rule">Source: Google Scholar via SerpApi, retrieved on {when}. These are profile totals, not sums of the website’s imported papers. People are counted once by Scholar author ID even if they appear in more than one department. Profile citations may include work completed at other institutions.</p></section>
{PEER}
<section class="showcase-card" aria-labelledby="departments-heading"><p class="draft-kicker">Top {TOP_DEPARTMENTS} among departments with at least {MIN_PROFILES} retrieved profiles</p><h2 id="departments-heading">Department highlights</h2><p>Ordered by mean cached profile citations per successfully retrieved researcher profile. This draft measure is not citations per staff member.</p>
<ul class="example-list">
{d_items}
</ul><p class="draft-rule">Only departments with at least {MIN_PROFILES} retrieved profiles are ranked. A mean describes only the retrieved subset, and a few highly cited profiles can dominate it. Profile counts can include citations to shared papers more than once across researchers. No verified staff headcount or field normalisation is applied. Missing profiles are excluded, not assigned zero.</p></section>
</div>
<section class="department-section draft-method" aria-labelledby="coverage-heading"><h2 id="coverage-heading">All departments with retrieved profiles</h2><p>Every department below contributed to the calculations. Departments with fewer than {MIN_PROFILES} retrieved profiles are shown for coverage but are not ranked.</p><div class="coverage-scroll" role="region" aria-label="Cached profile batch department coverage" tabindex="0"><table class="coverage-table"><caption>Google Scholar profile-summary batch · {day} · {unique} unique Scholar profiles</caption><thead><tr><th scope="col">Department</th><th scope="col">Retrieved profiles</th><th scope="col">Mean citations per retrieved profile</th><th scope="col">Status</th></tr></thead><tbody>{rows}</tbody></table></div><p class="draft-rule">Departments without a successful retrieval are not listed and are not ranked as low-performing. University-wide scope does not imply complete data coverage.</p></section>
<section class="department-section draft-method" aria-labelledby="draft-method-heading"><h2 id="draft-method-heading">How to read this working draft</h2><p>These are replaceable examples, not verified institutional performance selections. Profile totals, paper-level citation counts, citations per paper and citations per staff member are distinct measures and are not substituted for one another. No fresh citation retrieval, paid provider calls or automatic selection jobs are enabled by this page.</p><p><a href="data/faculty.json">Current faculty profile records →</a> · <a href="data/environmental-scholar-citations.json">Separate paper-level pilot snapshot →</a></p>
<details><summary>Profile inputs used for these highlights</summary><p>All-time profile citation totals from the {day} retrieval batch. Imported identity associations remain subject to review.</p><ul>{inputs}</ul></details>
<details><summary>Rules before publishing verified university-wide selections</summary><ol><li>Reconcile researcher identities, department assignments and eligible roles against the university roster.</li><li>Use the same citation source and reporting scope within each comparison.</li><li>Agree reporting periods, eligible output types, minimum coverage and treatment of ties.</li><li>Display sources, retrieval dates and denominators. Missing records must not silently become zeroes.</li><li>Review selections before calling them university-wide leaders. These metrics are not field-normalised measures of research quality.</li></ol></details>
</section>
</main>
<footer><div class="wrap"><p>Working draft · Illustrative cached examples · Not verified university-wide rankings.</p><p>Copyright: Kuvempu University; Designed by Prof Rakesh Tiwari</p></div></footer>
</body>
</html>
"""


def build(root):
    root = Path(root)
    document = json.loads((root / 'data/faculty.json').read_text(encoding='utf-8'))
    latest, people, totals = collect(document)
    researchers, ranked, table, unique = select(people)
    text = page(latest, researchers, ranked, table, unique, len(people), sum(totals.values()))
    out = root / OUT
    out.mkdir(parents=True, exist_ok=True)
    (out / 'research-showcase.proposed.html').write_text(text, encoding='utf-8')
    summary = {'batch_retrieved_at': latest, 'unique_profiles': unique, 'departments_with_profiles': len(table), 'minimum_profiles_to_rank': MIN_PROFILES, 'researchers': researchers, 'ranked_departments': [{k: t[k] for k in ('department', 'profiles', 'sum', 'mean')} for t in ranked], 'coverage': [{k: t[k] for k in ('department', 'profiles', 'mean')} for t in table]}
    (out / 'research-showcase-summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return summary


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    result = build(ap.parse_args().root)
    print(json.dumps({'unique_profiles': result['unique_profiles'], 'ranked': [d['department'] for d in result['ranked_departments']]}, indent=2))
