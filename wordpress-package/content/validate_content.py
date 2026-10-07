#!/usr/bin/env python3
"""Check content integrity independently of WordPress runtime validation."""
from pathlib import Path
import csv, json, re, hashlib
from collections import Counter

ROOT=Path(__file__).resolve().parent
catalog=json.loads((ROOT/'catalog.json').read_text())
production=json.loads((ROOT/'production-briefs.json').read_text())
failures=[]
checks=[]

def check(name,value,detail=''):
    checks.append({'check':name,'passed':bool(value),'detail':detail})
    if not value: failures.append(name)

pages=catalog['pages'];collections=catalog['collections'];briefs=production['briefs']
keys={p['key'] for p in pages}
routes={'/'}
for p in pages:
    parent=next((x for x in pages if x['key']==p.get('parent_key')),None)
    routes.add('/'+(parent['slug']+'/' if parent else '')+p['slug']+'/')

check('Distinct stable page keys',len(keys)==len(pages))
check('Distinct canonical page routes',len(routes)==len(pages)+1)
check('22 canonical collections',len(collections)==22)
check('Seven distinct supporting guides',sum(p['type']=='guide' for p in pages)==7)
actual_by_key={look['key']:look for look in catalog['looks']}
check('440 separate production briefs with truthful completion status',len(briefs)==440 and all(b['publish'] is False and b['status']==('generated-approved' if b['key'] in actual_by_key else 'required-not-generated') for b in briefs))
check('154 launch-target complete-set requirements',sum(b['scope']=='launch-target' for b in briefs)==154)
actual_looks=catalog['looks']
real_look_failures=[]
for look in actual_looks:
    images=look.get('images',[])
    if {i.get('angle') for i in images} != {'front','side','back'} or len(images)!=3:
        real_look_failures.append(look['key']+': angles')
    for i in images:
        source=i.get('source_file') or i.get('file')
        candidates=[ROOT/str(source),ROOT.parent/str(source)]
        file=next((x for x in candidates if x.is_file()),None)
        if not file or hashlib.sha256(file.read_bytes()).hexdigest()!=i.get('sha256'):
            real_look_failures.append(look['key']+': source/hash')
        if not i.get('approved') or i.get('upscaled') or max(i.get('width',0),i.get('height',0))<1024:
            real_look_failures.append(look['key']+': approval/native')
check('No fabricated completed looks',not real_look_failures and catalog['counts']['provided_importable_looks']==len(actual_looks),str(real_look_failures))
check('Accepted original native quality and complete-angle requirement',catalog['requirements']['minimum_native_long_edge']==1024 and catalog['requirements']['require_complete_angles'] is True and catalog['requirements']['no_upscaling'] is True and catalog['requirements']['no_8k_claim'] is True)
brief_media_failures=[]
for brief in briefs:
    actual=actual_by_key.get(brief['key'])
    if not actual:
        if brief['provided_media_ids'] or any(i.get('file') is not None or i.get('width') is not None or i.get('height') is not None for i in brief['images']):
            brief_media_failures.append(brief['key']+': fictitious unfinished media')
        continue
    by_image={image['key']:image for image in actual['images']}
    if set(brief['provided_media_ids'])!=set(by_image) or len(brief['images'])!=3:
        brief_media_failures.append(brief['key']+': actual set identifiers')
    for image in brief['images']:
        source=by_image.get(image['key'],{})
        for field in ['source_file','file','sha256','width','height','angle','approved','review_status']:
            if image.get(field)!=source.get(field):
                brief_media_failures.append(brief['key']+': actual '+field)
check('Every completed brief matches a hash-verified actual coherent set',not brief_media_failures,str(brief_media_failures))
check('Unique intended haircut structure design keys',len({b['shape_brief']['distinctness_basis'] for b in briefs})==len(briefs))
check('No inflation of collection planned photos',all(c['minimum_complete_looks']==7 and c['planned_unique_view_images']==21 and len(c['required_primary_look_ids'])==7 for c in collections))
unready_collection_keys={c['key'] for c in collections if c['provided_primary_images']<20 or c['provided_complete_angle_sets']<7}
check('All unpopulated collections remain drafts',all(p['status']=='draft' for p in pages if p['type']=='collection' and p['gallery_collection'] in unready_collection_keys))
check('Contact and privacy require genuine owner review',all(p['status']=='draft' for p in pages if p['key'] in ['contact','privacy']))
guide_pages=[p for p in pages if p['type']=='guide']
check('All guides allocate complete three-angle canonical photo sets',all(p.get('photo_set_requirements') and all(x['angles']==['front','side','back'] for x in p['photo_set_requirements']) for p in guide_pages))
actual_look_keys={x['key'] for x in actual_looks}
check('Image-led guides stay draft with missing actual photo sets',all(p['status']=='draft' for p in guide_pages if not all(s['look_key'] in actual_look_keys for s in p['photo_set_requirements'])))
check('Guide allocation totals24 views with no additional originals',sum(p['minimum_photos'] for p in guide_pages)==24 and catalog['counts']['additional_originals_required_for_guides']==0)
check('Fine-versus-thin guide shows two distinct complete reference sets',next(p for p in guide_pages if p['key']=='fine-vs-thin-hair')['minimum_photos']==6)
check('Guide look allocations are distinct across guides',len({x['look_key'] for p in guide_pages for x in p['photo_set_requirements']})==8)

missing_links=[];unbalanced=[];h1s=[];bad_parent=[]
for p in pages:
    if p.get('parent_key') and p['parent_key'] not in keys: bad_parent.append(p['key'])
    if re.search(r'<h(?:1|[4-6])\b',p['content']): h1s.append(p['key'])
    for path in re.findall(r'href="(/[^"]*)"',p['content']):
        if path not in routes: missing_links.append((p['key'],path))
    stack=[]
    for marker in re.findall(r'<!--\s*(.*?)\s*-->',p['content']):
        if marker.startswith('wp:'):
            if not marker.endswith('/'):
                stack.append(marker.split()[0][3:])
        elif marker.startswith('/wp:'):
            if not stack or stack.pop()!=marker.split()[0][4:]: unbalanced.append(p['key'])
    if stack: unbalanced.append(p['key'])
check('All native block serialization markers balanced',not unbalanced,str(unbalanced))
check('No body H1 or H4-H6',not h1s,str(h1s))
check('All internal editorial links resolve to catalog destinations',not missing_links,str(missing_links))
check('All page parents declared',not bad_parent,str(bad_parent))
check('All mapped keyword destinations resolve',all(not x['canonical_route'] or x['canonical_route'] in routes for x in catalog['canonical_keyword_map']))
check('All 81 shortlisted terms accounted',len(catalog['canonical_keyword_map'])==81 and len({x['keyword'] for x in catalog['canonical_keyword_map']})==81)
check('Organic main term rank preserved',next(x for x in catalog['canonical_keyword_map'] if x['keyword']=='bixie haircut')['organic_positions']=='johnfrieda.com: 2; nealandwolf.com: 1; stylist.co.uk: 5')
check('Source snapshot metrics remain separate',next(x for x in catalog['canonical_keyword_map'] if x['keyword']=='bixie haircut')['keyword_magic_volume']=='22200' and next(x for x in catalog['canonical_keyword_map'] if x['keyword']=='bixie haircut')['positions_export_volume']=='27100')
check('SEO titles respect concise 60-character preference',all(len(p['seo_title'])<=60 for p in pages))
check('Collection metadata descriptions unique',len({c['meta_description'] for c in collections})==len(collections))

report={'status':'passed' if not failures else 'failed','checks_passed':len(checks)-len(failures),'checks_total':len(checks),'failures':failures,'checks':checks,
        'counts':catalog['counts'],'keyword_dispositions':dict(Counter(x['disposition'] for x in catalog['canonical_keyword_map'])),
        'not_verified':['WordPress editor round trip and rendering','Live internal route responses','Rendered SEO-plugin coexistence','Full launch media and complete view sets until actual approval/import','Current external-source content behind proxy403','Live rankings/field performance']}
(ROOT/'content-validation.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'status':report['status'],'checks_passed':report['checks_passed'],'checks_total':report['checks_total'],'failures':failures},indent=2))
raise SystemExit(1 if failures else 0)
