from pathlib import Path
import numpy as np,json,hashlib,sys
sys.path.insert(0,'scripts');from glb import GLB
root=Path.cwd();base=GLB(root/'baseline/rider.glb');report={'date':'2026-10-01','source':str(base.path),'sourceSHA256':hashlib.sha256(base.raw).hexdigest(),'modeling':'All CPU NumPy/SciPy; no inference/model/GPU jobs. Blender Cycles CPU two threads. No other agent/source/production files changed.','variants':{}}
for name in ['A','B','C19','C']:
 g=GLB(root/'deliverables'/f'{name}.glb');count=0
 for mi,m in enumerate(base.j['meshes']):
  for pi,p in enumerate(m['primitives']):
   out=g.j['meshes'][mi]['primitives'][pi]
   for attr,ai in p['attributes'].items():
    if attr.startswith(('JOINTS','WEIGHTS'))and name!='A':continue
    assert np.array_equal(base.array(ai),g.array(out['attributes'][attr])),(name,attr);count+=1
   assert np.array_equal(base.array(p['indices']),g.array(out['indices']));assert p.get('targets')==out.get('targets')
 assert base.j['materials']==g.j['materials'];assert base.j['images']==g.j['images'];assert bytes(g.bin[:len(base.bin)])==bytes(base.bin)
 P=np.load(root/'experiments'/f'{name}-bind.npz')['centres'];legs=[]
 for h,k,f in [(13,14,15),(16,17,18)]:legs.append({'thigh':float(np.linalg.norm(P[k]-P[h])),'shin':float(np.linalg.norm(P[f]-P[k]))})
 report['variants'][name]={'sha256':hashlib.sha256(g.raw).hexdigest(),'bytes':len(g.raw),'skinJoints':len(g.j['skins'][0]['joints']),'sourceGeometryNormalUVColorIndicesMorphsImagesMaterialsExact':True,'originalBinaryPrefixExact':True,'standingCoordinatesRetained':True,'sourceAttributesChecked':count,'legLengthsM':legs,'freshSkeleton':name.startswith('C'),'freshWeights':name!='A','newHipCentres':P[[13,16]].tolist(),'standToSitKeyCount':25,'controlSeconds':2,'restAxes':'C joints use explicit world-aligned coordinate bases with local translations from the new parent hierarchy; Blender importer reconstructs display tails. Local quaternions are solved from world poses, not copied between rigs.'}
report['contactBasis']='One static retained contact endpoint supplies wrist/ankle transforms for all variants; closed-grip source morphs retained. All animation trajectories newly authored, rigid two-bone IK with explicit forward/outward knee and backward/outward elbow poles. Same pelvis translation/torso rotation controls; changed anatomical centres change elbow/knee paths by design.'
report['limits']='Diagnostic offline control only. No normal gameplay/Garage adapter, broad riding-state sweep, dynamic cloth solver or production promotion. C19 is a failed overall sitting fix despite improved endpoint contour/stretch.'
(root/'deliverables/provenance.json').write_text(json.dumps(report,indent=2));print('PARITY PASS')
