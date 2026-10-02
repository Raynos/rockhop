"""Independent plane-equation and source-index check, without importing audit.py."""
import os
os.environ.setdefault('OPENBLAS_NUM_THREADS','2')
os.environ.setdefault('OMP_NUM_THREADS','2')
import json,hashlib
from pathlib import Path
import numpy as np
R=Path('/Users/raynos/projects/games/rockhop')
L=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2')
E=R/'docs/evidence/hero-remaster/one-rider-v2'
j=json.loads((E/'saddle-surface165/report.json').read_text())
results=[]
def raw(root,record,width):
 b=(root/record['file']).read_bytes();assert hashlib.sha256(b).hexdigest()==record['sha256'];return np.frombuffer(b,dtype='<f8').reshape(-1,width)
def plane(q,xz):return np.c_[xz,np.ones(len(xz))]@np.linalg.solve(np.c_[q[:,[0,2]],np.ones(3)],q[:,1])
def inside(q,xz):
 bary=np.linalg.solve(np.vstack([q[:,[0,2]].T,np.ones(3)]),np.c_[xz,np.ones(len(xz))].T).T
 assert bary.min()>-1e-6 and bary.max()<1+1e-6
for row in j['rows']:
 rel='rig-adapter01/body-bind34'if row['variant']=='physical34'else'garment-rebuild01/physical-v5-control157'
 folder=L/rel/'candidate-cpu';manifestpath=E/rel/'candidate-cpu/pose-manifest.json'
 if not manifestpath.exists():manifestpath=folder/'pose-manifest.json'
 m=json.loads(manifestpath.read_text());frame=next(x for x in m['rows']if x['i']==row['i']);p=raw(folder,frame['dump'][0]['positions'],3);t=raw(folder,m['primitives'][0]['index'],3).astype(int);bp=raw(folder,frame['bodyworkBikeFrame'],3);bt=raw(folder,m['bodyworkSource']['triangles'],3).astype(int)
 for kind,w in [('minimum',row['witness']),('crossing',row['first_surface_crossing_witness'])]:
  if w is None:continue
  h=p[t[w['rider_triangle_id']]];s=bp[bt[w['seat_source_bodywork_face']]];assert np.array_equal(h,w['rider_triangle_bike_frame_m']);assert np.array_equal(s,w['seat_triangle_bike_frame_m']);poly=np.array(w['overlap_polygon_xz_m']);inside(h,poly);inside(s,poly);gap=plane(h,poly)-plane(s,poly)
  if kind=='minimum':error=abs(gap.min()*1000-row['minimum_bike_frame_Y_gap_mm']);assert error<1e-7
  else:
   assert gap.min()<0 and gap.max()>0;segment=np.array(w['zero_gap_segment_xz_m']);assert len(segment)>=2;inside(h,segment);inside(s,segment);error=float(abs(plane(h,segment)-plane(s,segment)).max())*1000;assert error<1e-7
  results.append({'variant':row['variant'],'i':row['i'],'kind':kind,'plane_equation_error_mm':float(error),'rider_triangle':w['rider_triangle_id'],'seat_triangle':w['seat_source_bodywork_face']})
a={(x['i']):x for x in j['rows']if x['variant']=='physical34'};b={(x['i']):x for x in j['rows']if x['variant']=='physicalV5'}
for i in a:
 for field in ['state_sha256','camera_sha256','bones_sha256','bikeframe_bones_sha256','minimum_bike_frame_Y_gap_mm','finite_projection_pairs','surface_crossing_pairs']:assert a[i][field]==b[i][field]
out={'status':'FINITE_WITNESSES_REPRODUCED_NO_ACCEPTANCE','method':'Separate plane equation solve, barycentric inclusion, literal source triangle rows and actual position dump checks; no shared clipper.','results':results,'four_variant_pose_camera_state_hashes_match':True}
(E/'saddle-surface165/independent-check.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
