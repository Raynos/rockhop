"""Enforce exact float32 face orientation on the measured cuff obstacle field.

Only increase displacement lower bounds; preserve all 482 measured pose
constraints and the exact local carrier. No altered clearance acceptance.
"""
import runpy,sys,json,time,shutil,hashlib
from pathlib import Path
import numpy as np
D=runpy.run_path(str(Path(__file__).with_name('fit.py')))
def main(intake,base_dir,out_dir):
 start=time.monotonic();base=Path(base_dir);out=Path(out_dir);assert not out.exists();out.mkdir(parents=True)
 report=json.loads((base/'report.json').read_text());z=dict(np.load(base/'patch.npz'));_,comps=D['load'](Path(intake));f=comps['RiderHoodie']['indices']
 p=z['positionsBefore'];directions=z['radialDirections'];inv=z['sourcePositionToUnique'];first=z['sourcePositionUniqueRows'];u=p[first];n=len(u)
 required=z['requiredByUniqueRow'].copy();anchors=required.copy();delta=z['connectedDisplacementByUniqueRow'].copy();domain=np.any(directions[first]!=0,axis=1)
 edges=np.concatenate([inv[f[:,[0,1]]],inv[f[:,[1,2]]],inv[f[:,[2,0]]]]);edges=np.sort(edges,axis=1);edges=np.unique(edges[edges[:,0]!=edges[:,1]],axis=0)
 weight=1/np.linalg.norm(u[edges[:,1]]-u[edges[:,0]],axis=1);src=np.r_[edges[:,0],edges[:,1]];dst=np.r_[edges[:,1],edges[:,0]];ww=np.r_[weight,weight];degree=np.bincount(src,weights=ww,minlength=n)
 original=np.cross(p[f[:,1]]-p[f[:,0]],p[f[:,2]]-p[f[:,0]]);original_length=np.linalg.norm(original,axis=1)
 nonzero=original_length>1e-20;epsilon=report['policies'][0]['quantizationClearanceMeters'];history=[]
 for iteration in range(200):
  cp=(p+delta[inv,None]*directions).astype(np.float32).astype(float);area=np.cross(cp[f[:,1]]-cp[f[:,0]],cp[f[:,2]]-cp[f[:,0]])
  dots=np.sum(area*original,axis=1);lengths=np.linalg.norm(area,axis=1);bad=np.flatnonzero(nonzero&((dots<=0)|(lengths<=1e-20)))
  history.append({'iteration':iteration,'invalidFaces':bad.tolist(),'maxDisplacementMeters':float(delta.max())});print(json.dumps(history[-1]),flush=True)
  if not len(bad):break
  for face in bad:
   ids=inv[f[face]];assert domain[ids].all(),'Invalid face outside local cuff domain'
   # Uniform radial displacement is locally orientation preserving; lift the
   # lower corners to the measured larger corner, then diffuse coherently.
   anchors[ids]=np.maximum(anchors[ids],np.max(delta[ids]))
  for inner in range(20000):
   average=np.bincount(src,weights=ww*delta[dst],minlength=n)/np.maximum(degree,1e-30)
   update=np.where(domain,np.maximum(anchors,average),0.);error=np.max(abs(update-delta));delta=update
   if error<=epsilon/32:break
  else:raise AssertionError('Connected face constraint solve did not converge')
 else:raise AssertionError('Exact float32 face orientation did not converge')
 assert np.all(delta>=required) and np.all(delta[~domain]==0)
 z.update(positionsAfter=cp.astype(np.float32),connectedDisplacementByUniqueRow=delta,sourceCarrierRowDisplacement=delta[inv],conditionedOrientationLowerBounds=anchors)
 np.savez(out/'patch.npz',**z)
 for name in ['jointsAfter.bin','weightsAfter.bin']:shutil.copyfile(base/name,out/name)
 affected=np.any(np.any(cp[f]!=p[f],axis=2),axis=1);area_ratio=lengths[affected&nonzero]/original_length[affected&nonzero]
 report.update(accepted=False,recipeSHA256=D['sha'](__file__),baseEnvelope={'report':{'path':str(base/'report.json'),'sha256':D['sha'](base/'report.json')},'patch':{'path':str(base/'patch.npz'),'sha256':D['sha'](base/'patch.npz')}},
   patch={'path':str(out/'patch.npz'),'sha256':D['sha'](out/'patch.npz')},nonpositiveAreaOrientationDots=0,newlyDegenerateTriangles=0,
   affectedInheritedZeroAreaTriangles=int(np.sum(affected&~nonzero)),affectedAreaRatioPercentiles=np.percentile(area_ratio,[0,50,100]).tolist(),
   hoodieMaxRestDisplacementMeters=float(np.linalg.norm(cp-p,axis=1).max()),hoodieChangedRows=int(np.any(cp!=p,axis=1).sum()),
   exactFloat32GeometryChecked=True,orientationConditioning={'method':'Raise failing face corner lower bounds to its current maximum then solve the same connected obstacle. All pose lower bounds retained, no displacement cap or orientation waiver.','iterations':history},elapsedSeconds=time.monotonic()-start)
 (out/'report.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
 print(json.dumps({'pass':True,'accepted':False,'maxRestDisplacementMeters':report['hoodieMaxRestDisplacementMeters'],'iterations':len(history)}),flush=True)
if __name__=='__main__':main(*sys.argv[sys.argv.index('--')+1:])
