# Google Scholar metrics: review-first setup

This pipeline retrieves all-time total citations, h-index and i10-index from SerpApi's Google Scholar Author endpoint. SerpApi is a third-party provider, not an official Google API. Provider quota and charges may apply.

## Safety defaults

- No live request on push, in tests, or on a default manual run.
- Live manual runs require `live_approved: true` AND the repository secret `SCHOLAR_SERPAPI_KEY`.
- Weekly Monday 01:37 UTC audits make live requests only if the repository Actions variable `SCHOLAR_METRICS_ENABLED` is explicitly set to `true`. Leave it absent or false until the pilot has been approved.
- The workflow has read-only repository permissions. It does not commit, publish, or alter website data.
- No CAPTCHA bypass, direct Google scraping, raw provider payload storage, or browser-side API keys.
- One request per distinct selected author per run, with no automatic retries or article pagination. API quota still applies; provider caching may reduce usage.

## First pilot

1. Add a SerpApi key as repository Settings > Secrets and variables > Actions > Secrets > `SCHOLAR_SERPAPI_KEY`. Never paste it into chat or commit it.
2. Keep `SCHOLAR_METRICS_ENABLED` unset.
3. After approval, run Actions > Google Scholar metrics audit with scope `pilot` and live approval checked. It targets `rakesh-tiwari` only.
4. Download the `scholar-metrics-audit` artifact. Review `scholar-sync-status.json` and the proposed `scholar_metrics` object in `faculty.proposed.json` against the public author profile, including the author name.
5. After approval, merge only the reviewed `scholar_metrics` objects into the CURRENT `data/faculty.json`. Do not replace the whole file from an old artifact, as other profile details may have changed. The existing profile renderer reads these objects without an additional metrics API call.
6. Expand to manual scope `all` after the pilot is verified. Enable the weekly audit variable only after agreeing to recurring provider usage. Weekly output remains review-only; automatic website publication is not enabled in this version.

## Validation and failure behaviour

The response must report success, match the configured Scholar author ID, and supply all three all-time values. Recent-period columns are never substituted. Missing/invalid values are not converted to zero. Valid zeroes remain zero. Wrong profiles, incomplete metrics and inconsistent counts are rejected.

Failures preserve prior metrics only when their source, scope and Scholar URL match the current profile. The original successful retrieval date remains unchanged; latest attempt/status are stored separately. The profile status helper adds a small failure/staleness note when such reviewed data is published. First-time failures leave metric slots unpopulated.

`retrieved_at` records when this pipeline received the provider result; it is not a claim about Google's indexing date. SerpApi may return a cached response. No API keys, request URLs containing keys, or raw provider error text are saved in artifacts or logs.

The existing ORCID publication and OpenAlex DOI citation audits remain independent and unchanged.

## Local offline tests

```sh
python -m unittest discover -s tests -p 'test_scholar_metrics.py' -v
```

A deliberately approved live audit can also be run locally with the secret supplied through the environment:

```sh
python scripts/sync_scholar_metrics.py --live --faculty rakesh-tiwari --out scholar-audit
```

There is no `--apply` option: proposed results always require publication review.
