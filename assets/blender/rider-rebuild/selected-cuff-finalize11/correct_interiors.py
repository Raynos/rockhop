"""Add glove-to-sleeve triangle-interior constraints to the selected cuff.

Native glove digit support is excluded from must-hide cuff ownership; those
surfaces remain in the separate actual triangle crossing check. Original
visible witness corners remain explicitly included. No source stream outside
the selected sleeve position/normal/tangent/local carrier may change.
"""
import runpy,sys,json,time
from pathlib import Path
import numpy as np
from mathutils import Vector
D=runpy.run_path('assets/blender/rider-rebuild/selected-cuff-finish06/fit.py')

def prepare(intake,base):
 _,comps=D['load'](Path(intake));h=comps['RiderHoodie'];p=h['POSITION'].astype(float);f=h['indices'];names=h['names']
 report=json.loads((Path(base)/'report.json').read_text());z=dict(np.load(Path(base)/'patch.npz'))
 classify,canonical=D['load_canonical'](Path.cwd(),names);sides={}
 for policy in report['policies']:
  side=policy['side'];g=comps['ActualSelectedGlove.'+side];gp=g['POSITION'].astype(float);head=np.array(policy['nativeWrist']);axis=np.array(policy['nativeForearmAxis'])
  ext=np.zeros(len(p),bool);ext[policy['sourceExteriorRowIDs']]=True
  candidates=np.flatnonzero(np.any(ext[f],axis=1));centers=p[f[candidates]].mean(1);normals=np.cross(p[f[candidates,1]]-p[f[candidates,0]],p[f[candidates,2]]-p[f[candidates,0]])
  radial=centers-head-((centers-head)@axis)[:,None]*axis;_,_,_,body_signed=classify(centers,side)
  faces=candidates[(np.sum(normals*radial,axis=1)>0)&(body_signed>=0)]
  ownership,*_=classify(gp,side);cuff_faces=np.flatnonzero(np.any(ownership[g['indices']],axis=1));rows=np.unique(g['indices'][cuff_faces])
  digit=np.array([n.startswith(('DEF-thumb.','DEF-f_')) for n in names]);digitmass=np.sum(digit[g['JOINTS_0']]*g['WEIGHTS_0'],axis=1)
  # Exact original carrier semantics; no tuned positional/weight threshold.
  rows=rows[digitmass[rows]==0]
  keys=np.column_stack([gp[rows],g['JOINTS_0'][rows],g['WEIGHTS_0'][rows]]);_,first=np.unique(keys,axis=0,return_index=True);rows=rows[first]
  stations=(gp[rows]-head)@axis;origins=head+stations[:,None]*axis;radial=gp[rows]-origins;radii=np.linalg.norm(radial,axis=1);dirs=radial/radii[:,None]
  st=D['tree'](p,f[faces]);covered=[]
  for k,(o,d) in enumerate(zip(origins,dirs)):
   if any(q[1]>0 for q in D['hits'](st,o,d,1.,1e-6)):covered.append(k)
  covered=np.asarray(covered,dtype=int);witness_faces=[167304] if side=='L' else [74724,81481]
  assert np.all(digitmass[np.unique(g['indices'][witness_faces])]==0)
  sides[side]={'g':g,'faces':faces,'rows':rows[covered],'origins':origins[covered],'directions':dirs[covered],'radii':radii[covered],
   'policy':{'side':side,'mustCoverRepresentatives':len(covered),'nativeDigitSupportExcluded':True,'witnessFaces':witness_faces,'sourceExteriorTriangles':len(faces)}}
 return h,p,f,names,report,z,sides

def main(intake,base,outdir):
 start=time.monotonic();out=Path(outdir);assert not out.exists();out.mkdir(parents=True)
 h,p,f,names,report,z,sides=prepare(intake,base);inv=z['sourcePositionToUnique'];first=z['sourcePositionUniqueRows'];u=p[first];n=len(u)
 directions=z['radialDirections'];delta=z['connectedDisplacementByUniqueRow'].copy();domain=np.any(directions[first]!=0,axis=1);lower=delta.copy()
 cp=z['positionsAfter'].astype(float);cj=z['jointsAfter'];cw=z['weightsAfter'];samples=[];max_added=0.;badconstraint=[]
 epsilon=report['policies'][0]['quantizationClearanceMeters']
 for bike,played in report['playedReports'].items():
  poses=json.loads(Path(played['path']).read_text())['played']['motionSamples'];assert len(poses)==241
  for pi,sample in enumerate(poses):
   byname={j['id']:j['worldMatrix'] for j in sample['joints']};world=np.array([byname[name] for name in names]).reshape(-1,4,4).transpose(0,2,1);mat=world@h['ib']
   hp=D['skin'](cp,cj,cw,mat);posed_direction=np.zeros_like(p)
   for k in range(4):posed_direction+=np.einsum('nij,nj->ni',mat[cj[:,k],:3,:3],directions)*cw[:,k,None]
   for side,data in sides.items():
    ht=D['tree'](hp,f[data['faces']]);g=data['g'];rows=data['rows'];m=np.zeros((len(rows),4,4))
    for k in range(4):m+=mat[g['JOINTS_0'][rows,k]]*g['WEIGHTS_0'][rows,k,None,None]
    origins=np.einsum('nij,nj->ni',m[:,:3,:],np.column_stack([data['origins'],np.ones(len(rows))]));dirs=np.einsum('nij,nj->ni',m[:,:3,:3],data['directions']);scales=np.linalg.norm(dirs,axis=1);dirs/=scales[:,None]
    negative=0;missing=0;worst=0.;maxstep=0.
    for k,(o,d,r,s) in enumerate(zip(origins,dirs,data['radii'],scales)):
     hits=[q for q in D['hits'](ht,o,d,1.,1e-6) if q[1]>0]
     if not hits:missing+=1;continue
     t,dot,localface=max(hits,key=lambda q:q[0]);clearance=t-r*s
     if clearance>=epsilon:continue
     face=int(data['faces'][localface]);ids=f[face];uid=inv[ids]
     q=o+t*d;bary=D['barycentric'](q,hp[ids]);normal=np.cross(hp[ids[1]]-hp[ids[0]],hp[ids[2]]-hp[ids[0]]);normal/=np.linalg.norm(normal)
     response=posed_direction[ids]@normal
     # Give each face corner enough positive normal translation on its own.
     # This preserves a supporting half-space independent of hit barycentrics.
     if not domain[uid].all() or np.any(response<=0):
      badconstraint.append({'bike':bike,'tick':sample['tick'],'side':side,'gloveRow':int(rows[k]),'face':face,'response':response.tolist(),'clearance':float(clearance)});continue
     step=(epsilon-clearance)*dot/response
     np.maximum.at(lower,uid,delta[uid]+step)
     negative+=1;worst=min(worst,clearance);maxstep=max(maxstep,float(step.max()))
    samples.append({'bike':bike,'tick':sample['tick'],'side':side,'negativeOrBelowPrecision':negative,'missingSourceCoverage':missing,'worstMeters':worst,'maxRequiredAdditionalMeters':maxstep})
   if pi%40==0:
    progress={'accepted':False,'samples':samples,'elapsedSeconds':time.monotonic()-start,'maxAdditionalLowerBoundMeters':float((lower-delta).max()),'unresolvedConstraintCount':len(badconstraint)}
    (out/'progress.json').write_text(json.dumps(progress,indent=2)+'\n');print(json.dumps({k:v for k,v in progress.items() if k!='samples'}),flush=True)
 # Local obstacle continuation changes only the original connected cuff field.
 edges=np.concatenate([inv[f[:,[0,1]]],inv[f[:,[1,2]]],inv[f[:,[2,0]]]]);edges=np.sort(edges,axis=1);edges=np.unique(edges[edges[:,0]!=edges[:,1]],axis=0)
 weight=1/np.linalg.norm(u[edges[:,1]]-u[edges[:,0]],axis=1);src=np.r_[edges[:,0],edges[:,1]];dst=np.r_[edges[:,1],edges[:,0]];ww=np.r_[weight,weight];degree=np.bincount(src,weights=ww,minlength=n)
 original=np.cross(p[f[:,1]]-p[f[:,0]],p[f[:,2]]-p[f[:,0]]);original_length=np.linalg.norm(original,axis=1);nonzero=original_length>1e-20;history=[]
 for orient in range(100):
  for it in range(20000):
   average=np.bincount(src,weights=ww*delta[dst],minlength=n)/np.maximum(degree,1e-30);update=np.where(domain,np.maximum(lower,average),0.);error=float(np.max(abs(update-delta)));delta=update
   if error<=epsilon/32:break
  else:raise AssertionError('Local connected obstacle did not converge')
  candidate=(p+delta[inv,None]*directions).astype(np.float32);area=np.cross(candidate[f[:,1]].astype(float)-candidate[f[:,0]],candidate[f[:,2]].astype(float)-candidate[f[:,0]])
  dot=np.sum(area*original,axis=1);length=np.linalg.norm(area,axis=1);bad=np.flatnonzero(nonzero&((dot<=0)|(length<=1e-20)))
  history.append({'iteration':orient,'invalidFaces':bad.tolist()})
  if not len(bad):break
  for face in bad:
   ids=inv[f[face]];assert domain[ids].all();lower[ids]=np.maximum(lower[ids],np.max(delta[ids]))
 else:raise AssertionError('Float32 source face conditioning did not converge')
 assert np.all(delta>=z['connectedDisplacementByUniqueRow']);assert np.all(delta[~domain]==0)
 z.update(positionsAfter=candidate,connectedDisplacementByUniqueRow=delta,sourceCarrierRowDisplacement=delta[inv],conditionedOrientationLowerBounds=lower)
 np.savez(out/'patch.npz',**z);cj.astype('u1').tofile(out/'jointsAfter.bin');np.rint(cw*65535).astype('<u2').tofile(out/'weightsAfter.bin')
 report.update(accepted=False,recipeSHA256=D['sha'](__file__),baseEnvelope={'report':{'path':str(Path(base)/'report.json'),'sha256':D['sha'](Path(base)/'report.json')},'patch':{'path':str(Path(base)/'patch.npz'),'sha256':D['sha'](Path(base)/'patch.npz')}},patch={'path':str(out/'patch.npz'),'sha256':D['sha'](out/'patch.npz')},
  nonpositiveAreaOrientationDots=0,newlyDegenerateTriangles=0,exactFloat32GeometryChecked=True,hoodieMaxRestDisplacementMeters=float(np.linalg.norm(candidate-p,axis=1).max()),hoodieChangedRows=int(np.any(candidate!=p,axis=1).sum()),
  triangleInteriorCorrection={'policies':[q['policy'] for q in sides.values()],'samples':samples,'unresolvedConstraints':badconstraint,'orientationConditioning':history,'maxAdditionalLowerBoundMeters':float((lower-z['requiredByUniqueRow']).max()),'maxAdditionalActualMeters':float(np.linalg.norm(candidate-cp,axis=1).max()),'limits':['No must-hide requirement for digit-carried glove points or missing rays through cuff openings. Actual finite triangle crossing validation remains required.','All482 recorded poses constrain sampled sleeve triangle supporting planes; independent re-evaluation required.']},elapsedSeconds=time.monotonic()-start)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'accepted':False,'maxTotalMeters':report['hoodieMaxRestDisplacementMeters'],'maxAdditionalMeters':report['triangleInteriorCorrection']['maxAdditionalActualMeters'],'unresolved':len(badconstraint),'elapsedSeconds':time.monotonic()-start}),flush=True)
 assert not badconstraint,'Unresolved actual face constraints require source correction'
if __name__=='__main__':main(*sys.argv[sys.argv.index('--')+1:])
