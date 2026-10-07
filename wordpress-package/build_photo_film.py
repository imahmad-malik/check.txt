#!/usr/bin/env python3
"""Build the truthful, uncropped Home photographic sequence from reviewed sources."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent
KEYS = ['home-angle-front', 'home-angle-side', 'home-angle-back']


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    rows = [json.loads((ROOT / 'media/records' / (key + '.json')).read_text()) for key in KEYS]
    for key, row in zip(KEYS, rows):
        source = ROOT / row['source_file']
        assert row['approved'] is True and row['review_status'] == 'approved', key
        assert not row['upscaled'] and row['native_original'], key
        assert source.is_file() and digest(source) == row['sha256'], key
        assert 'coherent_set' in row['review'] and row['review']['coherent_set'].startswith('pass'), key
    assert len({r['sha256'] for r in rows}) == 3
    width, height = rows[0]['width'], rows[0]['height']
    assert width % 2 == height % 2 == 0
    assert all((r['width'], r['height']) == (width, height) for r in rows)
    target = ROOT / 'video/home-motion-film.mp4'
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name('home-motion-film.tmp.mp4')
    command = ['ffmpeg', '-nostdin', '-y', '-hide_banner', '-loglevel', 'error']
    for row, duration in zip(rows + [rows[0]], [4.4, 4.4, 4.4, 0.8]):
        command += ['-loop', '1', '-framerate', '24', '-t', str(duration), '-i', str(ROOT / row['source_file'])]
    filters = []
    for i in range(4):
        filters.append(f'[{i}:v]format=yuv420p,setsar=1,settb=AVTB[v{i}]')
    filters += ['[v0][v1]xfade=transition=fade:duration=0.8:offset=3.6[s1]',
                '[s1][v2]xfade=transition=fade:duration=0.8:offset=7.2[s2]',
                '[s2][v3]xfade=transition=fade:duration=0.8:offset=10.8[out]']
    command += ['-filter_complex', ';'.join(filters), '-map', '[out]', '-an', '-c:v', 'libx264',
                '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', '-movflags', '+faststart',
                '-threads', '2', str(temporary)]
    subprocess.run(command, check=True)
    metadata = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(temporary)]))
    video = next(s for s in metadata['streams'] if s['codec_type'] == 'video')
    assert video['codec_name'] == 'h264' and (video['width'], video['height']) == (width, height)
    assert not any(s['codec_type'] == 'audio' for s in metadata['streams'])
    assert 11 < float(metadata['format']['duration']) < 12
    subprocess.run(['ffmpeg', '-v', 'error', '-i', str(temporary), '-f', 'null', '-'], check=True)
    temporary.replace(target)
    row = {'id': 'home-motion-film', 'key': 'home-motion-film', 'usage': 'homepage-film',
           'source_file': 'video/home-motion-film.mp4', 'file': 'video/home-motion-film.mp4',
           'sha256': digest(target), 'display_sha256': digest(target), 'width': width, 'height': height,
           'source_bytes': target.stat().st_size, 'display_bytes': target.stat().st_size,
           'duration_seconds': float(metadata['format']['duration']), 'native_original': True,
           'native_8k': False, 'upscaled': False, 'generated': False, 'fictional_adult': True,
           'approved': True, 'review_status': 'approved', 'public_status': 'draft',
           'multiview': True, 'source_keys': KEYS, 'source_asset_keys': KEYS, 'source_angles': ['front', 'side', 'back'],
           'sources': [{'key': key, 'angle': angle, 'sha256': source['sha256']} for key, angle, source in zip(KEYS, ['front', 'side', 'back'], rows)],
           'alt': 'Front, side and back photographic sequence of a layered bixie haircut.',
           'caption': 'Three photographs, one haircut: fringe, crown and nape.',
           'provenance': 'Silent native-dimension H.264 photographic sequence made from three separate reviewed generated originals. It is not filmed salon footage.',
           'review': {'method': 'Direct review of all three source photographs; ffprobe actual stream dimensions, complete FFmpeg decode and separate browser playback verification.',
                      'framing': 'pass: full native frames, no crop, zoom or enlargement',
                      'sources': 'pass: three reviewed distinct native originals with coherent hair, adult, clothing and lighting',
                      'native_detail': 'H.264 delivery encode, CRF18; decoded photographic sources remain downloadable separately',
                      'browser_playback': 'pending actual WordPress autoplay/pause and decoded-frame check'}}
    record = ROOT / 'media/records/home-motion-film.json'
    record.write_text(json.dumps(row, indent=2) + '\n')
    print(json.dumps({'key': row['key'], 'bytes': row['source_bytes'], 'dimensions': [width, height], 'duration_seconds': row['duration_seconds'], 'sha256': row['sha256']}))


if __name__ == '__main__':
    main()
