"""Independent finite triangle crossing audit of the deformed selected cuff.

BVH pairs are only candidates. Float64 finite edge/triangle intersection
confirms every reported non-coplanar pair against actual posed positions.
Both directional edge sets are checked; all glove surfaces remain eligible.
"""
import runpy,sys,json,time
from pathlib import Path
import numpy as np
D=runpy.run_path('assets/blender/rider-rebuild/selected-cuff-finish06/fit.py')

def exact_crossings(a,b):
 result=np.zeros(len(a),bool);points=np.zeros((len(a),3));crossings=np.zeros(len(a),int);coplanar=np.zeros(len(a),bool)
 for edges,triangles in [(a,b),(b,a)]:
  e1=triangles[:,1]-triangles[:,0];e2=triangles[:,2]-triangles[:,0]
  for k in range(3):
   origin=edges[:,k];direction=edges[:,(k+1)%3]-origin;pvec=np.cross(direction,e2);det=np.einsum('ij,ij->i',e1,pvec)
   scale=np.linalg.norm(e1,axis=1)*np.linalg.norm(pvec,axis=1);parallel=np.abs(det)<=64*np.finfo(float).eps*scale
   invdet=np.zeros(len(a));invdet[~parallel]=1/det[~parallel];tvec=origin-triangles[:,0]
   u=np.einsum('ij,ij->i',tvec,pvec)*invdet;qvec=np.cross(tvec,e1);v=np.einsum('ij,ij->i',direction,qvec)*invdet;t=np.einsum('ij,ij->i',e2,qvec)*invdet
   hit=(~parallel)&(u>=0)&(v>=0)&(u+v<=1)&(t>=0)&(t<=1)
   points[hit]=origin[hit]+direction[hit]*t[hit,None];result|=hit;crossings+=hit
   normal=np.cross(e1,e2);plane=np.abs(np.einsum('ij,ij->i',normal,tvec));pscale=np.linalg.norm(normal,axis=1)*np.maximum(np.linalg.norm(tvec,axis=1),1)
   coplanar|=parallel&(plane<=64*np.finfo(float).eps*pscale)
 return result,points,crossings,coplanar

def main(intake,fit_path,out_path,mode='all'):
 a=np.array([[[0.,0.,0.],[1.,0.,0.],[0.,1.,0.]]])
 b=np.array([[[.2,.2,-1.],[.2,.2,1.],[.7,.2,0.]]])
 assert exact_crossings(a,b)[0][0], 'Known crossing must be reported'
 assert not exact_crossings(a,b+np.array([0.,0.,3.]))[0][0], 'Separated triangles must not cross'
 assert exact_crossings(a,a)[3][0], 'Coplanar identity must be surfaced as ambiguous'
 start=time.monotonic();out=Path(out_path);assert not out.exists();out.mkdir(parents=True)
 _,comps=D['load'](Path(intake));h=comps['RiderHoodie'];p=h['POSITION'].astype(float);f=h['indices'];names=h['names']
 fit=Path(fit_path);report=json.loads((fit/'report.json').read_text());z=np.load(fit/'patch.npz');classify,_=D['load_canonical'](Path.cwd(),names);sides={}
 for policy in report['policies']:
  side=policy['side'];g=comps['ActualSelectedGlove.'+side];head=np.array(policy['nativeWrist']);axis=np.array(policy['nativeForearmAxis']);ext=np.zeros(len(p),bool);ext[policy['sourceExteriorRowIDs']]=True
  candidates=np.flatnonzero(np.any(ext[f],axis=1));centers=p[f[candidates]].mean(1);normals=np.cross(p[f[candidates,1]]-p[f[candidates,0]],p[f[candidates,2]]-p[f[candidates,0]]);radial=centers-head-((centers-head)@axis)[:,None]*axis;_,_,_,signed=classify(centers,side)
  faces=candidates[(np.sum(normals*radial,axis=1)>0)&(signed>=0)]
  # Entire actual glove, including native digit surfaces, participates.
  sides[side]={'g':g,'faces':faces}
 result={'schema':'selected-cuff-finite-crossing-v1','accepted':False,'source':report['source'],'patchSHA256':D['sha'](fit/'patch.npz'),'samples':[],
  'method':'Actual native75 pose matrices; all actual glove triangles versus retained source exterior sleeve sheet. BVH candidates confirmed by float64 finite segment-triangle intersection in both directions. Native digit surfaces remain eligible; no must-hide ray ownership is used.',
  'limits':['Finite recorded poses, not unseen-pose proof.','Original radial exterior-sheet identity excludes retained internal sleeve caps/folds; moving parent visibility remains required.','Coplanar ambiguous pairs are reported separately and never called a pass.']}
 for bike,played in report['playedReports'].items():
  poses=json.loads(Path(played['path']).read_text())['played']['motionSamples'];assert len(poses)==241
  if mode!='all':poses=[q for q in poses if q['tick'] in [0,265,280,600,1200]]
  for pi,sample in enumerate(poses):
   byname={j['id']:j['worldMatrix'] for j in sample['joints']};world=np.array([byname[n] for n in names]).reshape(-1,4,4).transpose(0,2,1);mat=world@h['ib'];hp=D['skin'](z['positionsAfter'],z['jointsAfter'],z['weightsAfter'],mat)
   for side,data in sides.items():
    g=data['g'];gp=D['skin'](g['POSITION'],g['JOINTS_0'],g['WEIGHTS_0'],mat);faces=data['faces'];ht=D['tree'](hp,f[faces]);gt=D['tree'](gp,g['indices']);pairs=np.array(ht.overlap(gt),dtype=int).reshape(-1,2)
    if len(pairs):
     a=hp[f[faces[pairs[:,0]]]];b=gp[g['indices'][pairs[:,1]]];hit,points,edgecount,coplanar=exact_crossings(a,b);confirmed=pairs[hit];ambiguous=pairs[coplanar&~hit]
    else:confirmed=ambiguous=pairs;points=np.empty((0,3));hit=np.zeros(0,bool)
    row={'bike':bike,'tick':sample['tick'],'side':side,'bvhCandidatePairs':len(pairs),'confirmedNoncoplanarPairs':len(confirmed),'coplanarAmbiguousPairs':len(ambiguous),
     'hoodieFaces':np.unique(faces[confirmed[:,0]]).tolist() if len(confirmed) else [],'gloveFaces':np.unique(confirmed[:,1]).tolist() if len(confirmed) else [],
     'pairs':[{'hoodieFace':int(faces[aa]),'gloveFace':int(bb),'intersectionPoint':point.tolist()} for (aa,bb),point in zip(confirmed,points[hit])],
     'coplanarPairs':[[int(faces[aa]),int(bb)] for aa,bb in ambiguous]}
    result['samples'].append(row)
   if pi%20==0:
    result['elapsedSeconds']=time.monotonic()-start;(out/'progress.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'bike':bike,'tick':sample['tick'],'samples':len(result['samples']),'latestCrossings':[q['confirmedNoncoplanarPairs'] for q in result['samples'][-2:]]}),flush=True)
 result['confirmedPairsTotal']=sum(q['confirmedNoncoplanarPairs'] for q in result['samples']);result['ambiguousPairsTotal']=sum(q['coplanarAmbiguousPairs'] for q in result['samples']);result['sampledPoses']=len(result['samples'])//2;result['pass']=result['confirmedPairsTotal']==0 and result['ambiguousPairsTotal']==0;result['elapsedSeconds']=time.monotonic()-start
 (out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['samples','source','method','limits']}),flush=True)
if __name__=='__main__':main(*sys.argv[sys.argv.index('--')+1:])
