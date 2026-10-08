"""Fixed six-landmark sewn underarm pattern. Numpy only; no scene mutation."""
import numpy as np
PATTERN=np.array([[0,0],[0,.5],[0,1],[1,1],[1,.5],[1,0]],float)
def curve(values,metric=None):
 values=np.asarray(values,float);lengths=np.linalg.norm(np.diff(values if metric is None else metric,axis=0),axis=1);knots=np.r_[0,np.cumsum(lengths)];assert knots[-1]>1e-8;knots/=knots[-1]
 def at(t):
  k=min(len(values)-2,max(0,int(np.searchsorted(knots,t,side='right')-1)));f=(t-knots[k])/(knots[k+1]-knots[k]);return values[k]*(1-f)+values[k+1]*f
 return knots,at
def layout(boundary,anchor_ids,positions):
 boundary=list(boundary);start=boundary.index(anchor_ids[0]);boundary=boundary[start:]+boundary[:start]
 sign=1
 if [boundary.index(i)for i in anchor_ids]!=sorted(boundary.index(i)for i in anchor_ids):
  boundary=boundary[:1]+boundary[:0:-1];sign=-1
 offsets=[boundary.index(i)for i in anchor_ids]+[len(boundary)];assert offsets==sorted(offsets)
 arcs=[];params={}
 for k in range(6):
  arc=boundary[offsets[k]:offsets[k+1]]+[boundary[offsets[k+1]%len(boundary)]];arcs.append(arc);knots,_=curve(positions[arc])
  for i,t in zip(arc,knots):params[i]=PATTERN[k]*(1-t)+PATTERN[(k+1)%6]*t
 return boundary,arcs,params,sign
def correspondence(values,arcs,positions):
 _,AT=curve(values[arcs[0]],positions[arcs[0]]);_,TB=curve(values[arcs[1]],positions[arcs[1]]);_,BC=curve(values[arcs[2]],positions[arcs[2]])
 _,SD=curve(values[arcs[4][::-1]],positions[arcs[4][::-1]]);_,CS=curve(values[arcs[3][::-1]],positions[arcs[3][::-1]]);_,AD=curve(values[arcs[5][::-1]],positions[arcs[5][::-1]])
 A,T,B,C,S,D=[values[a[0]]for a in arcs]
 def at(u,v):
  if v<=.5:
   t=v*2;left,right,top,bottom=AT(t),SD(t),AD(u),(1-u)*T+u*S;corners=(A,D,T,S)
  else:
   t=(v-.5)*2;left,right,top,bottom=TB(t),CS(t),(1-u)*T+u*S,BC(u);corners=(T,S,B,C)
  a,b,c,d=corners
  bilinear=(1-t)*(1-u)*a+(1-t)*u*b+t*(1-u)*c+t*u*d
  return (1-u)*left+u*right+(1-t)*top+t*bottom-bilinear
 return at
def cloth_surface(outer_anchors,side,controls):
 A,T,B,C,S,D=np.asarray(outer_anchors,float);sign=1 if side=='L'else-1
 def mid(u,v):
  front=v<=.5;t=v*2 if front else (1-v)*2
  P,Q=(A,D)if front else(B,C)
  x0=(1-t)*abs(P[0])+t*controls['torsoUnderarmXM'];x1=(1-t)*abs(Q[0])+t*controls['sleeveUnderarmXM']
  top=(1-u)*P[2]+u*Q[2]+4*u*(1-u)*(controls['shoulderBridgeZM']-(P[2]+Q[2])*.5)
  z=(1-t)*top+t*controls['underarmSeamZM']
  depth=controls['frontDepthM']if front else controls['rearDepthM']
  y=(-1 if front else 1)*depth*(1-t**4)
  return np.array([sign*((1-u)*x0+u*x1),y,z])
 def at(u,v,interior):
  p=mid(u,v)
  if interior:
   e=1e-5;du=mid(min(1,u+e),v)-mid(max(0,u-e),v);dv=mid(u,min(1,v+e))-mid(u,max(0,v-e));normal=np.cross(du,dv);normal*=(-1 if side=='L'else 1);normal/=np.linalg.norm(normal)
   p=p-controls['clothThicknessM']*normal
  return p
 return at
def phase(st):
 u,v=st
 if abs(u)<1e-7:return v
 if abs(v-1)<1e-7:return 1+u
 if abs(u-1)<1e-7:return 3-v
 assert abs(v)<1e-7;return 4-u

def patch(boundary,anchor_ids,positions,raw,fields,side,interior,outer_anchors,controls):
 ordered,arcs,outer_uv,orientation=layout(boundary,anchor_ids,positions)
 identity=correspondence(raw,arcs,positions);weight=correspondence(fields,arcs,positions);surface=cloth_surface(outer_anchors,side,controls)
 nx,ny=controls['columns'],controls['rows'];assert ny%2==0
 points=[];identities=[];weights=[];uvs=[];grid={}
 for j in range(ny+1):
  for i in range(nx+1):
   u,v=i/nx,j/ny;grid[i,j]=len(points);points.append(surface(u,v,interior));identities.append(identity(u,v));w=np.maximum(weight(u,v),0);assert w.sum()>1e-8;weights.append(w/w.sum());uvs.append(.12+.76*np.array([u,v]))
 grid_faces=[]
 for j in range(ny):
  for i in range(nx):grid_faces.append([grid[i,j],grid[i,j+1],grid[i+1,j+1],grid[i+1,j]])
 perimeter=([grid[0,j]for j in range(ny)]+[grid[i,ny]for i in range(nx)]+[grid[nx,j]for j in range(ny,0,-1)]+[grid[i,0]for i in range(nx,0,-1)])
 inner_phase=[phase(((uvs[k]-.12)/.76))for k in perimeter];outer_phase=[phase(outer_uv[k])for k in ordered]
 assert inner_phase==sorted(inner_phase)and outer_phase==sorted(outer_phase)
 # Negative indices identify retained cut-boundary vertices; generated indices
 # identify the two sewn regular panels. A monotone zipper handles unequal
 # edge counts without forcing arbitrary old boundary IDs into grid corners.
 annulus=[];i=j=0;no,ni=len(ordered),len(perimeter)
 while i<no or j<ni:
  a=-(ordered[i%no]+1);b=perimeter[j%ni]
  nextouter=outer_phase[(i+1)%no]+(4 if i+1>=no else 0)
  nextinner=inner_phase[(j+1)%ni]+(4 if j+1>=ni else 0)
  if i<no and(j>=ni or nextouter<=nextinner):annulus.append([a,-(ordered[(i+1)%no]+1),b]);i+=1
  else:annulus.append([a,perimeter[(j+1)%ni],b]);j+=1
 faces=grid_faces+annulus
 if orientation<0:faces=[f[::-1]for f in faces]
 return {'positions':np.asarray(points),'raw':np.asarray(identities),'weights':np.asarray(weights),'UV':np.asarray(uvs),'outerUV':outer_uv,'faces':faces,'regularQuads':len(grid_faces),'transitionTriangles':len(annulus),'orientation':orientation}
