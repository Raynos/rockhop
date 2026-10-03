"""Silent matched clip; labels outside two unchanged512-square render panels."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

import numpy as np
from PIL import Image,ImageDraw


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--orbit',required=True);parser.add_argument('--out',required=True)
    args=parser.parse_args();assert os.environ.get('ROCKHOP_GENERATION_CONTROLLER_PID')
    report=json.loads(Path(args.orbit).read_text());assert len(report['rows'])==48 and report['loadedArraysByteIdentical']
    out=Path(args.out).resolve();out.mkdir(parents=True,exist_ok=False)
    for row in report['rows']:
        canvas=Image.new('RGB',(1024,576),'#101319');draw=ImageDraw.Draw(canvas)
        for index,name in enumerate(('gray','pbr')):
            item=row[name];assert sha(item['path'])==item['SHA256'];panel=Image.open(item['path']).convert('RGB');assert panel.size==(512,512)
            canvas.paste(panel,(index*512,64));assert np.array_equal(np.asarray(canvas)[64:,index*512:(index+1)*512],np.asarray(panel))
        draw.text((12,8),'Pixal3D upright / documented1024 / raw6.60m triangles / seed42',fill='white')
        draw.text((12,30),'NEUTRAL / unchanged geometry',fill='white')
        draw.text((524,30),'NATIVE PBR ATTRS / vertex display derivative',fill='white')
        draw.text((12,46),f'NativeYup display / yaw{row["yawDegrees"]:.1f} / root review pending / no openings or fit proof',fill='#b6bbc5')
        canvas.save(out/f'{row["frame"]:03d}.png')
    movie=out/'pixal-neutral-pbr.mp4'
    subprocess.run(['ffmpeg','-y','-v','error','-framerate','8','-i',str(out/'%03d.png'),'-an','-c:v','libx264','-threads','2','-crf','19','-pix_fmt','yuv420p','-movflags','+faststart',str(movie)],check=True)
    probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','stream=codec_type,width,height,avg_frame_rate,nb_frames:format=duration,size','-of','json',str(movie)],text=True))
    assert len(probe['streams'])==1 and probe['streams'][0]['codec_type']=='video'
    assert probe['streams'][0]['nb_frames']=='48' and float(probe['format']['duration'])==6
    result={'accepted':False,'movie':str(movie),'SHA256':sha(movie),'bytes':movie.stat().st_size,'ffprobe':probe,
            'orbitSHA256':sha(args.orbit),'recipeSHA256':sha(__file__),'renderPixelsUnchangedBeforeEncoding':True}
    (out/'movie.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'SHA256':result['SHA256'],'bytes':result['bytes']}))


if __name__=='__main__':
    main()
