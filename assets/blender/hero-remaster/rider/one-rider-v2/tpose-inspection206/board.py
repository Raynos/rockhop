"""Compose existing actual gray renders, without changing source views."""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

parser = argparse.ArgumentParser()
parser.add_argument('--report', type=Path, required=True)
parser.add_argument('--extension', type=Path, required=True)
a = parser.parse_args()
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
report = json.loads(a.report.read_text())
assert report['status'] == 'COMPLETE_UNACCEPTED_RAW_STRUCTURAL_INSPECTION'
views = {v['label']: v for v in report['views']}
labels = ['front', 'front-left', 'left', 'rear-left', 'rear', 'rear-right', 'right', 'front-right', 'upper-front']
out = a.report.parent / 'diagnostic-nine-board.png'
assert not out.exists() and not a.extension.exists()
board = Image.new('RGB', (1200, 1320), (30, 30, 30))
draw = ImageDraw.Draw(board)
font = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 18)
draw.text((12, 8), 'FINITE SUBSET DIAGNOSTIC — UNRIGGED — NO ART / POSE PASS', fill='white', font=font)
for i, label in enumerate(labels):
    item = views[label]
    p = Path(item['path'])
    assert sha(p) == item['sha256']
    x, y = (i % 3) * 400, 40 + (i // 3) * 425
    board.paste(Image.open(p).convert('RGB').resize((400, 400), Image.Resampling.LANCZOS), (x, y))
    draw.text((x + 10, y + 400), label + (' (detail crop)' if label == 'upper-front' else ''), fill='white', font=font)
board.save(out)
extension = {'status': 'DIAGNOSTIC_ONLY_NO_ACCEPTANCE', 'sourceKind': report['sourceKind'], 'sourceSHA256': report['sourceSHA256'], 'reportPin': {str(a.report): sha(a.report)}, 'boardRecipePin': {str(Path(__file__).resolve()): sha(__file__)}, 'boardPin': {str(out): sha(out)}, 'sourceViewPins': {views[label]['path']: views[label]['sha256'] for label in labels}, 'labels': labels, 'limits': 'Eight full-body camera angles and one explicitly labeled upper-front detail crop. This is not a nine-angle acceptance gate, deformation motion, textured output or native-generation success.'}
a.extension.write_text(json.dumps(extension, indent=2) + '\n')
print(str(out))
