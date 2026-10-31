let snapshot;
export async function apply(result){
result.citationSource='Google Scholar';result.citations=null;result.citationCoverage=0;result.citationDates=[];result.metrics={source:'Google Scholar',entriesById:Object.create(null)};
try{
if(!snapshot)snapshot=fetch(new URL('../../data/environmental-scholar-citations.json',import.meta.url)).then(r=>{if(!r.ok)throw Error('Scholar snapshot unavailable');return r.json()});
const s=await snapshot,stamp=Date.parse(s.retrieved_at);
if(s.schema_version!==1||s.department_id!=='environmental-science'||s.source!=='Google Scholar'||!Number.isFinite(stamp)||stamp>Date.now()||!Array.isArray(s.records))throw Error('Invalid Scholar snapshot');
const records=new Map();
for(const row of s.records){const [id,doi,year,count,clusters]=row;if(typeof id!=='string'||typeof doi!=='string'||!Number.isSafeInteger(year)||!Number.isSafeInteger(count)||count<0||typeof clusters!=='string'||!/^\d+(?:,\d+)*$/.test(clusters)||records.has(id))throw Error('Invalid Scholar record');records.set(id,{id,doi,year,count,source_url:'https://scholar.google.com/scholar?cites='+encodeURIComponent(clusters),retrieved_at:s.retrieved_at})}
const matched=[];
for(const p of result.papers){const row=records.get(p.id);if(row&&row.doi===(p.doi||'')&&String(row.year)===String(p.year)){result.metrics.entriesById[p.id]=row;matched.push(row)}}
result.citations=matched.length?matched.reduce((n,p)=>n+p.count,0):null;result.citationCoverage=matched.length;result.citationDates=matched.length?[s.retrieved_at]:[];
result.note='Teaching-team and published PhD-student records, deduplicated across both lists. Google Scholar counts retrieved via SerpApi; '+matched.length+' of '+result.papers.length+' eligible research papers have automatically matched citation values in this view. Snapshot: '+s.retrieved_at+'. The retrieval covered '+s.profiles_retrieved+' public Scholar profiles; '+s.researchers_without_usable_profile+' listed researchers lacked a usable recorded Scholar profile. Exact normalised title and year matching with supporting author-name overlap; these are not independently verified matches. Missing and conflicting counts are excluded, not treated as zero. No OpenAlex values are added or silently substituted. Coverage is incomplete, and records may predate the researcher’s time at Kuvempu University. This paper-level Scholar snapshot is not automatically refreshed.';
result.metadata.coverage='Combined teaching-team and PhD-student publication records; citation source: Google Scholar (automatically matched snapshot).';
}catch{result.note='Google Scholar citation snapshot unavailable or invalid. Citation values are not replaced with OpenAlex counts or shown as zero. Publication and PhD figures retain their existing definitions.';result.metadata.coverage='Google Scholar citation snapshot unavailable.'}
return result;
}
