"""Pixel-only diagnostic boards and explicit approximate landmark inventory."""
import hashlib, json, math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

REPO=Path('/Users/raynos/projects/games/rockhop')
OUT=REPO/'docs/evidence/hero-remaster/one-rider-v2/body-audit'
RUNTIME=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/body-audit')
font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',19)
groups={'hands':[f'hand-{side}-{view}' for side in ['positive','negative'] for view in ['front','profile','back']],
        'legs':['knees-front','knees-profile','shoes-front','shoes-profile'],
        'garment-back':['armpits-front','armpits-quarter','back-full','back-quarter']}
inspection=json.loads((OUT/'inspection.json').read_text())
for r in inspection['views']:
    assert hashlib.sha256(Path(r['file']).read_bytes()).hexdigest()==r['sha256']
for group,views in groups.items():
    board=Image.new('RGB',(len(views)*360,2*405),(23,26,31)); draw=ImageDraw.Draw(board)
    for row,mode in enumerate(['pbr','gray']):
        for col,view in enumerate(views):
            im=Image.open(RUNTIME/f'{view}-{mode}.png').convert('RGB'); im.thumbnail((360,360),Image.Resampling.LANCZOS)
            board.paste(im,(col*360,row*405+45)); draw.text((col*360+5,row*405+8),f'{view} / {mode}',font=font,fill='white')
    board.save(OUT/f'{group}-matched.jpg',quality=95,subsampling=0)
# These are visually placed provisional centres inside the clothed source envelope.
# No skeleton exists in this unrigged donor. Bounds/mesh metrics are measured separately.
points={'pelvis': [0,0,.94], 'shoulder.positive': [.20,0,1.41], 'elbow.positive':[.29,0,1.16],
        'wrist.positive':[.35,0,.94], 'hip.positive':[.09,0,.94], 'knee.positive':[.14,0,.50],
        'ankle.positive':[.17,0,.105], 'palm.positive':[.352,0,.855], 'sole.positive':[.17,-.06,.015]}
for name,p in list(points.items()):
    if name.endswith('.positive'): points[name.replace('.positive','.negative')]=[-p[0],p[1],p[2]]
def distance(a,b): return math.sqrt(sum((points[a][i]-points[b][i])**2 for i in range(3)))
segments={'torso': 1.41-.94,
          'upperArm':distance('shoulder.positive','elbow.positive'),'forearm':distance('elbow.positive','wrist.positive'),
          'thigh':distance('hip.positive','knee.positive'),'shin':distance('knee.positive','ankle.positive')}
physical={'torso':.52,'upperArm':.32,'forearm':.27,'thigh':.46,'shin':.43}
landmarks={'status':'provisional visible-envelope estimates; NOT final measured rig mapping',
 'basis':'1.8m display height, ground z0, body front -Y, lateral X; height includes rejected hair; hidden joint centres visually estimated',
 'uncertaintyMeters':{'lateral':.03,'vertical':.03,'depth':.05},
 'estimateMethod':'Manual inspection of calibrated orthographic front/profile images; symmetric centres are a proposed clean-bind target, not a measurement of existing bilateral anatomy.',
 'pointsBlenderZUpMeters':points,'uniform1p78ConversionFactor':1.78/1.8,
 'runtimeAdapterAxisFormula':'runtime (X,Y,Z) = (-BlenderY, BlenderZ, BlenderX); left/right sign must be verified against actual socket convention',
 'estimatedSegmentsMetersAt1p8':segments,
 'physicalSegmentsMetersUnchanged':physical,
 'provisionalRenderToPhysicsRatios':{k:physical[k]/segments[k] for k in segments},
 'sourceContract':{'boneCount':19,'boneOrder':['pelvis','spine','chest','neck','head','shoulder.L','upperArm.L','forearm.L','hand.L','shoulder.R','upperArm.R','forearm.R','hand.R','thigh.L','shin.L','foot.L','thigh.R','shin.R','foot.R'],
   'sockets':['gripSocket.L','gripSocket.R','soleSocket.L','soleSocket.R'], 'runtimeUp':'Y','runtimeForward':'X','fileAxleShiftMeters':.65},
 'limits':['No approved hidden joint centres or final anatomy lengths yet. Do not construct an adapter by treating these estimates as measured bind transforms.',
   'One uniform scale cannot preserve torso, arm, leg and hand-contact proportions simultaneously.',
   'Palm/sole points are visual labels, not valid bike-space contact measurement. Native relaxed mitten shapes cannot wrap a grip.']}
(OUT/'landmark-probes.json').write_text(json.dumps(landmarks,indent=2)+'\n')
manifest={'status':'read-only CPU inspection complete, parent judgment pending','renderFramesVerified':len(inspection['views']),
          'boards':{str(p.relative_to(OUT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.glob('*matched.jpg')},
          'sourcesUntouched':inspection['sourceSHA256']==inspection['sourceSHA256After']}
(OUT/'verification.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(manifest,indent=2))
