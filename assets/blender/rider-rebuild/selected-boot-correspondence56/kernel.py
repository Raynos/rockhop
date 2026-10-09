"""Scale-independent barycentrics; preserve the original source bearing.

Only the dimensional Gram-determinant cutoff changes. The frozen coefficient
containment tolerance and clamping remain. No triangle is removed or replaced.
"""
import ast
import hashlib
import json
from pathlib import Path

import numpy as np

ENGINE_SHA = 'bc9e03aa6d99eba0d4b5037ceff49424c34ddcde99f0f2aae0f84a5090cbc483'
OLD_CALL = 'coeff=barycentric(np.asarray(near[0]),sp[sf[tri]])'
NEW_CALL = 'coeff=correspondence56.evaluate(np.asarray(near[0]),sp[sf[tri]],tri,i)'


def barycentric(p, t):
    p = np.asarray(p, dtype=np.float64)
    t = np.asarray(t, dtype=np.float64)
    assert p.shape == (3,) and t.shape == (3, 3), 'Invalid correspondence shape'
    assert np.isfinite(p).all() and np.isfinite(t).all(), 'Nonfinite correspondence'
    a = t[1]-t[0]; b = t[2]-t[0]; q = p-t[0]
    scale = max(np.max(np.abs(a)), np.max(np.abs(b)))
    assert np.isfinite(scale) and scale > 0, 'Degenerate source correspondence triangle'
    a = a/scale; b = b/scale; q = q/scale
    cross = np.cross(a, b)
    normal_scale = np.max(np.abs(cross))
    assert normal_scale > 0, 'Degenerate source correspondence triangle'
    # Scaling the normal avoids squaring an already small area. Cross products
    # avoid the cancellation in (a.a)*(b.b)-(a.b)**2 for skinny triangles.
    normal = cross/normal_scale
    denominator = cross@normal
    v = np.cross(q, b)@normal/denominator
    w = np.cross(a, q)@normal/denominator
    result = np.array([1-v-w, v, w])
    assert np.isfinite(result).all(), 'Nonfinite source coefficients'
    assert result.min() > -1e-5, 'Outside source correspondence triangle'
    result = np.maximum(result, 0)
    return result/result.sum()


def adapted_transfer_source(raw):
    """Extract the pinned transfer verbatim and replace only its kernel call."""
    assert hashlib.sha256(raw).hexdigest() == ENGINE_SHA, 'Frozen engine25 changed'
    source = raw.decode()
    node = next(n for n in ast.parse(source).body
                if isinstance(n, ast.FunctionDef) and n.name == 'transfer')
    transfer = ''.join(source.splitlines(keepends=True)[node.lineno-1:node.end_lineno])
    assert transfer.count(OLD_CALL) == 1, 'Frozen transfer call drift'
    return transfer.replace(OLD_CALL, NEW_CALL)


class Audit:
    def __init__(self):
        self.calls = 0
        self.corrected = []
        self.failure = None

    def evaluate(self, p, t, source_face_id, target_vertex_id):
        self.calls += 1
        a = t[1]-t[0]; b = t[2]-t[0]
        old_determinant = float((a@a)*(b@b)-(a@b)*(a@b))
        row = {'sourceFaceId': int(source_face_id), 'targetVertexId': int(target_vertex_id),
               'frozenGramDeterminantM4': old_determinant}
        try:
            coeff = barycentric(p, t)
        except Exception as error:
            self.failure = dict(row, error=repr(error))
            raise
        if old_determinant <= 1e-24:
            self.corrected.append(dict(row, coefficients=coeff.tolist(),
                                       reconstructionResidualM=float(np.linalg.norm(coeff@t-p))))
        return coeff

    def report(self):
        return {'status': 'NUMERICAL_CORRESPONDENCE_ONLY_UNACCEPTED',
                'bearingPolicy': 'Original BVH nearest source triangle and point unchanged',
                'kernelCalls': self.calls, 'formerlyRejectedBearings': self.corrected,
                'kernelFailure': self.failure, 'acceptedArt': False,
                'limits': 'These IDs identify actual queried bearings, not all 78 source cutoff faces. Downstream geometry, normal, skin, contact, bake and motion gates remain required.'}


def install(engine, out):
    """Keep every frozen transfer gate; persist numerical evidence even on failure."""
    raw = Path(engine.__file__).read_bytes()
    audit = Audit()
    namespace = dict(vars(engine), correspondence56=audit)
    exec(compile(adapted_transfer_source(raw), str(engine.__file__)+'[kernel56]', 'exec'), namespace)
    frozen_transfer = namespace['transfer']

    def transfer(*args, **kwargs):
        try:
            result = frozen_transfer(*args, **kwargs)
            result['correspondenceKernel56'] = audit.report()
            return result
        finally:
            (out/'correspondence56.json').write_text(json.dumps(audit.report(), indent=2)+'\n')

    engine.transfer = transfer
