"""Frozen old averaged frames versus same-angle flat/derived normal renders."""
import argparse,hashlib,json,os,subprocess
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--out',required=True);args=parser.parse_args()
    assert os.environ.get('ROCKHOP_GENERATION_CONTROLLER_PID')
    root=Path.cwd();base=root/'.tmp/generation-comparison-2026-10-03/user-agent2'
    out=Path(args.out);out.mkdir(parents=True,exist_ok=False);frames=out/'frames';frames.mkdir()
    cases=[];reports=[]
    for family,old in [('trellis','qualified-trellis-upright01'),('pixal','qualified-pixal-orbit01')]:
        original=base/old/'orbit';render=base/'qualified-trellis-surface01'/('causal-'+family+'01')/'orbit'
        old_report=json.loads((original/'orbit.json').read_text());new_report=json.loads((render/'orbit.json').read_text())
        assert new_report['frozenArchivesStillExact'] and len(new_report['rows'])==49
        assert new_report['blender']==old_report['blender']
        old_pixels=np.array(Image.open(original/'frames/000-gray.png').convert('RGB'))
        replica=np.array(Image.open(render/'frames/000-raw-replica.png').convert('RGB'))
        delta=np.abs(old_pixels.astype(np.int16)-replica.astype(np.int16))
        # Baseline mismatch invalidates a causal claim; retain actual result.
        reports.append({'family':family,'oldOrbitSHA256':sha(original/'orbit.json'),'renderReportSHA256':sha(render/'orbit.json'),
                        'rawReplicaPixelsExact':bool(np.array_equal(old_pixels,replica)),
                        'rawReplicaMaximumRGBDifference':int(delta.max()),'rawReplicaMeanAbsoluteRGBDifference':float(delta.mean()),
                        'conditions':new_report['conditions'],'angleDeltas':[]})
        cases.append((family,original,render,old_report,new_report))
    for frame in range(24):
        canvas=Image.new('RGB',(1536,1152),(18,21,28));draw=ImageDraw.Draw(canvas)
        for row,(family,original,render,old_report,new_report) in enumerate(cases):
            titles=['Raw averaged normals','Raw faces / flat normals','Bounded orientation / averaged']
            images=[]
            for column,condition in enumerate(['gray','flat','derived']):
                path=(original/'frames'/f'{frame*2:03d}-gray.png') if column==0 else render/'frames'/f'{frame:03d}-{condition}.png'
                recorded=old_report['rows'][frame*2]['gray']['SHA256'] if column==0 else next(r['SHA256'] for r in new_report['rows'] if r['condition']==condition and r['frame']==frame)
                assert sha(path)==recorded
                im=Image.open(path).convert('RGB');assert im.size==(512,512);images.append(np.array(im))
                x,y=column*512,row*576;canvas.paste(im,(x,y+64))
                draw.text((x+12,y+7),family.upper()+' | '+titles[column],fill=(238,238,245))
                subtitle=('Frozen baseline | '+str(frame*15)+' degrees') if column==0 else ('Positions + face sets + materials unchanged' if column==1 else ('Contradictory faces kept: '+str(new_report['orientationLimits']['contradictoryFacesUnchanged'])))
                draw.text((x+12,y+29),subtitle,fill=(180,189,204))
                if column==2:draw.text((x+12,y+46),'Open patches use native sign; no global repair',fill=(235,186,101))
            angle={'frame':frame,'yawDegrees':frame*15}
            for label,index in [('flat',1),('derived',2)]:
                d=np.abs(images[0].astype(np.int16)-images[index].astype(np.int16))
                angle[label]={'changedPixels':int(np.any(d,axis=2).sum()),'meanAbsoluteRGBDifference':float(d.mean()),'maximumRGBDifference':int(d.max())}
            reports[row]['angleDeltas'].append(angle)
        canvas.save(frames/f'{frame:03d}.png')
    movie=out/'causal-normal-comparison.mp4'
    subprocess.run(['ffmpeg','-v','error','-framerate','4','-i',str(frames/'%03d.png'),'-an','-c:v','libx264','-crf','16','-pix_fmt','yuv420p','-movflags','+faststart',str(movie)],check=True)
    probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(movie)],text=True))
    assert len(probe['streams'])==1 and probe['streams'][0]['codec_type']=='video'
    stream=probe['streams'][0];assert int(stream['nb_frames'])==24 and (stream['width'],stream['height'])==(1536,1152)
    receipt={'accepted':False,'recipeSHA256':sha(__file__),'movieSHA256':sha(movie),'movieBytes':movie.stat().st_size,
             'fps':4,'frames':24,'seconds':6,'resolution':[1536,1152],'audioStreams':0,
             'baselineReproductionPass':all(r['rawReplicaPixelsExact'] for r in reports),'comparisons':reports,
             'limits':['Image deltas prove actual display changes, not a spatial attribution of every contour band.',
                       'Contradictory and native-anchored open patches prevent a whole-garment winding-only test.',
                       'Pixal is documented1024 alternative; prior1536 memory stop remains explicit. Hunyuan stays selected.']}
    (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({k:v for k,v in receipt.items() if k!='comparisons'}))

if __name__=='__main__':main()
