"""Quantify exact-source skin union and loss before moving-pose acceptance."""
import json,sys,numpy as np
from pathlib import Path
intake,prepare,out=map(Path,sys.argv[1:]);t=np.load(prepare/'transfer.npz')
j=np.fromfile(intake/'JOINTS_0.bin',np.uint8).reshape(-1,4);w=np.fromfile(intake/'WEIGHTS_0.bin','<f4').reshape(-1,4);ix=np.fromfile(intake/'indices.bin','<u4').reshape(-1,3)
# Union across the complete original hoodie, ignoring exact zero weights.
face_j=j[ix].reshape(-1,12);face_w=w[ix].reshape(-1,12);sorted_j=np.sort(np.where(face_w>1e-8,face_j,255),axis=1)
counts=((sorted_j[:,:1]!=255).astype(int).ravel()+((sorted_j[:,1:]!=sorted_j[:,:-1])&(sorted_j[:,1:]!=255)).sum(1))
discard=[];union=[];worst=[];nearestj=np.empty_like(t['joints']);nearestw=np.empty_like(t['weights'])
for v,(face,bc) in enumerate(zip(t['closestFaces'],t['bary'])):
 rows=ix[face];a=np.bincount(j[rows].ravel(),weights=(w[rows]*bc[:,None]).ravel(),minlength=256);loss=float(max(0,1-np.sort(a)[-4:].sum()));discard.append(loss);union.append(int((a>1e-8).sum()))
 chosen=rows[np.argmax(bc)];nearestj[v]=j[chosen];nearestw[v]=w[chosen]
 if loss>.1:worst.append({'lowVertex':v,'sourceFace':int(face),'bary':bc.tolist(),'discardedMass':loss,'jointMass':{str(k):float(a[k]) for k in np.flatnonzero(a>1e-8)}})
def hist(a):return {str(int(k)):int(n) for k,n in zip(*np.unique(a,return_counts=True))}
a=np.asarray(discard);report={'accepted':False,'geometricVertices':len(a),'top4DiscardedMassCounts':{str(q):int((a>q).sum()) for q in [.01,.05,.1,.2]},'originalFaceUnionInfluenceCounts':hist(counts),'targetProjectedUnionInfluenceCounts':hist(union),'worstRows':sorted(worst,key=lambda r:r['discardedMass'],reverse=True)[:30],'candidateAlternative':'Unpromoted largest-barycentric-source-corner exact4weight field, preserving original native joint IDs. Requires procedural moving-matrix comparison before selecting either field.'}
out.mkdir(parents=True,exist_ok=True);(out/'skin.json').write_text(json.dumps(report,indent=2)+'\n');nearestj.tofile(out/'nearest-corner-joints.u8');nearestw.tofile(out/'nearest-corner-weights.f32');print(json.dumps({k:v for k,v in report.items() if k!='worstRows'}))
