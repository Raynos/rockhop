"""Diagnose zero-surface coverage from an immutable explicit evaluated mask."""
import argparse
import hashlib
import json
import os
from pathlib import Path

import numpy as np
from skimage import measure
from finite_cell_mc import finite_cell_mask


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    for name in ('field', 'pre-sentinel', 'out'):
        parser.add_argument('--' + name, required=True)
    args = parser.parse_args()
    assert os.environ.get('ROCKHOP_GENERATION_CONTROLLER_PID') == str(os.getppid())
    assert sha(args.field) == '44054a59516676c64b54454d27be1052200a20a040afa6c60d5db28cc57f95f8'
    assert sha(args.pre_sentinel) == '3ee8e76d67700efa67f9debe9c57165ce0c380da8a48f12b2f0c1c621198aa52'
    out = Path(args.out)
    assert not out.exists()
    out.mkdir(parents=True)
    field = np.load(args.field, allow_pickle=False)['logits'][0]
    with np.load(args.pre_sentinel, allow_pickle=False) as archive:
        evaluated = archive['evaluated'].copy()
        before = archive['logits'][0].copy()
    assert np.array_equal(evaluated, np.isfinite(field))
    assert np.array_equal(before[evaluated], field[evaluated])
    assert np.all(before[~evaluated] == -10000)
    field_bytes = hashlib.sha256(field.tobytes()).hexdigest()
    cell_shape = tuple(n - 1 for n in field.shape)
    known = np.zeros(cell_shape, dtype=np.uint8)
    below = np.zeros(cell_shape, dtype=bool)
    above = np.zeros(cell_shape, dtype=bool)
    zero = np.zeros(cell_shape, dtype=bool)
    for x in (0, 1):
        for y in (0, 1):
            for z in (0, 1):
                part = field[x:x + cell_shape[0], y:y + cell_shape[1], z:z + cell_shape[2]]
                valid = evaluated[x:x + cell_shape[0], y:y + cell_shape[1], z:z + cell_shape[2]]
                known += valid
                below |= valid & (part < 0)
                above |= valid & (part >= 0)
                zero |= valid & (part == 0)
    incomplete = (known > 0) & (known < 8)
    crossing_excluded = incomplete & below & above
    excluded_positions = np.argwhere(crossing_excluded)
    report = {'accepted': False, 'modelRuns': 0, 'recipeSHA256': sha(__file__),
              'fieldSHA256': sha(args.field), 'preSentinelFieldSHA256': sha(args.pre_sentinel),
              'explicitMaskMatchesFiniteField': True, 'originalEvaluatedValuesUnchanged': True,
              'unknownPreConversionValuesAreAllSentinel': True, 'fieldShape': list(field.shape),
              'cellsByKnownCornerCount': np.bincount(known.ravel(), minlength=9).tolist(),
              'incompleteCellsKnownCornersStraddleZero': int(crossing_excluded.sum()),
              'incompleteCellsWithKnownExactZero': int((incomplete & zero).sum()),
              'excludedStraddleCellSamples': excluded_positions[:32].tolist(),
              'limits': ['Unknown cells can contain unseen surfaces; absence of observed straddles is not completeness proof.',
                         'No neural resampling, field filling, component deletion or mesh cleanup.',
                         'Closed topology and finite arrays do not accept garment anatomy, materials or motion.']}
    mask, counts = finite_cell_mask(field, evaluated=evaluated)
    for name, kwargs in [('nativeUnmasked', {}), ('ownedFiniteCell', {'mask': mask})]:
        vertices, faces, normals, values = measure.marching_cubes(field, 0, method='lewiner', **kwargs)
        report[name] = {'vertices': len(vertices), 'faces': len(faces),
                        'nonfiniteVertexElements': int((~np.isfinite(vertices)).sum()),
                        'nonfiniteNormalElements': int((~np.isfinite(normals)).sum()),
                        'nonfiniteVertexValueElements': int((~np.isfinite(values)).sum())}
    report['finiteCellCounts'] = counts
    report['originalFieldCBytesUnchanged'] = hashlib.sha256(field.tobytes()).hexdigest() == field_bytes
    assert report['originalFieldCBytesUnchanged']
    (out / 'receipt.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report), flush=True)


if __name__ == '__main__':
    main()
