"""Actual replay pad gaps and conservative whole-triangle envelope bounds, CPU only."""
from pathlib import Path
import json,hashlib,sys
import numpy as np
from scipy.optimize import linprog
np.seterr(all='raise')
repo=Path('/Users/raynos/projects/games/rockhop');adapter=repo/'docs/evidence/hero-remaster/one-rider-v2/rig-adapter01';out=Path(sys.argv[1]) if len(sys.argv)>1 else adapter/'played-surfaces11';roi=json.loads((out/'source-roi.json').read_text());r=json.loads((out/'report.json').read_text());assert len(r['samples'])==480 and not r.get('failure')
def distances(points,triangles):
 a=triangles[:,0];ab=triangles[:,1]-a;ac=triangles[:,2]-a;n=np.cross(ab,ac);n/=np.linalg.norm(n,axis=1)[:,None];q=points[:,None,:]-a;sd=np.einsum('pti,ti->pt',q,n);proj=q-sd[:,:,None]*n
 aa=np.einsum('ti,ti->t',ab,ab);bb=np.einsum('ti,ti->t',ab,ac);cc=np.einsum('ti,ti->t',ac,ac);den=aa*cc-bb*bb
 qa=np.einsum('pti,ti->pt',proj,ab);qc=np.einsum('pti,ti->pt',proj,ac);u=(cc*qa-bb*qc)/den;v=(aa*qc-bb*qa)/den;inside=(u>=0)&(v>=0)&(u+v<=1)
 best=np.where(inside,sd*sd,np.inf)
 for i in range(3):
  start=triangles[:,i];edge=triangles[:,(i+1)%3]-start;q=points[:,None,:]-start;w=np.clip(np.einsum('pti,ti->pt',q,edge)/np.einsum('ti,ti->t',edge,edge),0,1);d=q-w[:,:,None]*edge;best=np.minimum(best,np.einsum('pti,pti->pt',d,d))
 return np.sqrt(best.min(1))
rows=[];summaries=[]
for k,entry in enumerate(roi['hands']+roi['feet']):
 kind='hand' if k<2 else 'sole';p=out/f'{kind}-{entry["side"]}.f32'
 if not p.exists():p=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/rig-adapter01')/out.relative_to(adapter)/p.name
 points=np.fromfile(p,dtype='<f4').reshape(480,len(entry['sourceVertices']),3).astype(np.float64);assert np.isfinite(points).all();drift=np.linalg.norm(points-points[0],axis=2).max();setup=r['surfaceSetup'][k];tri=np.array([t['points'] for t in setup['bikeTriangleVertices']]);summary={'kind':kind,'side':entry['side'],'actualVertices':points.shape[1],'actualTriangles':len(entry['triangles']),'maximumActualBikeLocalVertexDriftM':float(drift),'bufferSHA256':hashlib.sha256(p.read_bytes()).hexdigest()}
 if kind=='hand':
  selected=sorted(set(i for ids in entry['palmarPadGroups'].values() for i in ids));lookup={v:i for i,v in enumerate(selected)};allgaps=[]
  for fi in range(480):
   gap=distances(points[fi,selected],tri);groups={}
   for finger,ids in entry['palmarPadGroups'].items():
    ds=gap[[lookup[v] for v in ids]];groups[finger]={'minimumAbsolutePadVertexTriangleGapM':float(ds.min()),'within1mmPadVertices':int((ds<=.001).sum()),'padVertices':len(ids)}
   rows.append({'i':fi,'tick':r['samples'][fi]['tick'],'side':entry['side'],'palmarPads':groups});allgaps.append(groups)
  summary['palmarPadGapRangesM']={f:[min(g[f]['minimumAbsolutePadVertexTriangleGapM'] for g in allgaps),max(g[f]['minimumAbsolutePadVertexTriangleGapM'] for g in allgaps)] for f in entry['palmarPadGroups']}
  # Every actual rod vertex/triangle lies inside an explicitly inflated convex
  # envelope. LP finds deepest point over each whole actual glove triangle.
  a=tri[:,0];n=np.cross(tri[:,1]-a,tri[:,2]-a);n/=np.linalg.norm(n,axis=1)[:,None];centre=tri.reshape(-1,3).mean(0);flip=np.einsum('ti,ti->t',n,tri.mean(1)-centre)<0;n[flip]*=-1;offset=np.einsum('ti,ti->t',n,a);verts=tri.reshape(-1,3);inflation=np.maximum((np.einsum('vi,fi->vf',verts,n)-offset).max(0),0);outer=offset+inflation+1e-9;records=[]
  for ti,ids in enumerate(entry['triangles']):
   q=points[0,ids];signed=np.einsum('vi,fi->vf',q,n)-outer
   if np.any(signed.min(0)>1e-9):continue
   e1=q[1]-q[0];e2=q[2]-q[0];constraint=np.column_stack([np.einsum('fi,i->f',n,e1),np.einsum('fi,i->f',n,e2),np.ones(len(n))]);rhs=outer-np.einsum('fi,i->f',n,q[0]);constraint=np.vstack([constraint,[1,1,0]]);rhs=np.r_[rhs,1];result=linprog([0,0,-1],A_ub=constraint,b_ub=rhs,bounds=[(0,None),(0,None),(None,None)],method='highs');assert result.success
   records.append({'handTriangle':ti,'sourceVertices':[entry['sourceVertices'][i] for i in ids],'depthM':max(0,float(result.x[2])),'barycentric':[float(1-result.x[0]-result.x[1]),float(result.x[0]),float(result.x[1])]})
  records.sort(key=lambda x:x['depthM'],reverse=True);summary['conservativeWholeTriangleEnvelope']={'referenceSample':0,'linearPrograms':len(records),'planeInflationMaximumM':float(inflation.max()),'referenceMaximumDepthM':records[0]['depthM'],'all480SampleDepthUpperBoundM':records[0]['depthM']+float(drift)+2e-7,'float32SerializationAllowanceM':2e-7,'worstTriangle':records[0],'interpretation':'Inflated convex-envelope depth bound plus maximum actual rigid-frame drift; not zero triangle intersections.'}
 else:
  cs=[s['contacts'][k] for s in r['samples']];summary['minimumAbsoluteVertexTriangleGapRangeM']=[min(c['minimumAbsoluteVertexTriangleGapM'] for c in cs),max(c['minimumAbsoluteVertexTriangleGapM'] for c in cs)];summary['nearestFaceSignedDepthRangeM']=[min(c['maximumNearestNormalSignedVertexDepthM'] for c in cs),max(c['maximumNearestNormalSignedVertexDepthM'] for c in cs)]
 summaries.append(summary)
baseline=json.loads((adapter/'body-bind09/played01/textured/report.json').read_text())['samples'];assert len(baseline)==480;equal=all(a['state']==b['state'] and a['hash']==b['hash'] and a['debug']==b['debug'] for a,b in zip(baseline,r['samples']));assert equal
landings=[]
for i,s in enumerate(r['samples'][1:],1):
 before=r['samples'][i-1]['state']['wheels'];after=s['state']['wheels']
 if any(not before[w]['grounded'] and after[w]['grounded'] for w in ['rear','front']):landings.append({'sample':i,'tick':s['tick'],'wheelTransitions':[w for w in ['rear','front'] if not before[w]['grounded'] and after[w]['grounded']],'recoverySamples':[j for j in range(i,min(i+13,480))]})
airborne=[];begin=None
for i,s in enumerate(r['samples']):
 air=not any(s['state']['wheels'][w]['grounded'] for w in ['rear','front'])
 if air and begin is None:begin=i
 if not air and begin is not None:
  if i-begin>=2:airborne.append({'firstAirborneSample':begin,'landingSample':i,'sampledAirborneSeconds':(i-begin)/12,'recoverySamples':list(range(i,min(i+13,480)))})
  begin=None
report={'actualSamples':480,'stateHashDebugExactAgainstBody09':equal,'maxLean':{'minimum':min(s['state']['rider']['lean'] for s in r['samples']),'maximum':max(s['state']['rider']['lean'] for s in r['samples']),'negativeSamples':[s['i'] for s in r['samples'] if s['state']['rider']['lean']==-1],'positiveSamples':[s['i'] for s in r['samples'] if s['state']['rider']['lean']==1]},'allWheelGroundingTransitions':landings,'twoWheelAirborneLandingsAndRecovery':airborne,'surfaces':summaries,'palmarPadSamples':rows,'limits':['Distances use actual rendered morph/skin vertex positions versus actual decoded bike triangles.','Whole-finger closest points can lie outside palmar pads; only explicit palmarPadGroups evaluate historical thumb-pad defect.','Conservative envelope penetration includes quantized plane inflation; no zero-intersection or visual contact acceptance claimed.','12fps metric sample cadence cannot bound intermediate unsampled physics ticks.','Source sole selection is the lowest 2.1mm vertices, not a certified complete outsole collision mesh.','All wheel-grounding transitions include contact jitter; separate sustained two-wheel airborne events require at least two sampled frames.','Builder has not judged visual quality; parent must play moving clips.']}
(out/'surface-audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'stateHashDebugExact':equal,'landings':len(landings),'surfaces':summaries}))
