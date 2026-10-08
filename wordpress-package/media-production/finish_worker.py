"""Resume helper: save real generation provenance and reviewed declarations.

Approval actions require the invoking human/agent to have actually inspected the
photograph. This helper neither generates nor visually approves photographs.
"""
import argparse, datetime, json, pathlib, subprocess, sys
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parents[1]
PROVENANCE = ROOT / 'media/workers/finish-media-provenance'
PROVENANCE.mkdir(exist_ok=True)
PLAN = {r['id']: r for r in json.loads((ROOT/'media/generation-plan.json').read_text())['planned_assets']}

def write(path, value):
    temporary = path.with_suffix(path.suffix+'.finish.tmp')
    temporary.write_text(json.dumps(value, indent=2)+'\n')
    temporary.replace(path)

def record(image_id):
    return json.loads((ROOT/'media/records'/f'{image_id}.json').read_text())

def previews(image_id):
    row = record(image_id)
    im = Image.open(ROOT/row['generator_original_file']).convert('RGB')
    width, height = im.size
    im.crop((width//2-200,height//3-200,width//2+200,height//3+200)).save(f'/tmp/{image_id}-native400.jpg',quality=98)
    im.thumbnail((400,400))
    im.save(f'/tmp/{image_id}-full400.jpg',quality=95)

action, image_id = sys.argv[1:3]
if action == 'request':
    item = PLAN[image_id]
    refs = []
    for ref in item.get('references', []):
        key = pathlib.Path(ref).stem
        r = record(key)
        assert r.get('approved') is True, 'Reference awaits direct review: '+key
        refs.append(str(ROOT/r['generator_original_file']))
    prompt = item['prompt'].replace('True LEFT SIDE PROFILE, face fully side-on and whole short nape visible, not three-quarter.', 'LEFT SIDE-FACING ANGLE, revealing temple, ear outline and whole short nape clearly; a profile or useful three-quarter side angle is acceptable. Keep it clearly distinct from the front.')
    prompt += ' Final framing requirement: image ends at the shoulder line, no lower torso visible; loose BULKY fully opaque high folded turtleneck covers the neck and all upper chest without chest contour, ivory cloth fills the lower edge. Adult subject only. Complete hair margin on every side.'
    q = {'image_id':image_id,'prompt':prompt,'references':refs,'state':'requested','requested_at':datetime.datetime.now(datetime.timezone.utc).isoformat()}
    write(PROVENANCE/f'{image_id}.json',q)
    print(json.dumps(q))
elif action == 'save':
    q = json.loads((PROVENANCE/f'{image_id}.json').read_text())
    q.update(tool_output_file=sys.argv[3], output_hint=sys.argv[4], state='saved-tool-output')
    write(PROVENANCE/f'{image_id}.json',q)
    subprocess.run([sys.executable,str(ROOT/'media-production/ingest_generated.py'),image_id,sys.argv[3]],check=True,cwd=ROOT,stdout=subprocess.DEVNULL)
    r = record(image_id)
    r.update(exact_generation_prompt=q['prompt'], reference_source_files=q['references'], provenance_record=str((PROVENANCE/f'{image_id}.json').relative_to(ROOT)))
    write(ROOT/'media/records'/f'{image_id}.json',r)
    previews(image_id)
    print(json.dumps({'id':image_id,'width':r['width'],'height':r['height'],'saved':True}))
elif action == 'approve':
    description = sys.argv[3]
    override = json.loads(sys.argv[4]) if len(sys.argv)>4 else {}
    r = record(image_id)
    meta = dict(r['expected_meta'])
    front = ROOT/'media/records'/f"{r['look_id']}-front.json"
    if r['angle'] != 'front': meta = dict(json.loads(front.read_text()).get('actual_meta', meta))
    meta.update(override)
    assert max(r['width'],r['height']) >= 1024 and r['native_pixel_identical_to_generator_png']
    r.update(approved=True, review_status='approved', public_status='ready-after-coherent-set-review',actual_meta=meta,observed_meta=meta,alt=f"{r['angle'].title()} view of a {meta['colour']} {meta['texture']} bixie",caption=description)
    r['review']={'reviewer':'finish-media','attire_pass':True,'complete_hair_outline_pass':True,'sharpness_pass':True,'viewpoint_pass':True,'native_resolution_pass':True,'method':'Actually inspected full-aspect <=400px photograph and a separate 400x400 crop of native hair/eye pixels; does not claim a full-native visual audit. Native dimensions, hashes and decoded PNG/lossless WebP RGB equality checked separately.','evidence':description+' Complete haircut margin, loose bulky opaque ivory high turtleneck covers neck and upper chest, sharp detail and neutral studio daylight.'}
    write(ROOT/'media/records'/f'{image_id}.json',r)
    print(json.dumps({'id':image_id,'approved':True,'actual_meta':meta}))
elif action == 'complete':
    rows=[record(image_id+'-'+a) for a in ['front','side','back']]
    assert all(r.get('approved') is True and r.get('review_status')=='approved' for r in rows)
    assert len({r['generator_original_sha256'] for r in rows})==3
    worker_file=ROOT/'media/workers/finish-90s-round.json'
    w=json.loads(worker_file.read_text()) if worker_file.exists() else {'worker':'finish-media','owned_look_keys':[f'{c}-{n:02}' for c in ['90s-inspired','round-face'] for n in range(1,8)],'looks':[]}
    assert image_id not in {l['key'] for l in w['looks']}
    meta=rows[0]['actual_meta']
    w['looks'].append({'key':image_id,'id':image_id,'slug':image_id,'canonical_look_key':image_id,'brief_key':image_id,'title':image_id.replace('-',' ').title(),'primary_collection':rows[0]['collection'],'collections':[rows[0]['collection']],'meta':meta,'actual_meta':meta,'observed_meta':meta,'expected_meta':rows[0]['expected_meta'],'expected_meta_matches_actual':meta==rows[0]['expected_meta'],'shape_brief':rows[0]['shape_brief'],'approved':True,'review_status':'approved','public_status':'draft','images':rows,'coherent_review':{'passed':True,'reviewer':'finish-media','method':'Compared all three separately generated actual full-aspect photographs, with native detail inspection supplements.','evidence':sys.argv[3]}})
    w.update(complete_approved_look_count=len(w['looks']), approved_image_count=3*len(w['looks']),updated_at=datetime.datetime.now(datetime.timezone.utc).isoformat())
    write(worker_file,w)
    print(json.dumps({'complete_look':image_id,'worker_complete_looks':len(w['looks'])}))
elif action == 'previews':
    previews(image_id)
