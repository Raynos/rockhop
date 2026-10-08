"""Write matched actual-PBR review specs after the parent saves sculpt01.

No Blender, model evaluation, shader edits or render is performed.
Usage: bundled-python review_specs.py ACTUAL_REPORT FRESH_SPEC_DIRECTORY
"""
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def unit(vector):
    return vector / np.linalg.norm(vector)


def main():
    assert len(sys.argv) == 3
    report_path, out = (Path(value).resolve() for value in sys.argv[1:])
    assert out.is_relative_to(ROOT / 'docs/evidence/rider-rebuild/glove-anatomical04')
    assert not out.exists()
    report = json.loads(report_path.read_text())
    controls_path = HERE / 'controls-orientation02.json'
    controls = json.loads(controls_path.read_text())
    assert report['acceptedArt'] is False and report['controlsSHA256'] == sha(controls_path)
    assert report['status'] == 'BILATERAL_SELECTED_SCULPT_SAVED_BEFORE_PARENT_PBR_REVIEW'
    assert sha(ROOT / report['native']['path']) == report['native']['sha256']
    native = np.load(ROOT / controls['pins']['nativeArrays']['path'])
    names = native['jointNames'].tolist()
    lookup = {name: i for i, name in enumerate(names)}
    objects = ['Boots__LocallyRepairedSelectedDenseBoot.L',
               'Boots__LocallyRepairedSelectedDenseBoot.R',
               'Hoodie__ActualOriginalDensePBR_FrozenFitContext',
               'Jeans__AlignedSelectedDenseJeans']
    objects += [report['hands'][side]['object'] for side in ('R', 'L')]
    out.mkdir(parents=True)
    receipt = {'acceptedArt': False, 'actualNative': report['native'],
               'actualReportSHA256': sha(report_path), 'generatorSHA256': sha(__file__),
               'controlsSHA256': sha(controls_path), 'specs': {},
               'material': 'Unchanged genuine packed selected PBR from actual authored native.',
               'framing': 'Canonical wearer focus and fixed scales; never fitted-result bounds.',
               'limits': ['Specs only; no render executed. Stills reject gross fit, never accept moving art.']}
    for side in ('R', 'L'):
        hand = np.load(ROOT / controls['pins']['hand' + side]['path'])
        initial = controls['hands'][side]['initialPlacement']
        curls = np.asarray([row['palmCurlDirection'] for row in initial['signedMCPPalmCurlChecks']])
        dorsal = -unit(curls.mean(0))
        palm = -dorsal
        wrist = native['jointHeads'][lookup['DEF-hand.' + side]]
        middle = native['jointHeads'][lookup['DEF-f_middle.01.' + side]]
        thumb = native['jointHeads'][lookup['DEF-thumb.02.' + side]]
        radial = thumb - (wrist + middle) / 2
        radial = unit(radial - dorsal * np.dot(radial, dorsal))
        focus = (hand['vertices'].min(0) + hand['vertices'].max(0)) / 2
        cuff_focus = wrist + hand['cuffProximalAxis'] * .025
        views = {
            'hand': (focus, .30, {'anatomical-dorsal': dorsal,
                                  'anatomical-palm': palm,
                                  'thumb-web-palmar-oblique': unit(radial + palm * .45)}),
            'cuff': (cuff_focus, .15,
                     {'selected-strap-hoodie-overlap': unit(dorsal + hand['cuffProximalAxis'] * .40 + radial * .25)}),
        }
        for region, (center, scale, directions) in views.items():
            spec = {'accepted': False, 'native': report['native'], 'mode': 'stills',
                    'objects': objects, 'bodyObject': 'RiderBody', 'rigObject': 'RiderSkeleton',
                    'focus': center.tolist(), 'orthoScale': scale,
                    'views': {name: (center + unit(direction) * 2).tolist()
                              for name, direction in directions.items()},
                    'anatomicalBasis': {'side': side, 'dorsalOpposesSignedMCPPalmCurl': True,
                                        'dorsalWorld': dorsal.tolist(), 'thumbRadialWorld': radial.tolist()},
                    'preserveAllActualOutfitMeshesAndMaterials': True}
            path = out / (side + '-' + region + '.json')
            path.write_text(json.dumps(spec, indent=2) + '\n')
            receipt['specs'][side + '-' + region] = {'path': str(path.relative_to(ROOT)),
                                                    'sha256': sha(path)}
    (out / 'specs.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
