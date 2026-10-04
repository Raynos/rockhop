"""CPU-only recovery of retained finite-cell outputs after provenance failure."""
import argparse, hashlib, inspect, json, os, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import numpy as np
from finite_cell_mc import extract
from audit_native import audit

ADAPTER_SHA = 'fd56f9211c61a99f0f517ee9598102ff1507a0006f016f354762ba6045ddb014'
def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(8 * 1024 * 1024), b''): h.update(block)
    return h.hexdigest()

def main():
    ap = argparse.ArgumentParser()
    for key in ('prior', 'checkpoint', 'out'): ap.add_argument('--' + key, required=True)
    a = ap.parse_args()
    assert os.environ.get('ROCKHOP_GENERATION_CONTROLLER_PID') == str(os.getppid())
    prior, out = Path(a.prior), Path(a.out)
    assert not out.exists()
    pins = json.loads(Path(a.checkpoint).read_text())
    assert pins['phase'] == 'decode01' and pins['guardExitCode'] == 1
    for row in pins['rawFiles']:
        assert sha(row['path']) == row['sha256'], row['path']
    adapter = Path(inspect.getfile(extract))
    assert sha(adapter) == ADAPTER_SHA
    report = json.loads((prior / 'progress.json').read_text())
    assert report['stage'] == 'native replay saved'
    assert all(report['nativeReplayEquality'].values())
    assert report['allEvaluatedNeuralBatchesFinite'] and report['newSamplerRuns'] == 0
    with np.load(prior / 'native-replayed.npz', allow_pickle=False) as replay, np.load(
            '.tmp/generation-comparison-2026-10-03/user-agent2/items01/jeans/shape01/native.npz', allow_pickle=False) as raw:
        for key in ('vertices', 'faces'):
            assert replay[key].shape == raw[key].shape and replay[key].dtype == raw[key].dtype
            assert replay[key].tobytes() == raw[key].tobytes()
    with np.load(prior / 'actual-field.npz', allow_pickle=False) as f: field = f['logits'].copy()
    with np.load(prior / 'actual-pre-sentinel-field.npz', allow_pickle=False) as f:
        mask, presentinel = f['evaluated'].copy(), f['logits'].copy()
    assert np.array_equal(mask, np.isfinite(field[0]))
    assert np.array_equal(presentinel[0][mask], field[0][mask])
    field_bytes = hashlib.sha256(field.tobytes()).hexdigest()
    assert field_bytes == report['fieldCBytesSHA256']
    with np.load(prior / 'finite-cell-derived.npz', allow_pickle=False) as f:
        vertices, faces = f['vertices'].copy(), f['faces'].copy()
    started = time.monotonic()
    grid, reproduced_faces, counts = extract(field[0], level=0., evaluated=mask)
    reproduced_vertices = (grid / [385] * [2.02] - [1.01]).astype(np.float32)
    assert reproduced_vertices.tobytes() == vertices.tobytes()
    assert reproduced_faces.tobytes() == faces.tobytes()
    assert hashlib.sha256(field.tobytes()).hexdigest() == field_bytes
    derived_audit = audit(vertices, faces)
    assert derived_audit['validGeometryArrays']
    out.mkdir(parents=True)
    import trimesh
    trimesh.Trimesh(vertices=vertices.copy(), faces=faces[:, ::-1].copy(), process=False).export(out / 'finite-cell-display.glb')
    report.update(stage='retained finite-cell source exported; root review pending',
                  recoveryRecipeSHA256=sha(__file__), failedRecipeSHA256=report['recipeSHA256'],
                  failedCheckpointSHA256=sha(a.checkpoint), priorRoot=str(prior),
                  recoveryNewSamplerRuns=0, recoveryDecoderRuns=0,
                  recoveryCPUExtractionReproductionByteExact=True, fieldBytesUnchanged=True,
                  derivedAudit=derived_audit, finiteCellCounts=counts,
                  adapterPath=str(adapter), adapterSHA256=ADAPTER_SHA,
                  derivedSHA256=sha(prior / 'finite-cell-derived.npz'), elapsedSeconds=time.monotonic()-started,
                  displayDerivative={'path':str(out / 'finite-cell-display.glb'), 'SHA256':sha(out / 'finite-cell-display.glb'),
                                     'method':'Original official global winding reversal; no repair/reduction', 'accepted':False})
    (out / 'receipt.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({'stage': report['stage'], 'mesh': report['derivedSHA256'], 'vertices':len(vertices), 'triangles':len(faces), 'newModelRuns':0}), flush=True)

if __name__ == '__main__': main()
