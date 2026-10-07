import argparse,hashlib,json,struct,subprocess,shutil,os
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument('image_id');p.add_argument('generated_file')
args=p.parse_args()
root=Path(os.environ.get('BIXIE_PACKAGE_ROOT',Path(__file__).resolve().parents[1]))
plan=json.loads((root/'media/generation-plan.json').read_text())
item=next(r for r in plan['planned_assets'] if r['id']==args.image_id)
original=root/item['source_file']
original.parent.mkdir(parents=True,exist_ok=True)
generated=Path(args.generated_file)
if original.exists(): raise SystemExit('Refusing to overwrite existing original; resume or use a distinct retry id')
shutil.copy2(generated,original)
data=original.read_bytes()
if data[:8]!=b'\x89PNG\r\n\x1a\n':raise SystemExit('Unexpected source encoding; PNG required for native header audit')
w,h=struct.unpack('>II',data[16:24])
display=root/item['file']
display.parent.mkdir(parents=True,exist_ok=True)
subprocess.run(['ffmpeg','-nostdin','-y','-i',str(original),'-c:v','libwebp','-quality','95','-compression_level','6',str(display),'-loglevel','error'],check=True)
record={
'id':item['id'],'key':item['id'],'look_id':item.get('look_id'),'look_key':item.get('look_id'),'canonical_look_key':item.get('look_id'),'collection':item.get('collection'),'usage':item['usage'],'angle':item.get('angle'),
'source_file':item['source_file'],'file':item['file'],'width':w,'height':h,
'sha256':hashlib.sha256(data).hexdigest(),'display_sha256':hashlib.sha256(display.read_bytes()).hexdigest(),
'source_bytes':len(data),'display_bytes':display.stat().st_size,'native_original':True,'native_8k':False,'upscaled':False,'generated':True,'fictional_adult':True,
'generated_tool_file':str(generated),'generator':'OpenAI image_gen','exact_generation_prompt':item['prompt'],'reference_source_files':item.get('references',[]),
'approved':False,'review_status':'awaiting-direct-source-review','public_status':'draft','expected_meta':item.get('expected_meta',{}),'shape_brief':item.get('shape_brief',{}),
'alt':'Pending direct review of actual haircut and clothing','caption':'Generated fictional adult haircut reference; actual native dimensions recorded.',
}
out=root/'media/records'/f'{args.image_id}.json'
temporary=out.with_suffix('.json.tmp')
temporary.write_text(json.dumps(record,indent=2)+'\n')
temporary.replace(out)
subprocess.run(['python',str(Path(__file__).with_name('native_source.py')),args.image_id],check=True)
print(json.dumps({'id':args.image_id,'source_file':str(original),'width':w,'height':h,'source_bytes':len(data),'review_status':record['review_status']}))
