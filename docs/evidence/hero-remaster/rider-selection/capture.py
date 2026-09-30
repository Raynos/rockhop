import json, subprocess, sys
from pathlib import Path
root = Path('harness/out/hero-remaster/rider-selection')
for item in json.loads((root/'inventory.json').read_text()):
    if item['board'] != sys.argv[1]:
        continue
    subprocess.run(['pnpm','exec','tsx','harness/hero-remaster/review.mts',
        '--build='+str(root/(item['board']+'-build')),
        '--out='+str(root/item['id']), '--outfit='+item['slot'],
        '--size=1280x720','--dpr=1','--frames=30'], check=True)
