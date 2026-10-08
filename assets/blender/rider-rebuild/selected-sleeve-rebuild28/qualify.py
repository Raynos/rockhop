"""One parent-guarded actual static relation per process; no authoring/export.

Invoke after author.py with CONSTRUCTION_JSON RELATION. Full native triangle
checks fail on inherited degenerates too. Static results never qualify motion.
"""
import hashlib
import json
import runpy
import sys
from pathlib import Path
import bpy
import numpy as np

ROOT = Path(__file__).resolve().parents[4]
RELATIONS = ('hoodie-full-wearer', 'hoodie-self', 'hoodie-glove-L', 'hoodie-glove-R',
             'glove-L-full-wearer', 'glove-R-full-wearer')


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        while b := f.read(1048576): h.update(b)
    return h.hexdigest()


def pin(row):
    p = ROOT/row['path']; assert sha(p) == row['sha256'], row
    return p


def main():
    args = sys.argv[sys.argv.index('--')+1:]; assert len(args) == 2
    receipt_path = Path(args[0]).resolve(); relation = args[1]; assert relation in RELATIONS
    assert receipt_path.is_relative_to(ROOT/'harness/out/rider-rebuild/selected-sleeve-rebuild28')
    report = json.loads(receipt_path.read_text()); assert not report['acceptedArt']
    out = receipt_path.parent/('dense-'+relation+'.json'); assert not out.exists()
    config = json.loads(pin(report['sourcePins']['cuffInput']).read_text())
    base = json.loads(pin(config['baseInput']).read_text())
    helper_path = pin(base['intersectionHelper']); helper = runpy.run_path(str(helper_path))
    bpy.ops.wm.open_mainfile(filepath=str(pin(report['native'])), use_scripts=False)
    rig = bpy.data.objects['RiderSkeleton']; assert all(b.matrix_basis.is_identity for b in rig.pose.bones)
    names = {'hoodie': 'RiderHoodie', 'full-wearer': 'RiderBody__FullAnatomyReference',
             'glove-L': 'ActualSelectedGlove.L', 'glove-R': 'ActualSelectedGlove.R'}
    arrays = {key: (helper['points'](bpy.data.objects[name])[1], helper['faces'](bpy.data.objects[name]))
              for key, name in names.items()}
    if relation == 'hoodie-self': result = helper['intersections'](*arrays['hoodie'])
    elif relation.startswith('hoodie-'): result = helper['intersections'](*arrays['hoodie'], *arrays[relation[7:]])
    else: result = helper['intersections'](*arrays[relation[:7]], *arrays['full-wearer'])
    row = {'acceptedArt': False, 'relation': relation, 'sourceNative': report['native'],
           'recipeSHA256': sha(__file__), 'actualIntersectionHelper': base['intersectionHelper'],
           'fullTrianglesNoRadialCrop': True, 'result': result,
           'status': 'PASS_SINGLE_STATIC_RELATION' if result['passed'] else 'REJECTED_ACTUAL_TRIANGLE_RELATION',
           'poseEnclosurePassed': False, 'movingReviewPassed': False}
    out.write_text(json.dumps(row, indent=2)+'\n')
    available = {name: receipt_path.parent/('dense-'+name+'.json') for name in RELATIONS}
    complete = all(path.is_file() for path in available.values())
    if complete:
        results = {name: json.loads(path.read_text()) for name, path in available.items()}
        assert all(r['sourceNative'] == report['native'] for r in results.values())
        passed = all(r['result']['passed'] for r in results.values())
        aggregate = {'acceptedArt': False, 'sourceNative': report['native'], 'completeStaticRelations': True,
                     'staticTriangleRelationsPassed': passed, 'poseEnclosurePassed': False,
                     'movingReviewPassed': False, 'relations': {n: {'path': str(p.relative_to(ROOT)), 'sha256': sha(p)} for n, p in available.items()}}
        (receipt_path.parent/'dense-summary.json').write_text(json.dumps(aggregate, indent=2)+'\n')
    print(json.dumps({'output': str(out.relative_to(ROOT)), 'status': row['status'], 'allStaticRelationsRun': complete}), flush=True)


if __name__ == '__main__': main()
