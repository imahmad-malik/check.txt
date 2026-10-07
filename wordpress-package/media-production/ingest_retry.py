import argparse, hashlib, json, os, shutil, struct, subprocess
from pathlib import Path

p=argparse.ArgumentParser()
p.add_argument('image_id');p.add_argument('generated_file');p.add_argument('provenance_json')
a=p.parse_args()
r=Path(os.environ.get('BIXIE_PACKAGE_ROOT',Path(__file__).resolve().parents[1]))
record_file=r/'media/records'/f'{a.image_id}.json'
old=json.loads(record_file.read_text())
assert not old['approved'], 'Refusing to replace approved source'
provenance=json.loads(Path(a.provenance_json).read_text())
attempt=1
while (r/'source-media'/f'{a.image_id}-retry{attempt:02}.png').exists(): attempt+=1
source=r/'source-media'/f'{a.image_id}-retry{attempt:02}.png'
old_display=r/old['file']
display=r/'media'/f'{a.image_id}-retry{attempt:02}.webp'
reject_record=r/'media/records/rejected'/f'{a.image_id}-attempt{attempt:02}.json'
reject_display=r/'media/rejected'/f'{a.image_id}-attempt{attempt:02}.webp'
reject_record.parent.mkdir(parents=True,exist_ok=True);reject_display.parent.mkdir(parents=True,exist_ok=True)
assert not reject_record.exists() and not reject_display.exists()
shutil.copy2(old_display,reject_display)
archived=old.copy();archived['id']=f'{a.image_id}-attempt{attempt:02}';archived['key']=archived['id'];archived['rejected_attempt_of']=a.image_id;archived['file']=str(reject_display.relative_to(r));archived['display_sha256']=hashlib.sha256(reject_display.read_bytes()).hexdigest()
tmp=reject_record.with_suffix('.json.pilot.tmp');tmp.write_text(json.dumps(archived,indent=2)+'\n');os.replace(tmp,reject_record)
shutil.copy2(a.generated_file,source)
data=source.read_bytes();assert data[:8]==b'\x89PNG\r\n\x1a\n'
w,h=struct.unpack('>II',data[16:24])
subprocess.run(['ffmpeg','-nostdin','-y','-i',str(source),'-c:v','libwebp','-quality','95','-compression_level','6',str(display),'-loglevel','error'],check=True)
new=old.copy();new.pop('review',None)
for stale in ['native_pixel_sha256','lossless_pixel_equality_verified','source_encoding','source_format','native_pixel_identical_to_generator_png','native_source_encoding']:
 new.pop(stale,None)
new.update(file=str(display.relative_to(r)),source_file=str(source.relative_to(r)),width=w,height=h,sha256=hashlib.sha256(data).hexdigest(),display_sha256=hashlib.sha256(display.read_bytes()).hexdigest(),source_bytes=len(data),display_bytes=display.stat().st_size,generated_tool_file=a.generated_file,exact_generation_prompt=provenance['prompt'],reference_source_files=provenance['references'],approved=False,review_status='awaiting-direct-source-review',public_status='draft',alt='Pending direct review of corrected native source',caption='Generated fictional adult haircut reference; actual native dimensions recorded.')
new['generator_original_file']=str(source.relative_to(r));new['generator_original_sha256']=new['sha256'];new['generator_original_bytes']=len(data)
new['previous_attempt_records']=old.get('previous_attempt_records',[])+[str(reject_record.relative_to(r))]
tmp=record_file.with_suffix('.json.pilot.tmp');tmp.write_text(json.dumps(new,indent=2)+'\n');os.replace(tmp,record_file)
print(json.dumps({'id':a.image_id,'source_file':new['source_file'],'width':w,'height':h,'preserved_rejected_record':str(reject_record.relative_to(r))}))
