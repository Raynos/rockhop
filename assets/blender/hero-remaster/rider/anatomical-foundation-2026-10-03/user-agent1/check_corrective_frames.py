"""All shared source surfaces must remain inside both native review cameras."""
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np

ap = argparse.ArgumentParser(description=__doc__)
for n in ['driver', 'expanded', 'output']:
    ap.add_argument('--' + n, required=True)
a = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else None)
dp, ep, output = Path(a.driver).resolve(), Path(a.expanded).resolve(), Path(a.output).resolve()
driver, expanded = json.loads(dp.read_text()), json.loads(ep.read_text())
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(dp) == expanded['poseDriverSHA256']
meshes = []
for row in driver['meshRows']:
    if row['region'] not in ['body', 'cloth', 'jeans']:
        continue
    original = dp.parent / (row['region'] + '-native-four.f64')
    assert sha(original) == driver['pins'][original.name]['sha256']
    variants = [('before', original)]
    if row['region'] == 'body':
        variants.append(('after', original))
    else:
        corrected = ep.parent / (row['region'] + '-corrective-native-four.f64')
        assert sha(corrected) == expanded['pins'][corrected.name]['sha256']
        variants.append(('after', corrected))
    for variant, path in variants:
        data = np.memmap(path, dtype='<f8', mode='r', shape=(len(driver['frames']), row['vertices'], 3))
        meshes.append((row['region'], variant, data))
views = []
for name, yaw in [('front3q', -45), ('rear3q', -135)]:
    angle = math.radians(yaw); cosine, sine = math.cos(angle), math.sin(angle)
    right = np.array([-sine, cosine, 0]); back = np.array([cosine, sine, 0])
    camera = np.array([.65 + 4 * cosine, 4 * sine, 1.2]); rows = []
    for region, variant, data in meshes:
        low, high = np.full(3, np.inf), np.full(3, -np.inf)
        for frame in data:
            blender = np.column_stack((frame[:, 0], -frame[:, 2], frame[:, 1])) - camera
            local = np.column_stack((blender @ right, blender[:, 2], blender @ back))
            low, high = np.minimum(low, local.min(0)), np.maximum(high, local.max(0))
        inside = bool(low[0] > -.95 and high[0] < .95 and low[1] > -1.425 and high[1] < 1.425 and high[2] < -.1)
        assert inside, (name, region, variant, low, high)
        rows.append({'region': region, 'variant': variant, 'cameraLocalMinM': low.tolist(), 'cameraLocalMaxM': high.tolist(),
            'all529FramesInside': inside, 'minimumBorderM': float(min(low[0] + .95, .95 - high[0], low[1] + 1.425, 1.425 - high[1]))})
    views.append({'name': name, 'yawDegrees': yaw, 'rows': rows})
report = {'status': 'UNACCEPTED native review framing verified; no clipping/art/fit acceptance inference',
    'framingRecipeSHA256': sha(__file__), 'driverSHA256': sha(dp), 'expandedDriverSHA256': sha(ep), 'frames': len(driver['frames']),
    'camera': {'targetBlenderM': [.65, 0, 1.2], 'distanceM': 4, 'orthoHorizontalM': 1.9, 'orthoVerticalM': 2.85, 'panel': [512, 768]},
    'views': views, 'limits': ['Bounds cover whole frozen body including all hands and both original/corrected garments at529samples.',
        'Discrete geometric framing is not continuous clearance, supportedbike motion, physicaldevice or art judgment.']}
output.write_text(json.dumps(report, indent=2) + '\n')
print('CORRECTIVE_FRAMING', min(row['minimumBorderM'] for view in views for row in view['rows']), flush=True)
