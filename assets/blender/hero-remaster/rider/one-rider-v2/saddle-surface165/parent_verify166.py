"""Parent read-only hash, plane and inside-triangle intersection verification."""
from pathlib import Path
import hashlib,json,subprocess
import numpy as np
R=Path('/Users/raynos/projects/games/rockhop')
OUT=R/'docs/evidence/hero-remaster/one-rider-v2/saddle-surface165'
reportPath=OUT/'report.json';report=json.loads(reportPath.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for name,row in report['input_files'].items():
 p=Path(name);assert sha(p)==row['sha256'] and p.stat().st_size==row['bytes']
def height_and_inside(tri,xz):
 tri=np.array(tri);v=np.array([xz[0],0,xz[1]])
 n=np.cross(tri[1]-tri[0],tri[2]-tri[0]);assert abs(n[1])>1e-12
 v[1]=(np.dot(n,tri[0])-n[0]*v[0]-n[2]*v[2])/n[1]
 A=np.column_stack((tri[1]-tri[0],tri[2]-tri[0]));uv=np.linalg.lstsq(A,v-tri[0],rcond=None)[0]
 assert np.linalg.norm(A@uv-(v-tri[0]))<1e-12
 assert uv.min()>-1e-9 and uv.sum()<1+1e-9
 return v
rows=[]
for row in report['rows']:
 w=row['witness'];a=height_and_inside(w['rider_triangle_bike_frame_m'],w['minimum_xz_m']);b=height_and_inside(w['seat_triangle_bike_frame_m'],w['minimum_xz_m'])
 assert abs((a[1]-b[1])*1000-row['minimum_bike_frame_Y_gap_mm'])<1e-9
 crossing=row.get('first_surface_crossing_witness');worst=0
 if crossing:
  assert row['i']==186 and row['phase']=='riding' and row['actual_rider_metadata']['debug']['physicalPose']
  assert row['grounded']==[False,False]
  for xz in crossing['zero_gap_segment_xz_m']:
   c=height_and_inside(crossing['rider_triangle_bike_frame_m'],xz);d=height_and_inside(crossing['seat_triangle_bike_frame_m'],xz);worst=max(worst,float(np.linalg.norm(c-d)));assert worst<1e-12
 rows.append({'variant':row['variant'],'frame':row['i'],'minimumGapMm':float((a[1]-b[1])*1000),'crossingSegmentPlaneResidualM':worst if crossing else None})
for i in [114,186,304,426]:
 a,b=[next(x for x in rows if x['frame']==i and x['variant']==v) for v in ['physical34','physicalV5']];assert a['minimumGapMm']==b['minimumGapMm']
matched=R/'docs/evidence/hero-remaster/one-rider-v2/garment-rebuild01/physical-v5-control157/played/matched';movies=[]
for view in ['side','rear-three-quarter']:
 for surface in ['gray','textured']:
  src=matched/(view+'-'+surface+'-before-after.mp4');dest=OUT/(view+'-'+surface+'-frames174-198.mp4');assert not dest.exists()
  cmd=['ffmpeg','-v','error','-i',str(src),'-vf','trim=start_frame=174:end_frame=199,setpts=PTS-STARTPTS','-c:v','libx264','-threads','2','-filter_threads','2','-crf','18','-pix_fmt','yuv420p','-an','-movflags','+faststart',str(dest)]
  subprocess.run(cmd,check=True);probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=width,height,r_frame_rate,nb_frames','-of','json',str(dest)],text=True));assert int(probe['streams'][0]['nb_frames'])==25
  movies.append({'source':str(src),'sourceSHA256':sha(src),'destination':dest.name,'sha256':sha(dest),'ffmpeg':cmd,'ffprobe':probe,'scope':'All25consecutive174–198frames, same old actual playback/cameras/poses; timing-preserving excerpt, not new rendering.'})
result={'kind':'Parent166 independent finite surface verification and moving-window preservation','inputHashFiles':len(report['input_files']),'reportSHA256':sha(reportPath),'rows':rows,'movies':movies,'parentVisualReview':'Ordered actual side-gray181–192 source moving window inspected. Hip/saddle silhouette remains unacceptable; individual triangle hidden-side visibility not accepted from these whole-body views. No fullmovie pass.','limits':'No anatomy/force/friction/device acceptance. Positive clearance is not automatically failed support. Extra maxforward/landing need explicit outer prefix or new authoritative dumps.'}
(OUT/'parent-verification166.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['movies','rows']}))
