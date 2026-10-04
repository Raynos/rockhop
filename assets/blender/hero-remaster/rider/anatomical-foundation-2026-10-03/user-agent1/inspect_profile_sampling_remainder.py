"""Record the surviving fixed-resolution pair without modifying the donor."""
import argparse, hashlib, json, sys
from pathlib import Path
import numpy as np
ap=argparse.ArgumentParser(description=__doc__)
for k in ['field','diagnostic','out']:ap.add_argument('--'+k,required=True)
a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);field,diagnostic,out=[Path(getattr(a,k)).resolve() for k in ['field','diagnostic','out']]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();pins={str(p):sha(p) for p in [field,diagnostic]};f=np.load(field);r=json.loads(diagnostic.read_text());pairs=r['results'][-1]['originalParentPairs'];rows=[]
for pair in pairs:
    ids=f['previousTriangles'][pair].ravel();p=f['previousNativeXYZ'][ids];q=f['finalNativeXYZ'][ids];tri=p.reshape(2,3,3);areas=np.linalg.norm(np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]),axis=1)/2
    rows.append({'parentPair':pair,'vertexIDs':ids.tolist(),'sourceXYZ':f['sourceDisplayXYZ'][ids].tolist(),'previousXYZ':p.tolist(),'native19XYZ':q.tolist(),'previousTriangleAreasM2':areas.tolist(),'seamWeights':f['armSeamWeight'][ids].tolist(),'forearmWeights':f['forearmBlendWeight'][ids].tolist(),'branchStations':f['branchStation'][ids].tolist(),'branchSupport':f['branchSupport'][ids].tolist(),'branchScale':f['branchScale'][ids].tolist(),'previousTessellationPairPresentBeforeField':any(list(x)==pair for x in f['previousSelfPairs'])})
report={'status':'UNACCEPTED surviving fixed32 diagnostic pair inventory','pins':pins,'recipeSHA256':sha(__file__),'remainingParentPairs':rows,'limits':['This inventory identifies the remaining sampled-patch pair and parameters. It does not establish exact curved distance, a valid wearer port or a repair; unsupported field/geometry must be inspected.','Source19 native remains493body/35self failed; no radius/density iteration, native mutation, capture, rig, body/head/51bind change, Library/player promotion or M0-M5 acceptance.']}
assert pins=={p:sha(p) for p in pins};out.write_text(json.dumps(report,indent=2)+'\n');print('SURVIVING_PROFILE_PAIR_RECORDED',json.dumps(rows),flush=True)
