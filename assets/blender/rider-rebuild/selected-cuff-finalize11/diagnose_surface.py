"""Diagnose rejected finite rays against all actual selected hoodie triangles.

The rejected validator remains unchanged. This describes individual failures
and known visible source witnesses, without claiming visual acceptance.
"""
import json,runpy,sys,time,hashlib
from pathlib import Path
import numpy as np
from mathutils import Vector
D=runpy.run_path('assets/blender/rider-rebuild/selected-cuff-finish06/fit.py')
root=Path('harness/out/rider-rebuild/selected-cuff-finish06')
_,comps=D['load'](root/'intake02');h=comps['RiderHoodie'];p=h['POSITION'].astype(float);f=h['indices'];names=h['names']
z=np.load(root/'fit08/patch.npz');report=json.loads((root/'fit08/report.json').read_text());progress=json.loads((root/'validate01/progress.json').read_text())
classify,canonical=D['load_canonical'](Path.cwd(),names)
rows_out=[]
for policy in report['policies']:
 side=policy['side'];g=comps['ActualSelectedGlove.'+side];gp=g['POSITION'].astype(float);head=np.array(policy['nativeWrist']);axis=np.array(policy['nativeForearmAxis'])
 ext=np.zeros(len(p),bool);ext[policy['sourceExteriorRowIDs']]=True
 candidates=np.flatnonzero(np.any(ext[f],axis=1));centers=p[f[candidates]].mean(1)
 normals=np.cross(p[f[candidates,1]]-p[f[candidates,0]],p[f[candidates,2]]-p[f[candidates,0]])
 radial=centers-head-((centers-head)@axis)[:,None]*axis
 _,_,_,body_signed=classify(centers,side)
 faces=candidates[(np.sum(normals*radial,axis=1)>0)&(body_signed>=0)]
 witness_faces=[167304] if side=='L' else [74724,81481]
 worst=min([q for q in progress['samples'] if q['side']==side],key=lambda q:q['clearanceMeters'][0])
 selected=np.unique(np.r_[g['indices'][witness_faces].reshape(-1),worst['worst']['row'],worst['missingRowIDs']]).astype(int)
 stations=(gp[selected]-head)@axis;origins=head+stations[:,None]*axis;radials=gp[selected]-origins;radii=np.linalg.norm(radials,axis=1);dirs=radials/radii[:,None]
 witnessrows=set(g['indices'][witness_faces].reshape(-1).tolist())
 states=[('sourceRest',p,h['JOINTS_0'],h['WEIGHTS_0'],np.tile(np.eye(4),(len(names),1,1))),('candidateRest',z['positionsAfter'],z['jointsAfter'],z['weightsAfter'],np.tile(np.eye(4),(len(names),1,1)))]
 for tick in sorted({worst['tick'],1200}):
  poses=json.loads(Path(report['playedReports']['rookie']['path']).read_text())['played']['motionSamples'];sample=next(q for q in poses if q['tick']==tick)
  byname={j['id']:j['worldMatrix'] for j in sample['joints']};world=np.array([byname[n] for n in names]).reshape(-1,4,4).transpose(0,2,1);mat=world@h['ib']
  states.append(('candidateRookie'+str(tick),z['positionsAfter'],z['jointsAfter'],z['weightsAfter'],mat))
 for label,hp,hj,hw,mat in states:
  hp=D['skin'](hp,hj,hw,mat);fulltree=D['tree'](hp,f);exttree=D['tree'](hp,f[faces]);ggp=D['skin'](gp[selected],g['JOINTS_0'][selected],g['WEIGHTS_0'][selected],mat)
  m=np.zeros((len(selected),4,4))
  for k in range(4):m+=mat[g['JOINTS_0'][selected,k]]*g['WEIGHTS_0'][selected,k,None,None]
  oo=np.einsum('nij,nj->ni',m[:,:3,:],np.column_stack([origins,np.ones(len(selected))]));dd=np.einsum('nij,nj->ni',m[:,:3,:3],dirs);scales=np.linalg.norm(dd,axis=1);dd/=scales[:,None]
  for k,row in enumerate(selected):
   rec={'side':side,'state':label,'row':int(row),'isWitness':int(row) in witnessrows,'isWorst':int(row)==worst['worst']['row'],'station':float(stations[k]),'radius':float(radii[k]),'position':ggp[k].tolist()}
   for key,t,ff in [('full',fulltree,f),('exterior',exttree,f[faces])]:
    hits=D['hits'](t,oo[k],dd[k],1.,1e-6)
    rec[key+'Hits']=[{'clearance':float(dist-radii[k]*scales[k]),'dot':dot,'face':int(fi if key=='full' else faces[fi])} for dist,dot,fi in hits]
    q,n,face,distance=t.find_nearest(Vector(ggp[k]));rec[key+'Nearest']={'face':int(face if key=='full' else faces[face]),'distance':distance,'signed':float((ggp[k]-np.asarray(q))@n),'barycentric':D['barycentric'](np.array(q),hp[ff[face]]).tolist()}
   rows_out.append(rec)
out=Path(sys.argv[sys.argv.index('--')+1]);assert not out.exists();out.parent.mkdir(parents=True,exist_ok=True)
out.write_text(json.dumps({'accepted':False,'schema':'selected-cuff-surface-diagnostic-v1','source':report['source'],'candidatePatchSHA256':D['sha'](root/'fit08/patch.npz'),'rows':rows_out,'limits':['Individual finite ray diagnosis only; no moving-art acceptance.','All original exterior gate failures retained; no altered acceptance.']},indent=2)+'\n')
print(json.dumps({'rows':len(rows_out),'output':str(out)}),flush=True)
