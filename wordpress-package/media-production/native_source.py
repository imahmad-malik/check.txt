import argparse,hashlib,json,subprocess,os
from pathlib import Path
parser=argparse.ArgumentParser();parser.add_argument('image_id');args=parser.parse_args()
root=Path(os.environ.get('BIXIE_PACKAGE_ROOT',Path(__file__).resolve().parents[1]))
record_path=root/'media/records'/f'{args.image_id}.json'
row=json.loads(record_path.read_text())
generator_rel=row.get('generator_original_file') or row['source_file']
if not generator_rel.endswith('.png'):raise SystemExit('Missing portable generator-original PNG path')
png=root/generator_rel
original=png.read_bytes();original_sha=hashlib.sha256(original).hexdigest()
native_rel=str(Path(generator_rel).with_name(Path(generator_rel).stem+'-native.webp'))
native=root/native_rel
if not native.is_file():
    temporary=native.with_name(native.name+'.tmp.webp')
    subprocess.run(['ffmpeg','-nostdin','-y','-i',str(png),'-c:v','libwebp','-lossless','1','-quality','25','-compression_level','3',str(temporary),'-loglevel','error'],check=True)
    temporary.replace(native)
def pixel_sha(path):
    pixels=subprocess.check_output(['ffmpeg','-v','error','-i',str(path),'-f','rawvideo','-pix_fmt','rgb24','-'])
    return hashlib.sha256(pixels).hexdigest()
png_pixel=pixel_sha(png);native_pixel=pixel_sha(native)
if png_pixel!=native_pixel:raise SystemExit('Lossless source pixels differ; source PNG remains authoritative')
fresh=json.loads(record_path.read_text())
fresh_generator=fresh.get('generator_original_file') or fresh['source_file']
if fresh_generator!=generator_rel:raise SystemExit('Source changed during conversion; rerun on current record')
if hashlib.sha256(png.read_bytes()).hexdigest()!=original_sha:raise SystemExit('Original bytes changed during conversion; rerun')
fresh.update({'generator_original_file':generator_rel,'generator_original_sha256':original_sha,'generator_original_bytes':len(original),'source_file':native_rel,'sha256':hashlib.sha256(native.read_bytes()).hexdigest(),'source_bytes':native.stat().st_size,'native_pixel_sha256':native_pixel,'native_pixel_identical_to_generator_png':True,'native_original':True,'upscaled':False,'native_8k':False,'native_source_encoding':'lossless WebP; decoded RGB pixels identical to generator PNG'})
tmp=record_path.with_suffix('.json.tmp');tmp.write_text(json.dumps(fresh,indent=2)+'\n');tmp.replace(record_path)
print(json.dumps({'id':args.image_id,'source_file':native_rel,'generator_original_file':generator_rel,'pixel_identical':True,'png_bytes':len(original),'native_bytes':native.stat().st_size}))
