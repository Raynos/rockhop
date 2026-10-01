"""Analytic projected overlap proof for two piecewise planar skin caps."""
import numpy as np

def cross(a,b):return a[0]*b[1]-a[1]*b[0]

def clip_triangle(subject,triangle):
 polygon=[p.copy() for p in subject]
 if cross(triangle[1]-triangle[0],triangle[2]-triangle[0])<0:triangle=triangle[::-1]
 for a,b in zip(triangle,np.roll(triangle,-1,axis=0)):
  if not polygon:break
  result=[];previous=polygon[-1];dp=cross(b-a,previous-a)
  for current in polygon:
   dc=cross(b-a,current-a);inside=dc>=-1e-12;previousInside=dp>=-1e-12
   if inside!=previousInside:
    denom=dp-dc
    if abs(denom)>1e-20:result.append(previous+(current-previous)*(dp/denom))
   if inside:result.append(current)
   previous,dp=current,dc
  polygon=result
 return np.array(polygon)

def z_at(triangle,xy):
 a,b,c=triangle;matrix=np.stack((b[:2]-a[:2],c[:2]-a[:2]),axis=1)
 weights=(xy-a[:2])@np.linalg.inv(matrix).T
 return a[2]+weights[:,0]*(b[2]-a[2])+weights[:,1]*(c[2]-a[2])

def verify_sheet_thickness(exterior,inner,minimum=1e-5):
 front=exterior['vertices'][exterior['triangles']].astype(np.float64);back=inner['vertices'][inner['triangles']].astype(np.float64);smallest=float('inf');polygons=0;vertices=0;witness=None
 for i,a in enumerate(front):
  if abs(cross(a[1,:2]-a[0,:2],a[2,:2]-a[0,:2]))<1e-14:continue
  lo=a[:,:2].min(0);hi=a[:,:2].max(0)
  for j,b in enumerate(back):
   if abs(cross(b[1,:2]-b[0,:2],b[2,:2]-b[0,:2]))<1e-14:continue
   if np.any(b[:,:2].max(0)<lo) or np.any(b[:,:2].min(0)>hi):continue
   polygon=clip_triangle(a[:,:2],b[:,:2])
   if len(polygon)<3:continue
   area=abs(sum(cross(p,q) for p,q in zip(polygon,np.roll(polygon,-1,axis=0))))*.5
   if area<1e-13:continue
   gap=z_at(b,polygon)-z_at(a,polygon);index=int(np.argmin(gap));value=float(gap[index]);polygons+=1;vertices+=len(polygon)
   if value<smallest:smallest=value;witness={'exteriorTriangle':i,'innerTriangle':j,'xyLocal':polygon[index].tolist(),'localThickness':value}
 return {'method':'Clip every projected cap triangle pair; affine depth difference reaches its minimum at convex overlap vertices.','analyticProjectedOverlapPolygons':polygons,'analyticOverlapVertices':vertices,'minimumLocalThickness':smallest if polygons else None,'minimumAllowedLocalThickness':minimum,'positiveThicknessAndCapNonintersection':polygons>0 and smallest>minimum,'minimumWitness':witness,'limits':['Floating-point polygon clipping tolerance 1e-12; zero-area overlaps excluded below 1e-13.','This proves relative cap depths in projected overlap, not all-source self-intersection or character acceptance.']}
