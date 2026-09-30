"""Freeze matched pixels and honest parent verdict for collar trial1."""
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

runtime = Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2')
out = Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/collar/trial1')
out.mkdir(parents=True, exist_ok=True)
if (out/'verification.json').exists():
    raise RuntimeError('Frozen report exists')
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
font = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',16)
board = Image.new('RGB',(1280,4*360),(23,26,31))
draw = ImageDraw.Draw(board)
files = []
for column, (case, mode) in enumerate([('collar-control','pbr'),('collar-trial1','pbr'),('collar-control','gray'),('collar-trial1','gray')]):
    directory = runtime/case/mode
    manifest = json.loads((directory/'manifest.json').read_text())
    (out/f'{case}-{mode}-manifest.json').write_bytes((directory/'manifest.json').read_bytes())
    for row, view in enumerate(manifest['views']):
        source = directory/view['file']
        assert sha(source) == view['sha256']
        target = out/f'{case}-{mode}-{row:04d}.png'
        target.write_bytes(source.read_bytes())
        files.append({'file':target.name,'sha256':sha(target)})
        image = Image.open(source).convert('RGB').resize((320,320),Image.Resampling.LANCZOS)
        board.paste(image,(320*column,360*row+40))
        draw.text((320*column+5,360*row+8),f'{"source" if case.endswith("control") else "REJECTED cut"} / {mode} / {view["yaw"]}°',font=font,fill='white')
board.save(out/'matched-collar.jpg',quality=95,subsampling=0)
(out/'selection.json').write_bytes((runtime/'collar-trial1/selection.json').read_bytes())
(out/'control.json').write_bytes((runtime/'collar-control/control.json').read_bytes())
verdict = {'status':'REJECTED parent collar extraction trial1; no neck assembly',
    'failedFixes':1,'verifiedFrames':files,'boardSHA256':sha(out/'matched-collar.jpg'),
    'visibleDefects':['Old dark nape/hair remnants retained above rear hood',
                     'Selected rim includes malformed old neck skin and irregular edges',
                     'Five protected body seed triangles removed when isolated components discarded'],
    'positiveFinding':'Nonplanar selection gives one111-edge boundary, preserves broad hood silhouette, no nonmanifold edges',
    'alternative':'Manually specified spatial collar contour with explicit hood/skin landmarks; texture colour alone is unreliable',
    'limits':['A single edge loop is not appearance approval','No new head sewn or local neck motion tested','Source remains untouched']}
(out/'verification.json').write_text(json.dumps(verdict,indent=2)+'\n')
print(json.dumps({k:v for k,v in verdict.items() if k!='verifiedFrames'},indent=2))
