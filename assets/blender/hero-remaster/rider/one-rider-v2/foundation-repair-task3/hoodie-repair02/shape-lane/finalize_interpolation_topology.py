from pathlib import Path
import sys,json,numpy as np,hashlib
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'hoodie-repair02/scripts'));from base import *
OUT=Path(__file__).parent;d=np.load(OUT/'interpolation-topology-flip78.npz');old=np.load(OUT/'shape-retop-uvsafe.npz');p=[d[f'p{i}']for i in range(5)];t=[d[f'tr{i}']for i in range(5)];allp=np.concatenate(p);q=np.zeros_like(U);np.add.at(q,INV,allp);q/=np.bincount(INV)[:,None];ct=np.concatenate([INV[t[i]+OFF[i]]for i in [0,2]]);oldct=np.concatenate([INV[old[f'tr{i}']+OFF[i]]for i in [0,2]]);qq=q[ct];fn=np.cross(qq[:,1]-qq[:,0],qq[:,2]-qq[:,0]);un=np.zeros_like(U)
for j in range(3):np.add.at(un,ct[:,j],fn)
un/=np.maximum(np.linalg.norm(un,axis=1,keepdims=True),1e-15);nn=[d[f'n{i}'].copy()for i in range(5)]
for i in [0,2]:nn[i]=un[INV[OFF[i]:OFF[i+1]]]
np.savez(OUT/'shape-interpolation-retop.npz',**{f'p{i}':v for i,v in enumerate(p)},**{f'tr{i}':v for i,v in enumerate(t)},**{f'n{i}':v for i,v in enumerate(nn)},sourceAlias=INV,primitiveOffsets=OFF)
def topology(tri):
 e=np.sort(np.concatenate([tri[:,[0,1]],tri[:,[1,2]],tri[:,[0,2]]]),axis=1);ue,c=np.unique(e,axis=0,return_counts=True);return ue[c==1],ue[c>2]
b0,m0=topology(oldct);b1,m1=topology(ct)
# Geometric deviation of alternate piecewise-linear quad via sampled barycentrics,
# triangle closest point distance. Existing vertices themselves unchanged.
from scipy.optimize import minimize
oldtr=old['tr2'][[78,79]];newtr=t[2][[78,79]];oldq=p[2][oldtr];newq=p[2][newtr]
def distance(point,triangles):
 best=1e9
 for tri in triangles:
  a,b,c=tri;B=np.stack([b-a,c-a],axis=1);fun=lambda v:float(np.sum((a+B@v-point)**2));fit=minimize(fun,np.array([.33,.33]),bounds=[(0,1),(0,1)],constraints=[{'type':'ineq','fun':lambda v:1-v.sum()}],method='SLSQP',options={'ftol':1e-14,'maxiter':40});best=min(best,float(np.sqrt(max(0,fit.fun))))
 return best
samples=np.array([[i/8,j/8,1-(i+j)/8]for i in range(9)for j in range(9-i)]);one=[distance(q,newq)for tri in oldq for q in samples@tri];two=[distance(q,oldq)for tri in newq for q in samples@tri]
rep={'sourceC19SHA256':hashlib.sha256(G.raw).hexdigest(),'baseShapeSHA256':hashlib.sha256((OUT/'shape-retop-uvsafe.npz').read_bytes()).hexdigest(),'candidateSHA256':hashlib.sha256((OUT/'shape-interpolation-retop.npz').read_bytes()).hexdigest(),'method':'Sourceconstruction alternate diagonal on warped posterior shoulderinsertquad; primitive2faces78/79 [106,108,101]+[121,108,106] ->[121,101,106]+[101,121,108]. Novertexdelete/collapse, no poseatlas, no changedrestpositions/weights/UV/materials.','changedFacesPrimitive2':[78,79],'changedFacesOtherPrimitives':0,'vertexArraysExactlySame':all(np.array_equal(d[f'p{i}'],old[f'p{i}'])for i in range(5)),'boundaryExactlySame':bool(np.array_equal(b0,b1)),'nonmanifoldBefore':len(m0),'nonmanifoldAfter':len(m1),'headGloveGeometryAndNormalsExact':all(np.array_equal(d[f'p{i}'],old[f'p{i}'])and np.array_equal(t[i],old[f'tr{i}'])and np.array_equal(nn[i],old[f'n{i}'])for i in [1,3,4]),'normalsRecomputedSewnCloth':True,'UVCoordinatesExact':'Existingattributearraysuntouched, bothnewUVareasnegativeasmatchingoldsource orientation. Newly interpolatedtexelswithinlocalquadwilldiffer; parentPBRreviewrequired.','sampledRestSurfaceMaxDeviationM':max(one+two),'sampledRestDeviationDetails':{'oldToNewMaxM':max(one),'newToOldMaxM':max(two),'samplesEachDirection':len(one)},'actualV6RuntimeLocalGate':json.load(open(OUT/'interpolation-retop-probes.json'))['reports'][0],'limits':['No all-timeCCD or thicknesscertificate. Existing101positions+changedtriangles have0localstrictcross; fullindependentnewGLBcheckrequired.','Twofacearea sum drops35.5% bydifferentdiagonalofnonplanar sourcequad; sourcepositionsfixed doesnotmeanentirepiecewiseplanarsurfaceidentical.','Regenerate baked NORMAL targets using newtriangles; copyingoldmorphnormalswould retainwrongshading.','Broadcanonicaloverhead/elbow/forwardfailures remain outside thislocalfix.','No frozenV6 inputsmodified.']}
(OUT/'shape-interpolation-retop-provenance.json').write_text(json.dumps(rep,indent=2));print(json.dumps({k:v for k,v in rep.items()if k!='actualV6RuntimeLocalGate'},indent=2))
