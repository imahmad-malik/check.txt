#!/usr/bin/env python3
"""Merge only actual reviewed, coherent look sets from a source-media manifest.

Read-only on media files. Planned requests and partial sets never become public
looks. This updates the portable content payload, not a live WordPress site.
"""
from pathlib import Path
from collections import defaultdict, Counter
import argparse, csv, hashlib, json, re, html
from PIL import Image

ROOT=Path(__file__).resolve().parent
parser=argparse.ArgumentParser()
parser.add_argument('--manifest',type=Path,default=ROOT.parent/'media'/'manifest.json')
parser.add_argument('--bundle-root',type=Path,default=ROOT.parent)
parser.add_argument('--look-keys',help='Optional comma-separated finalized look keys for a stable attachment-source handoff.')
args=parser.parse_args()
allowed_look_keys=set(args.look_keys.split(',')) if args.look_keys else None
catalog_path=ROOT/'catalog.json'
catalog=json.loads(catalog_path.read_text())
manifest=json.loads(args.manifest.read_text())
minimum=catalog['requirements']['minimum_native_long_edge']
records=list(manifest.get('records',[]))
declared_looks=manifest.get('looks',[])
if isinstance(declared_looks,dict):
    declared_looks=[{'key':k,**v} for k,v in declared_looks.items()]
else: declared_looks=list(declared_looks)
# A later bundle may contain only the next batch. Retain earlier sets, but
# reverify every actual source before including it in the updated catalog.
incoming_look_keys={x.get('key') or x.get('id') or x.get('look_id') for x in declared_looks}
incoming_image_keys={x.get('key') or x.get('id') for x in records}
for prior in catalog.get('looks',[]):
    if prior['key'] in incoming_look_keys: continue
    declared_looks.append(prior)
    for image in prior['images']:
        if image['key'] not in incoming_image_keys:
            records.append({**image,'look_id':prior['key']})
by_look=defaultdict(list)
file_diagnostics=[]
verified_records={}
all_real_sources={}
approved_home_records={}
required_home_keys=set(catalog['requirements'].get('required_home_media',[]))

def approved(obj):
    return obj.get('approved') is True and obj.get('review_status',obj.get('approval_status'))=='approved'

def paragraph(text):
    return '<!-- wp:paragraph -->\n<p>'+text+'</p>\n<!-- /wp:paragraph -->'

for r in records:
    key=r.get('key') or r.get('id')
    source=r.get('source_file') or r.get('file')
    if not source: continue
    if Path(source).suffix.lower() in ['.mp4','.webm','.mov']:
        continue  # video has separate production/runtime verification
    source_path=(args.bundle_root/source).resolve()
    try: source_path.relative_to(args.bundle_root.resolve())
    except ValueError:
        file_diagnostics.append({'key':key,'reason':'source path outside bundle'});continue
    if not source_path.is_file():
        file_diagnostics.append({'key':key,'reason':'missing source file'});continue
    try:
        with Image.open(source_path) as im:
            width,height=im.size
            im.verify()
    except Exception as e:
        file_diagnostics.append({'key':key,'reason':'unreadable image: '+type(e).__name__});continue
    digest=hashlib.sha256(source_path.read_bytes()).hexdigest()
    all_real_sources[digest]={'file':source,'width':width,'height':height}
    reasons=[]
    if r.get('sha256')!=digest: reasons.append('source hash mismatch/missing')
    if (r.get('width'),r.get('height'))!=(width,height): reasons.append('native dimensions mismatch/missing')
    if not approved(r): reasons.append('not explicitly approved')
    if r.get('upscaled') is not False: reasons.append('no-upscale assertion missing or failed')
    if max(width,height)<minimum: reasons.append('below accepted native long-edge minimum')
    if r.get('native_8k') is True and max(width,height)<7680: reasons.append('false native8K flag')
    if not r.get('alt'): reasons.append('reviewed image-specific alt missing')
    if key in required_home_keys:
        if reasons:
            file_diagnostics.append({'key':key,'reason':'; '.join(reasons)})
        else:
            approved_home_records[key]={**r,'key':key,'source_file':source,'width':width,'height':height,'sha256':digest}
        continue
    if r.get('angle') not in ['front','side','back']: reasons.append('not a canonical view angle')
    look_key=r.get('look_id') or r.get('look_key')
    if not look_key: reasons.append('no canonical look assignment')
    if reasons:
        file_diagnostics.append({'key':key,'look_key':look_key,'reason':'; '.join(reasons)});continue
    verified={**r,'key':key,'source_file':source,'width':width,'height':height,'sha256':digest}
    verified_records[key]=verified
    by_look[look_key].append(verified)

canonical_collections={c['key'] for c in catalog['collections']}
briefs=json.loads((ROOT/'production-briefs.json').read_text())['briefs']
launch_keys={b['key'] for b in briefs if b['scope']=='launch-target'}
actual_looks=[]
look_diagnostics=[]
used_hashes=set()
for declaration in declared_looks:
    key=declaration.get('key') or declaration.get('id') or declaration.get('look_id')
    if allowed_look_keys is not None and key not in allowed_look_keys:
        look_diagnostics.append({'key':key,'reason':'not selected for this explicit stable source/hash handoff'})
        continue
    images=by_look.get(key,[])
    reasons=[]
    if key not in launch_keys: reasons.append('not a canonical launch look key')
    if not approved(declaration): reasons.append('coherent-set approval missing')
    if len(images)!=3 or {i['angle'] for i in images}!={'front','side','back'}: reasons.append('approved complete front/side/back set missing')
    hashes={i['sha256'] for i in images}
    if len(hashes)!=3: reasons.append('three views are not three distinct original sources')
    if hashes&used_hashes: reasons.append('source reused by another primary look')
    collection=declaration.get('primary_collection') or declaration.get('collection')
    if not collection:
        collection=next((c for c in sorted(canonical_collections,key=len,reverse=True) if key and key.startswith(c+'-')),None)
    if collection not in canonical_collections: reasons.append('unknown primary collection')
    observations={}
    for image in images:
        for field,value in (image.get('observed_meta') or {}).items():
            if field in observations and observations[field]!=value:
                reasons.append('inconsistent reviewed '+field+' across real views')
            observations[field]=value
    observations.update(declaration.get('observed_meta') or {})
    if reasons:
        look_diagnostics.append({'key':key,'reason':'; '.join(reasons)});continue
    images=sorted(images,key=lambda x:['front','side','back'].index(x['angle']))
    title=declaration.get('title') or ('Bixie concept '+key)
    reviewed_shape=' '.join(i.get('caption','') for i in [images[0],images[-1]] if i.get('caption'))
    short_copy=declaration.get('excerpt') or reviewed_shape or title+'. Corresponding front, side and back views.'
    content=declaration.get('content') or '\n\n'.join([
        paragraph(html.escape(short_copy)),
        paragraph('Discuss the crown, fringe and nape details you prefer with your stylist. AI-created concept featuring a fictional adult; an image does not guarantee the same result on your own hair.')])
    meta={**declaration.get('meta',{}),**observations,'ai_concept':True}
    final_images=[]
    for image in images:
        angle=image['angle']
        caption=image.get('caption') or {'front':'Front: compare the face frame and fringe.','side':'Side: compare ear coverage and the crown-to-nape transition.','back':'Back: compare the crown outline and nape.'}[angle]
        final_images.append({**image,'caption':caption,'approved':True,'review_status':'approved','native_8k':bool(image.get('native_8k',False)),'upscaled':False})
    actual_looks.append({'key':key,'slug':declaration.get('slug',key),'title':title,'content':content,'excerpt':short_copy,
                         'collections':[collection],'primary_collection':collection,'meta':meta,'images':final_images,
                         'approved':True,'review_status':'approved','status':'publish',
                         'review':declaration.get('review',{}),'source_bundle_id':declaration.get('source_bundle_id') or manifest.get('bundle_id')})
    used_hashes.update(hashes)

catalog['looks']=actual_looks
photos_by_collection=defaultdict(set)
looks_by_collection=Counter()
for look in actual_looks:
    c=look['primary_collection'];looks_by_collection[c]+=1
    photos_by_collection[c].update(i['sha256'] for i in look['images'])
for c in catalog['collections']:
    c['provided_primary_images']=len(photos_by_collection[c['key']])
    c['provided_complete_angle_sets']=looks_by_collection[c['key']]
    c['status']='ready' if c['provided_primary_images']>=20 and c['provided_complete_angle_sets']>=7 else 'draft-until-media-reviewed'
actual_keys={x['key'] for x in actual_looks}
guide_count=0
for p in catalog['pages']:
    if p['type']=='collection':
        c=next(x for x in catalog['collections'] if x['key']==p['gallery_collection'])
        p['status']='publish' if c['status']=='ready' else 'draft'
    if p['type']=='guide':
        requirements=p.get('photo_set_requirements',[])
        ready=bool(requirements) and all(x['look_key'] in actual_keys for x in requirements)
        p['status']='publish' if ready else 'draft'
        p['provided_photo_references']=sum(3 for x in requirements if x['look_key'] in actual_keys)
        guide_count+=p['provided_photo_references']
catalog['counts'].update({'actual_generated_source_files':len(all_real_sources),
                         'provided_unique_primary_collection_images':len(used_hashes),
                         'provided_importable_looks':len(actual_looks),
                         'provided_complete_three_angle_sets':len(actual_looks),
                         'provided_guide_photo_references':guide_count,
                         'provided_approved_home_role_images':len({r['sha256'] for r in approved_home_records.values()}),
                         'provided_complete_collections':sum(c['status']=='ready' for c in catalog['collections'])})
catalog['provided_media_manifest']='media/manifest.json'
catalog_path.write_text(json.dumps(catalog,indent=2,ensure_ascii=False)+'\n')
# Keep the production checklist truthful as actual sets replace empty briefs.
# Briefs remain planning documents, never a second set of imported posts.
production_path=ROOT/'production-briefs.json'
production=json.loads(production_path.read_text())
actual_by_key={look['key']:look for look in actual_looks}
for brief in production['briefs']:
    look=actual_by_key.get(brief['key'])
    brief['publish']=False
    if look:
        brief['status']='generated-approved'
        brief['provided_media_ids']=[image['key'] for image in look['images']]
        brief['images']=[{**image,'status':'generated-approved'} for image in look['images']]
    elif brief.get('status')=='generated-approved':
        brief['status']='required-not-generated'
        brief['provided_media_ids']=[]
        brief['images']=[{'key':brief['key']+'-'+angle,'angle':angle,'file':None,
                          'width':None,'height':None,'status':'required-not-generated'}
                         for angle in ['front','side','back']]
production_path.write_text(json.dumps(production,indent=2,ensure_ascii=False)+'\n')
report={'bundle_id':manifest.get('bundle_id'),'manifest':str(args.manifest),'status':'synchronized-actual-only',
        'actual_generated_source_files':len(all_real_sources),'actual_approved_complete_looks':len(actual_looks),
        'actual_approved_collection_view_photos':len(used_hashes),'actual_guide_photo_references':guide_count,
        'actual_approved_home_role_images':len({r['sha256'] for r in approved_home_records.values()}),
        'missing_home_role_keys':sorted(required_home_keys-set(approved_home_records)),
        'home_video_verification':'separate production/runtime check; not inferred from planned metadata',
        'remaining_launch_looks':max(0,154-len(actual_looks)),
        'remaining_launch_view_photos':max(0,462-len(used_hashes)),
        'file_diagnostics':file_diagnostics,'look_diagnostics':look_diagnostics,
        'per_collection':[{'key':c['key'],'actual_complete_looks':c['provided_complete_angle_sets'],'actual_unique_views':c['provided_primary_images'],'status':c['status']} for c in catalog['collections']]}
(ROOT/'actual-source-counts.json').write_text(json.dumps(report,indent=2)+'\n')
doc=ROOT/'CONTENT-COVERAGE.md'
start='<!-- ACTUAL_MEDIA_ACCOUNTING_START -->'
end='<!-- ACTUAL_MEDIA_ACCOUNTING_END -->'
summary='\n'.join([start,'## Actual source accounting',
                  f'Last synchronization verified **{len(all_real_sources)} existing original source files**, **{len(actual_looks)} approved complete three-angle looks**, **{len(used_hashes)} approved collection-view photographs** and **{guide_count} available guide-photo references**.',
                  f'The remaining launch requirement is **{report["remaining_launch_looks"]} complete looks / {report["remaining_launch_view_photos"]} collection views**. Planned records, renditions and partial/failed sets are not counted as completed looks.',
                  'See `actual-source-counts.json` for per-collection counts and explicit file/look diagnostics. Homepage-only roles and the real photo-film have separate approval gates.',end])
text=doc.read_text()
if start in text and end in text:
    text=text[:text.index(start)]+summary+text[text.index(end)+len(end):]
else: text+='\n\n'+summary+'\n'
doc.write_text(text)
print(json.dumps({k:report[k] for k in ['status','actual_generated_source_files','actual_approved_complete_looks','actual_approved_collection_view_photos','actual_guide_photo_references','remaining_launch_looks','remaining_launch_view_photos']},indent=2))
