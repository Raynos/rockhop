"""Independent matrix accumulation for the raised body02 witness, no Blender save."""
import ast,gzip,hashlib,json
from pathlib import Path
import numpy as np
root=Path(__file__).resolve().parents[5]
folder=root/'harness/out/rider-finish/body02-intake02'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
report=json.loads((folder/'report.json').read_text())
for p,h in report['sourcePins'].items():assert sha(p)==h
assert sha(root/'harness/rider-finish/native-sample.py')==report['recipeSHA256']
for pin in [report['rest'],*report['samples']]:assert sha(folder/pin['path'])==pin['sha256']
rest=json.loads(gzip.decompress((folder/report['rest']['path']).read_bytes()))
sample=json.loads(gzip.decompress((folder/'sample-0157.json.gz').read_bytes()))
rig=np.array(rest['rigWorldRows']);skin=np.array(sample['skinNativeRows']);rows={}
# Explicit scalar-product accumulation avoids host BLAS warning artifacts.
transform=lambda matrix,points:(points[:,None,:]*matrix[None,:,:]).sum(axis=2)
for region,part in rest['parts'].items():
    coords=np.c_[np.array(part['xyz']),np.ones(len(part['xyz']))]
    coords=transform(np.linalg.inv(rig),transform(np.array(part['objectWorld']),coords));assert np.isfinite(coords).all()
    result={}
    for kind in ['full','four']:
        weights=np.array(part[kind+'Weights']);assert np.max(abs(weights.sum(1)-1))<1e-12
        predicted=np.zeros_like(coords)
        for j in range(51):predicted+=transform(skin[j],coords)*weights[:,j,None]
        assert np.isfinite(predicted).all()
        actual=np.array(sample['parts'][region][kind]['xyzWorld'])
        residual=np.linalg.norm(transform(rig,predicted)[:,:3]-actual,axis=1)
        assert residual.max()<5e-7
        result[kind+'ResidualM']=float(residual.max())
    full=np.array(sample['parts'][region]['full']['xyzWorld']);four=np.array(sample['parts'][region]['four']['xyzWorld'])
    loss=np.linalg.norm(full-four,axis=1);result.update(fullFourLossM=float(loss.max()),worstVertex=int(loss.argmax()))
    rows[region]=result
assert rows['head']['worstVertex']==43762
assert abs(rows['head']['fullFourLossM']-.020044278475262585)<1e-12
assert sha(report['idleExport']['path'])==report['idleExport']['sha256']
for p in ['harness/rider-finish/native-sample.py',str(Path(__file__).relative_to(root))]:ast.parse((root/p).read_text())
output={'status':'PARENT_INPUT_PINS_AND_RAISED_MATRIX_READBACK_PASS_NOT_ART_ACCEPTANCE','reportSHA256':sha(folder/'report.json'),'verifiedSnapshots':len(report['samples']),'independentMatrixSample':157,'regions':rows,'recipeSHA256':sha(__file__),'limits':['Only raised sample independently reaccumulated; remaining samples pin checked, not independent matrix recomputations.','Native/manual agreement and preserved original34objects do not qualify four-weight loss, contacts, support, natural animation or art.']}
Path(__file__).with_suffix('.json').write_text(json.dumps(output,indent=2)+'\n');print(json.dumps(output))
