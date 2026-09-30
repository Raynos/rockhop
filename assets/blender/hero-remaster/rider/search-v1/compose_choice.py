"""Choice boards from unchanged renders; resize/label only, no body retouch."""
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

REPO = Path(__file__).resolve().parents[5]
ROOT = Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/rendered')
OUT = REPO / 'docs/evidence/hero-remaster/rider-search-v1/choice'
OUT.mkdir(parents=True, exist_ok=True)
font = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 23)
records = []

def board(name, entries, columns):
    image = Image.new('RGB', (512 * columns, 848 * ((len(entries) + columns - 1) // columns)), (24, 27, 31))
    draw = ImageDraw.Draw(image)
    for i, (path, label) in enumerate(entries):
        source = Image.open(path).convert('RGB')
        assert source.size == (512, 768)
        x, y = (i % columns) * 512, (i // columns) * 848
        image.paste(source, (x, y + 80))
        draw.multiline_text((x + 12, y + 10), label, font=font, fill='white')
    output = OUT / name
    image.save(output, quality=95, subsampling=0)
    records.append({'file': name, 'sha256': hashlib.sha256(output.read_bytes()).hexdigest(),
                    'sources': [{'path': str(p), 'label': label,
                                 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p, label in entries]})

board('six-options.jpg', [
    (ROOT / 'hunyuan21/01/working/0000.png', 'H21-1 / first design'),
    (ROOT / 'hunyuan21/02/working/0000.png', 'H21-2 / broader body'),
    (ROOT / 'hunyuan21/03/working/0000.png', 'H21-3 / compact body'),
    (ROOT / 'hunyuan21/04/working/0000.png', 'H21-4 / RECOMMENDED\nNext refinement; still unaccepted'),
    (ROOT / 'hunyuan21/05/working/0000.png', 'H21-5 / slimmer body'),
    (ROOT / 'pixal/03/working/0000.png', 'P3 / UNCHANGED ORIGINAL\nTwo repair attempts failed'),
], 3)
board('h21-4-p3-front-back.jpg', [
    (ROOT / 'hunyuan21/04/working/0000.png', 'H21-4 / front'),
    (ROOT / 'pixal/03/working/0000.png', 'P3 ORIGINAL / front'),
    (ROOT / 'hunyuan21/04/working/0018.png', 'H21-4 / back'),
    (ROOT / 'pixal/03/working/0018.png', 'P3 ORIGINAL / back'),
], 2)
(OUT / 'layout.json').write_text(json.dumps({'status': 'unaccepted raw-body direction choice',
    'files': records, 'limits': ['Unchanged source pixels, layout only',
    'Same normalized height/camera/light; generator settings differ',
    'Unskinned raw body; no standing-to-sitting or riding acceptance',
    'P3 original remains intact; its failed repairs are separate evidence']}, indent=2) + '\n')
print('Saved six options and matched front/back choice boards')
