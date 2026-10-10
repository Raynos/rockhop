"""Attribute actual finite crossings to source sheet geometry and played sightlines.

No geometry edits. Source-face centroids, original radial exterior ownership,
actual wrist stations and nearest played-camera surfaces are measurements.
Visibility uses the exact captured source-pose camera, not a posed art scene.
"""
import runpy,sys,json,time
from pathlib import Path
import numpy as np
from mathutils import Vector
D=runpy.run_path('assets/blender/rider-rebuild/selected-cuff-finish06/fit.py')

def main(intake,fit_path,crossings_path,out_path,camera_mode="all"):
 start=time.monotonic();out=Path(out_path);assert not out.exists();out.parent.mkdir(parents=True,exist_ok=True)
 _,comps=D['load'](Path(intake));h=comps['RiderHoodie'];p=h['POSITION'].astype(float);f=h['indices'];names=h['names'];fit=Path(fit_path);z=np.load(fit/'patch.npz');report=json.loads((fit/'report.json').read_text());cross=json.loads(Path(crossings_path).read_text());classify,_=D['load_canonical'](Path.cwd(),names)
 source_faces=[];sides={}
 for policy in report['policies']:
  side=policy['side'];head=np.array(policy['nativeWrist']);axis=np.array(policy['nativeForearmAxis']);ext=np.zeros(len(p),bool);ext[policy['sourceExteriorRowIDs']]=True
  branches=np.array([(('.'+side) in n) and n.startswith(('DEF-forearm.','DEF-hand.','DEF-palm.','DEF-thumb.','DEF-f_')) for n in names]);positive_side=np.any(branches[h['JOINTS_0']]&(h['WEIGHTS_0']>0),axis=1);local=np.any(positive_side[f],axis=1);localfaces=np.flatnonzero(local);st=D['tree'](p,f[localfaces])
  faces=np.unique([fi for row in cross['samples'] if row['side']==side for fi in row['hoodieFaces']]);centers=p[f[faces]].mean(1);_,bodyface,bodydist,signed=classify(centers,side)
  for k,face in enumerate(faces):
   tri=p[f[face]];center=centers[k];station=(center-head)@axis;origin=head+station*axis;radial=center-origin;r=np.linalg.norm(radial);direction=radial/r;normal=np.cross(tri[1]-tri[0],tri[2]-tri[0]);normal/=np.linalg.norm(normal)
   hits=D['hits'](st,origin,direction,1.,1e-6);outward=[q[0] for q in hits if q[1]>0]
   source_faces.append({'side':side,'face':int(face),'sourceRows':f[face].tolist(),'sourceExteriorCorners':int(ext[f[face]].sum()),'sourceStationMeters':float(station),'sourceCornerStationsMeters':((tri-head)@axis).tolist(),'sourceRadiusMeters':float(r),'sourceNormalAlongAxis':float(normal@axis),'sourceNormalAlongRadial':float(normal@direction),'sourceOuterSheetAboveCentroidMeters':float(max(outward)-r) if outward else None,'sourceWearerSignedDistanceMeters':float(signed[k]),'sourceWearerDistanceMeters':float(bodydist[k]),'sourceWearerFace':int(bodyface[k])})
  sides[side]={'localfaces':localfaces,'head':head,'axis':axis}
 results=[];posecache={}
 for row in cross['samples']:
  if camera_mode=='focused' and row['tick'] not in [0,265,280,600,1200]:continue
  bike,tick,side=row['bike'],row['tick'],row['side'];g=comps['ActualSelectedGlove.'+side]
  if bike not in posecache:posecache[bike]={q['tick']:q for q in json.loads(Path(report['playedReports'][bike]['path']).read_text())['played']['motionSamples']}
  sample=posecache[bike][tick];byname={j['id']:j['worldMatrix'] for j in sample['joints']};world=np.array([byname[n] for n in names]).reshape(-1,4,4).transpose(0,2,1);mat=world@h['ib'];hp=D['skin'](z['positionsAfter'],z['jointsAfter'],z['weightsAfter'],mat);gp=D['skin'](g['POSITION'],g['JOINTS_0'],g['WEIGHTS_0'],mat)
  ht=D['tree'](hp,f);gt=D['tree'](gp,g['indices']);camera=np.array(sample['camera']['worldMatrix']).reshape(4,4).T;projection=np.array(sample['camera']['projectionMatrix']).reshape(4,4).T;origin=camera[:3,3];vp=projection@np.linalg.inv(camera)
  pairs=[]
  for pair in row['pairs']:
   point=np.array(pair['intersectionPoint']);ray=point-origin;dist=np.linalg.norm(ray);direction=ray/dist;hoodie_hits=D['hits'](ht,origin,direction,dist+.001,1e-6);glove_hits=D['hits'](gt,origin,direction,dist+.001,1e-6)
   front_hoodie=[q for q in hoodie_hits if q[1]<0];front_glove=glove_hits # selected gloves are double-sided
   hn=min(front_hoodie,key=lambda q:q[0]) if front_hoodie else None;gn=min(front_glove,key=lambda q:q[0]) if front_glove else None
   clip=vp@np.r_[point,1.];ndc=clip[:3]/clip[3]
   pairs.append({**pair,'hoodieCameraOcclusionMeters':float(dist-hn[0]) if hn else None,'hoodieOccluderFace':int(hn[2]) if hn else None,'gloveCameraOcclusionMeters':float(dist-gn[0]) if gn else None,'gloveOccluderFace':int(gn[2]) if gn else None,'nearestSurface':'hoodie' if hn and (not gn or hn[0]<gn[0]) else 'glove' if gn else None,'capturedNormalizedDeviceCoordinate':ndc.tolist()})
  results.append({'bike':bike,'tick':tick,'side':side,'pairs':pairs})
 output={'accepted':False,'schema':'selected-cuff-crossing-attribution-v1','candidatePatchSHA256':D['sha'](fit/'patch.npz'),'crossingReportSHA256':D['sha'](crossings_path),'cameraMode':camera_mode,'sourceFaceScopePoses':len(cross['samples'])//2,'sourceFaces':source_faces,'playedSamples':results,'elapsedSeconds':time.monotonic()-start,'limits':['Source exterior corner count and radial centroid depth describe folded-shell ownership; neither alone proves visibility from all directions.','Played camera occlusion is finite visibility at confirmed intersection points, not full adjacent-area or unseen-camera proof.','Native original played cameras are exact for the crossing pose reports; parent candidate02 movies remain independent appearance evidence.','No threshold was altered and no crossing was removed from the original rejected report.']}
 out.write_text(json.dumps(output,indent=2)+'\n');print(json.dumps({'faces':len(source_faces),'samples':len(results),'elapsedSeconds':output['elapsedSeconds']}),flush=True)
if __name__=='__main__':main(*sys.argv[sys.argv.index('--')+1:])
