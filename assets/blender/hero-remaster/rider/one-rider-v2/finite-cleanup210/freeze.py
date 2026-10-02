"""Pin this one CPU-only literal cleanup and its untouched diagnostic lineage."""
from pathlib import Path
import json,hashlib
R=Path('/Users/raynos/projects/games/rockhop')
B=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2')
A=R/'assets/blender/hero-remaster/rider/one-rider-v2/finite-cleanup210'
E=R/'docs/evidence/hero-remaster/one-rider-v2/finite-cleanup210'
def pin(p):
    return {'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
inputs=[B/'finite-native208/ancestry.npz',B/'finite-native208/native-display.glb',B/'tpose-shape207-01/native-decoded.npz',B/'tpose-shape207-01/native-diagnostics.json',R/'assets/blender/hero-remaster/rider/one-rider-v2/finite-native208/isolate.py',R/'docs/evidence/hero-remaster/one-rider-v2/tpose-source208/finite-isolation.json']
assert all(p.is_file() for p in inputs)
report=json.loads((E/'report.json').read_text())
assert report['status']=='UNACCEPTED_LITERAL_TOPOLOGY_CLEANUP'
owned=sorted([p for directory in (A,E) for p in directory.iterdir() if p.is_file() and p.name!='freeze.json'])
outputs=sorted(p for p in (B/'finite-cleanup210').iterdir() if p.is_file())
data={'status':'FROZEN_UNACCEPTED_LITERAL_CLEANUP_ONE_CANDIDATE','geometryAttempts':1,'gpuUsed':False,'cpuThreadLimit':2,'inputPins':{str(p):pin(p) for p in inputs},'ownedFiles':{str(p):pin(p) for p in owned},'privateOutputs':{str(p):pin(p) for p in outputs},'sourceUnchanged':pin(inputs[0])['sha256']=='48907fbbbcf1b787c07363006c86d2262e463b4f9f456c52191a7b73d4b288bb' and pin(inputs[1])['sha256']=='57eef332e00089296a5078d44c8e2c6963c8214aa55257aadcee5c818048923e','constructionContract':'Merge only source finite rows 34564/34565, retain lower row; remove only exact zero-area faces 68199/68209. Retain every distinct source position and every other face incidence in original order, including tiny component. Separate display winding reversal reproduces original source export. No rest-surface editing.'}
(E/'freeze.json').write_text(json.dumps(data,indent=2)+'\n')
print(json.dumps({'freezeSHA256':pin(E/'freeze.json')['sha256'],'inputPins':len(inputs),'ownedFiles':len(owned),'privateOutputs':len(outputs),'candidateSHA256':pin(B/'finite-cleanup210/clean-native.glb')['sha256']},indent=2))
