"""Freeze failed first texture transfer with matched geometry evidence."""
import argparse,hashlib,json,shutil
from pathlib import Path
from PIL import Image,ImageDraw
ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--runtime',required=True);ap.add_argument('--evidence',required=True)
a=ap.parse_args();source=Path(a.runtime);out=Path(a.evidence);out.mkdir(parents=True,exist_ok=True)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
reports={}
for name in ['transfer.json','material-application.json','uv-transfer-data.json']:
    shutil.copy2(source/name,out/name);reports[name]=json.loads((source/name).read_text())
for sub in ['pbr','gray','closeups','gray-closeups']:
    dest=out/sub;dest.mkdir(exist_ok=True)
    for p in (source/sub).glob('*'):
        if p.suffix in ['.png','.json']:shutil.copy2(p,dest/p.name)
    canvas=Image.new('RGB',(1024,1666),(20,23,26));draw=ImageDraw.Draw(canvas)
    draw.text((12,10),'FAILED texture transfer1: '+sub,fill='white')
    draw.text((12,30),'ACTUAL CPU OUTPUT | UNACCEPTED | shape unchanged',fill=(255,180,130))
    for n in range(4):
        img=Image.open(dest/f'{n:04d}.png').convert('RGB');img.thumbnail((512,768))
        x=(n%2)*512+(512-img.width)//2;y=54+(n//2)*806
        canvas.paste(img,(x,y));draw.text(((n%2)*512+12,y+776),['Front','Three-quarter','Profile','Rear'][n],fill='white')
    canvas.save(out/f'{sub}-four-views.jpg',quality=94)
report=dict(status='REJECTED by parent: first CPU texture transfer; visible corruption exposed',reports=reports,
    geometryAndUVUnchanged=reports['material-application.json']['geometryAndUVUnchanged'],
    remainingVisibleDefects=['Forehead/brow/nose color islands misregistered; lip/beard color displaced.',
        'Sharp face-to-ear/neck fallback boundary is visible in profile.',
        'Native scalp is continuous geometry but stubble albedo reads helmet-like with jagged nape line.',
        'Native brown iris/sclera now visible; full identity/appearance still unaccepted.'],
    seamReport=dict(UVPositionConflictTexels=reports['transfer.json']['UVPositionConflictTexels'],paddingPixels=6,
        appearance='UV raster conflicts0 do not measure visible semantic seams; sharp donor/fallback transition is FAIL.'),
    masters={str(p):sha(p) for p in [source/'head.blend',source/'head.glb',source/'skin-basecolor.png',source/'skin-roughness.png',source/'skin-metallic.png']},
    verifierSHA256=sha(__file__),limits=['No texture-only corruption is concealed by geometry approval.',
        'Distance/coverage count accepted samples, not correctness of donor semantic correspondence.',
        'No normal/displacement donor bake, neck join, rig, animation or gameplay acceptance.'])
(out/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'evidence':str(out),'shapeUnchanged':True}))
