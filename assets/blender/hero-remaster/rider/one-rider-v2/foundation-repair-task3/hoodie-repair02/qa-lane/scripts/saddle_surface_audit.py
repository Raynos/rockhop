from pathlib import Path
import sys,json
import numpy as np
ROOT=Path('/Users/raynos/projects/games/rockhop/assets/blender/hero-remaster/rider/one-rider-v2/foundation-repair-task3');Q=ROOT/'hoodie-repair02/qa-lane';OUT=Q/'uv-lower01';sys.path.insert(0,str(ROOT/'hoodie-repair02/scripts'));import base
bike={x['name']:x for x in json.loads((ROOT/'evidence/bike.json').read_text())};bp=np.array(bike['bodywork']['positions']);bt=np.array(bike['bodywork']['triangles']).reshape(-1,3);bq=bp[bt];normal=np.cross(bq[:,1]-bq[:,0],bq[:,2]-bq[:,0]);normal/=np.maximum(np.linalg.norm(normal,axis=1,keepdims=True),1e-15);sm=((bq[:,:,0]>=-.541)&(bq[:,:,0]<=-.049)&(bq[:,:,1]>=.5405)&(bq[:,:,1]<=.631)&(abs(bq[:,:,2])<=.069)).all(1)&(normal[:,1]>.3);SEAT=bq[sm];seatids=np.flatnonzero(sm)
TRI=np.concatenate([base.TRI[0],base.TRI[2]+base.OFF[2]]);REST=np.concatenate(base.POS);hip=((REST[TRI][:,:,1]>.69)&(REST[TRI][:,:,1]<1.08)&(abs(REST[TRI][:,:,2])<.245)).all(1);hipfaces=np.flatnonzero(hip);HT=TRI[hip]
# Exact verticalgap at convex intersections of projected trianglepairs. Bothheight fields linear.
def cross(a,b):return a[0]*b[1]-a[1]*b[0]
def clip(poly,triangle):
 if cross(triangle[1]-triangle[0],triangle[2]-triangle[0])<0:triangle=triangle[[0,2,1]]
 for i in range(3):
  a,b=triangle[i],triangle[(i+1)%3];edge=b-a;res=[]
  if not len(poly):break
  for p,q in zip(poly,np.roll(poly,-1,axis=0)):
   dp,dq=cross(edge,p-a),cross(edge,q-a);pin,qin=dp>=-1e-10,dq>=-1e-10
   if pin:res.append(p)
   if pin!=qin:
    den=dp-dq
    if abs(den)>1e-14:res.append(p+(q-p)*dp/den)
  poly=np.asarray(res,float).reshape(-1,2)
 return poly

def height(q,xz):
 m=np.array([q[1,[0,2]]-q[0,[0,2]],q[2,[0,2]]-q[0,[0,2]]]).T
 if abs(np.linalg.det(m))<1e-12:return None
 uv=(xz-q[0,[0,2]])@np.linalg.inv(m).T;return q[0,1]+uv[:,0]*(q[1,1]-q[0,1])+uv[:,1]*(q[2,1]-q[0,1])

manifest=json.loads((Q/'results/v7-export-motion-manifest-gate.json').read_text());r=next(r for r in manifest['rows']if r.get('time_s')==2.0);end=np.load(r['path']);D=end['matrices'];v7=np.load(ROOT/'hoodie-repair02/v7-bind.npz');fresh=base.deform([v7[f'p{i}']for i in range(5)],[v7[f'W{i}']for i in range(5)],D,closed=True);source=base.deform(base.POS,base.W,D,closed=True);sets=[('C19-raw-same-endpointD',source,base.TRI),('V7plain-same-endpointD',fresh,[v7[f'tr{i}']for i in range(5)]),('V7actual-export-endpoint', [end[f'p{i}']for i in range(5)],[v7[f'tr{i}']for i in range(5)])];rows=[]
for name,pts,tris in sets:
 t=np.concatenate([tris[0],tris[2]+base.OFF[2]]);roi=((REST[t][:,:,1]>.69)&(REST[t][:,:,1]<1.08)&(abs(REST[t][:,:,2])<.245)).all(1);hf=np.flatnonzero(roi);h= np.concatenate(pts)[t[roi]];hq=h[:,:,[0,2]];lo=hq.min(1);hi=hq.max(1);minimum=np.inf;witness=None;pairs=0;closeareas=0.
 for si,st in enumerate(SEAT):
  sq=st[:,[0,2]];cand=np.flatnonzero((lo<=sq.max(0)).all(1)&(hi>=sq.min(0)).all(1))
  for fi in cand:
   poly=clip(hq[fi].copy(),sq)
   if len(poly)<3:continue
   hy=height(h[fi],poly);sy=height(st,poly)
   if hy is None or sy is None:continue
   pairs+=1;g=hy-sy;worst=int(np.argmin(g));area=.5*abs(sum(cross(poly[i],poly[(i+1)%len(poly)])for i in range(len(poly))))
   if g.max()<=.003:closeareas+=area
   if g[worst]<minimum:minimum=float(g[worst]);witness={'hip_combined_face':int(hf[fi]),'hip_triangle_m':h[fi].tolist(),'seat_source_bodywork_face':int(seatids[si]),'seat_triangle_m':st.tolist(),'xz_minimum_point_m':poly[worst].tolist(),'cloth_height_m':float(hy[worst]),'seat_height_m':float(sy[worst]),'projected_intersection_polygon_xz_m':poly.tolist(),'projected_area_m2':float(area)}
 row={'variant':name,'finite_projection_intersection_pairs':pairs,'minimum_vertical_triangle_surface_gap_mm':minimum*1000 if np.isfinite(minimum)else None,'summed_projected_pair_area_with_entire_gap_le_3mm_m2':closeareas,'witness':witness,'gate':'NO_SUPPORT_HOVER'if minimum>.003 else'PENETRATION_OR_NEAR_CONTACT_REVIEW'};rows.append(row);print({k:v for k,v in row.items()if k!='witness'})
out={'source_endpoint_path':r['path'],'time_s':2.0,'same_world_D_for_all_variants':True,'rows':rows,'method':'Projectedtriangles clipped exactly inxz; linearheight difference minimum at convexintersection polygonvertices. Actual48upward saddlefaces, originalhiptriangle ROI.','limits':['Vertical clearances are not Euclidean closestdistance, ridercontactforce, friction or cloth thickness.','Projected overlapping foldedhipfaces may duplicate projectedarea; summedarea is not contactpatch area.','Fixed finite endpoint, no CCD; anatomicalbody geometry separatefrom garment is absent in source.']};(OUT/'saddle-triangle-surface-gap.json').write_text(json.dumps(out,indent=2))
