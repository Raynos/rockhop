"""Freeze both failed graph-cut collars against their unchanged source control."""
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

runtime = Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2')
out = Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/collar/trial2')
out.mkdir(parents=True, exist_ok=True)
if (out/'verification.json').exists():
    raise RuntimeError('Frozen report exists')
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
font = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',16)
board = Image.new('RGB',(1920,1440),(23,26,31))
draw = ImageDraw.Draw(board)
frames = []
for column, (case, mode) in enumerate([(c,m) for m in ['pbr','gray'] for c in ['collar-control','collar-trial1','collar-trial2']]):
    folder = runtime/case/mode
    manifest = json.loads((folder/'manifest.json').read_text())
    if case == 'collar-trial2':
        (out/f'{mode}-manifest.json').write_bytes((folder/'manifest.json').read_bytes())
    for row, view in enumerate(manifest['views']):
        source = folder/view['file']
        assert sha(source) == view['sha256']
        if case == 'collar-trial2':
            copied = out/f'{mode}-{row:04d}.png'
            copied.write_bytes(source.read_bytes())
        frames.append({'path':str(source),'sha256':sha(source)})
        im = Image.open(source).convert('RGB').resize((320,320),Image.Resampling.LANCZOS)
        board.paste(im,(320*column,360*row+40))
        draw.text((320*column+5,360*row+8),f'{case.replace("collar-","")} / {mode} / {view["yaw"]}°',font=font,fill='white')
board.save(out/'source-both-failures.jpg',quality=95,subsampling=0)
selection = json.loads((runtime/'collar-trial2/selection.json').read_text())
assert [v['count'] for v in selection['boundaryLoops']] == [125,41,33]
(out/'selection.json').write_bytes((runtime/'collar-trial2/selection.json').read_bytes())
verdict = {'status':'REJECTED collar trial2; graph-cut technique stopped after two failures',
    'failedFixes':2,'parentReviewed':'front/profile/rear PBR and matched gray geometry',
    'verifiedFrameInputs':frames,'boardSHA256':sha(out/'source-both-failures.jpg'),
    'visibleDefects':['Most nape hair removed but gold spike/rim remnants remain',
                     'Three boundary loops include two unintended rear hood openings',
                     'Four protected seeds lost during isolated-component filtering'],
    'nextSpecificTechnique':'Explicit local collar/rim retopology on reviewed anatomical/garment anchors; no more colour-seeded graph fixes',
    'limits':['No new head attachment','No complete character, texture/normal match, deformation or rig pass','Source bytes untouched']}
(out/'verification.json').write_text(json.dumps(verdict,indent=2)+'\n')
