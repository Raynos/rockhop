"""Freeze actual direct native skin views and immutable geometry/UV proof."""
import argparse,hashlib,json,shutil
from pathlib import Path
from PIL import Image,ImageDraw
ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--runtime',required=True);ap.add_argument('--evidence',required=True)
a=ap.parse_args();source=Path(a.runtime);out=Path(a.evidence);out.mkdir(parents=True,exist_ok=True)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
application=json.loads((source/'material-application.json').read_text())
shutil.copy2(source/'material-application.json',out/'material-application.json')
for sub in ['pbr','gray','closeups']:
    dest=out/sub;dest.mkdir(exist_ok=True)
    for p in (source/sub).glob('*'):
        if p.suffix in ['.png','.json']:shutil.copy2(p,dest/p.name)
    canvas=Image.new('RGB',(1024,1666),(20,23,26));draw=ImageDraw.Draw(canvas)
    draw.text((12,10),'Direct native UV skin fallback: '+sub,fill='white')
    draw.text((12,30),'ACTUAL CPU OUTPUT | appearance pending | geometry unchanged',fill=(255,180,130))
    for n in range(4):
        img=Image.open(dest/f'{n:04d}.png').convert('RGB');img.thumbnail((512,768))
        x=(n%2)*512+(512-img.width)//2;y=54+(n//2)*806
        canvas.paste(img,(x,y));draw.text(((n%2)*512+12,y+776),['Front','Three-quarter','Profile','Rear'][n],fill='white')
    canvas.save(out/f'{sub}-four-views.jpg',quality=94)
report=dict(status='UNACCEPTED final appearance; clean direct native fallback for parent review',
    application=application,geometryAndUVUnchanged=application['geometryAndUVUnchanged'],
    mapping='Exact installed native UVMap compatibility; no donor distances, coverage, or nearest-coordinate warp apply.',
    observed=['Clean natural face: no previous forehead/nose camouflage islands or sharp face-side transition.',
        'Native iris/sclera, lip and ear details aligned; natural native scalp has painted short stubble.',
        'Skin is pale, stubble light, eyebrows weak versus approved olive/dark-haired target.',
        'Native face shape and diffuse identity differ from approved Pixal/reference; exact likeness not established.',
        'Temporary neck base jagged and unjoined; source atlas may contain baked photographic shading.',
        'Native diffuse only; roughness/metallic authored constants, no normal or full PBR map set.'],
    masters={str(p):sha(p) for p in [source/'head.blend',source/'head.glb']},
    verifierSHA256=sha(__file__),failurePreservation='Two manual fit failures remain stopped; first Pixal attribute transfer failed and remains frozen.',
    limits=['No claim of successful Pixal texture/detail bake.',
        'No shape/UV/source-image edits; unchanged hashes are not final appearance acceptance.',
        'No neck join, rig, animation, moving contact, garage or game-ready approval.'])
assert application['geometryBefore']==application['geometryAfter']
(out/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'evidence':str(out),'shapeAndUVUnchanged':True}))
