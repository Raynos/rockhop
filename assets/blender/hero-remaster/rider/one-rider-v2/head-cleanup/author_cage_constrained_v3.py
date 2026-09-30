"""Explicit authored topology feasibility, NOT another source-contour repair.

Face chart has deliberate eyelid/lip/nostril loops. Ears have concha/helix
rings sewn to defined side-chart holes. Crown and neck rings are authored.
Initial source-guide placement and subsequent bounded dense fit are separate.
"""
import argparse, hashlib, json, math
from pathlib import Path
import numpy as np
import triangle
ap=argparse.ArgumentParser(description=__doc__)
ap.add_argument('--out',required=True);a=ap.parse_args();out=Path(a.out)
out.mkdir(parents=True,exist_ok=True)
if (out/'layout.npz').exists():raise RuntimeError('Frozen layout exists')
verts=[];faces=[];region=[];landmark=[]
def add(p,guide=0,feature=0):
    verts.append(list(p));region.append(guide);landmark.append(feature);return len(verts)-1
def quad(a,b,c,d):faces.extend(((a,b,c),(a,c,d)))
ys=np.unique(np.round(np.r_[np.arange(-.31,.2051,.005),-.15,-.02,.125],6))
theta=np.arange(120)*2*math.pi/120
profile_y=np.array([-.31,-.25,-.18,-.15,-.13,-.07,0,.11,.205])
profile_x=np.array([.20,.12,.11,.13,.145,.175,.185,.20,.19])
front=np.array([.16,.15,.15,.17,.18,.22,.24,.18,.17])
back=np.array([-.07,-.08,-.12,-.14,-.155,-.20,-.23,-.25,-.20])
def width(y):return np.interp(y,profile_y,profile_x)*math.sin(math.pi/3)
ids=[]
for y in ys:
    rx=np.interp(y,profile_y,profile_x);zf=np.interp(y,profile_y,front);zb=np.interp(y,profile_y,back)
    row=[]
    for t in theta:
        p=[rx*math.sin(t),y,(zf+zb)/2+(zf-zb)/2*math.cos(t)]
        guide=1 if (t<=math.pi/3+1e-6 or t>=5*math.pi/3-1e-6) and -.15-1e-6<=y<=.2051 else 0
        row.append(add(p,guide,0))
    ids.append(row)
ids=np.array(ids)
bottom=int(np.where(np.isclose(ys,-.15))[0][0]);top=len(ys)-1
ear_bottom=int(np.where(np.isclose(ys,-.02))[0][0]);ear_top=int(np.where(np.isclose(ys,.125))[0][0])
front_indices=list(range(100,120))+list(range(0,21))
ear_sectors=[(20,35,1),(85,100,-1)]
for j in range(len(ys)-1):
    for i in range(120):
        nxt=(i+1)%120
        is_front=(i>=100 or i<20) and bottom<=j<top
        is_ear=ear_bottom<=j<ear_top and any(lo<=i<hi for lo,hi,s in ear_sectors)
        if is_front or is_ear:continue
        quad(ids[j,i],ids[j,nxt],ids[j+1,nxt],ids[j+1,i])
# The scalp has ONE deliberately authored 120-vertex contour.
previous=ids[-1];crown_rings=[]
for y in np.linspace(.205,.34,16)[1:-1]:
    fac=math.sqrt(max(0,1-((y-.10)/.24)**2)/(1-((.205-.10)/.24)**2))
    row=np.array([add([.19*fac*math.sin(t),y,-.015+.185*fac*math.cos(t)],0,6) for t in theta])
    for i in range(120):quad(previous[i],previous[(i+1)%120],row[(i+1)%120],row[i])
    crown_rings.append(row);previous=row
apex=add([0,.34,-.015],0,6)
for i in range(120):faces.append((previous[i],previous[(i+1)%120],apex))
# Front skin is a planar semantic chart in q=X/width(Y), Y, not radial mapping.
chart=[];chart_ids=[]
def chart_add(idx):
    p=verts[idx];chart.append([p[0]/width(p[1]),p[1]]);chart_ids.append(idx)
for j in range(bottom,top+1):
    chart_add(int(ids[j,20]));chart_add(int(ids[j,100]))
for j in (bottom,top):
    for i in front_indices[1:-1]:chart_add(int(ids[j,i]))
# Rings' semantic values derive from measured source landmarks, native Y up.
features=[dict(name='left eyelid',x=-.081,y=.111,rx=.048,ry=.026,code=1),
          dict(name='right eyelid',x=.081,y=.111,rx=.048,ry=.026,code=1),
          dict(name='lip',x=0,y=-.032,rx=.070,ry=.024,code=2),
          dict(name='left nostril',x=-.024,y=.025,rx=.012,ry=.008,code=3),
          dict(name='right nostril',x=.024,y=.025,rx=.012,ry=.008,code=3)]
def in_hole(x,y):return any(((x-h['x'])/h['rx'])**2+((y-h['y'])/h['ry'])**2<1.02 for h in features)
for y in np.arange(-.145,.2001,.006):
    for q in np.arange(-.97,.971,.035):
        x=q*width(y)
        if in_hole(x,y):continue
        idx=add([x,y,.16],1,0);chart_add(idx)
feature_reports=[];outer_feature={}
for h in features:
    count=48 if h['code']!=3 else 32
    angles=np.arange(count)*2*math.pi/count
    outer=[]
    for t in angles:
        idx=add([h['x']+h['rx']*math.cos(t),h['y']+h['ry']*math.sin(t),.18],1,h['code'])
        outer.append(idx);chart_add(idx)
    for idx in outer:outer_feature[idx]=len(feature_reports)
    previous=np.array(outer);rings=[outer]
    fractions=[.86,.72,.58,.42,.25,.12]
    for fraction in fractions:
        row=np.array([add([h['x']+h['rx']*fraction*math.cos(t),h['y']+h['ry']*fraction*math.sin(t),.18],1,h['code']) for t in angles])
        for i in range(count):quad(previous[i],previous[(i+1)%count],row[(i+1)%count],row[i])
        rings.append(row.tolist());previous=row
    center=add([h['x'],h['y'],.18],1,h['code'])
    for i in range(count):faces.append((previous[i],previous[(i+1)%count],center))
    feature_reports.append(dict(**h,ringVertices=count,concentricRings=len(rings)))
# Extra nose bridge/wing points enforce explicit longitudinal anatomy flow.
for y in [.045,.060,.075,.09,.105,.13,.15]:
    for x in [-.020,-.010,0,.010,.020]:
        if in_hole(x,y):continue
        idx=add([x,y,.23],1,4);chart_add(idx)
uv=np.array(chart);index=np.array(chart_ids)
# Drop duplicate boundary corner references without altering authored coordinates.
_,first=np.unique(np.round(uv,9),axis=0,return_index=True)
uv=uv[np.sort(first)];index=index[np.sort(first)]
chart_lookup={int(global_id):local_id for local_id,global_id in enumerate(index)}
outer=list(ids[bottom,front_indices])
outer+=list(ids[bottom+1:top+1,20])
outer+=list(ids[top,front_indices[:-1][::-1]])
outer+=list(ids[bottom+1:top,100][::-1])
polygons=[outer]
for hindex in range(len(features)):
    polygons.append([idx for idx,group in outer_feature.items() if group==hindex])
segments=[]
for polygon in polygons:
    local=[chart_lookup[int(x)] for x in polygon]
    segments.extend((local[i],local[(i+1)%len(local)]) for i in range(len(local)))
holes=np.array([[h['x']/width(h['y']),h['y']] for h in features])
constraints=dict(vertices=uv,segments=np.array(segments,dtype=np.int32),holes=holes)
result=triangle.triangulate(constraints,'pQ')
if len(result['vertices'])>len(index):
    extra=[]
    for q,y in result['vertices'][len(index):]:extra.append(add([q*width(y),y,.16],1,0))
    index=np.r_[index,extra]
for tt in result['triangles']:faces.append(tuple(index[tt]))
# Ear holes have authored perimeter IDs, with helix and concha loops sharing them.
ear_reports=[]
for lo,hi,side in ear_sectors:
    boundary=list(ids[ear_bottom,lo:hi+1])
    boundary+=list(ids[ear_bottom+1:ear_top+1,hi])
    boundary+=list(ids[ear_top,lo:hi][::-1])
    boundary+=list(ids[ear_bottom+1:ear_top,lo][::-1])
    n=len(boundary);ang=np.arange(n)*2*math.pi/n+math.pi/2
    previous=np.array(boundary);rings=[]
    for radius,depth in [(1,0),(.87,.007),(.70,-.006),(.52,-.018),(.32,-.010),(.12,-.016)]:
        row=[]
        for t in ang:
            u,v=radius*math.cos(t),radius*math.sin(t)
            x=side*(.227+.025*u+.008*radius+depth*.35)
            y=.052+.073*v
            z=.077-.010*u+depth
            row.append(add([x,y,z],2,5))
        row=np.array(row)
        for i in range(n):quad(previous[i],previous[(i+1)%n],row[(i+1)%n],row[i])
        previous=row;rings.append(row.tolist())
    center=add([side*.225,.052,.055],2,5)
    for i in range(n):faces.append((previous[i],previous[(i+1)%n],center))
    ear_reports.append(dict(side=side,sharedBaseVertices=n,helixConchaRings=len(rings)))
v=np.array(verts,dtype=np.float32);f=np.array(faces,dtype=np.int32)
used,inv=np.unique(f,return_inverse=True)
v=v[used];f=inv.reshape(-1,3).astype(np.int32)
region=np.array(region,dtype=np.int32)[used];landmark=np.array(landmark,dtype=np.int32)[used]
e,c=np.unique(np.sort(np.concatenate((f[:,[0,1]],f[:,[1,2]],f[:,[2,0]])),axis=1),axis=0,return_counts=True)
np.savez(out/'layout.npz',vertices=v,faces=f,guide_region=region,landmark=landmark)
report=dict(status='UNACCEPTED authored topology feasibility; not fitted',
            vertices=len(v),faces=len(f),boundaryEdges=int(np.sum(c==1)),
            nonmanifoldEdges=int(np.sum(c>2)),features=feature_reports,ears=ear_reports,
            scalpRingVertices=120,neckRows=bottom+1,headTopNativeY=.34,
            scriptSHA256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            constrainedTriangulation=dict(package='triangle',version=triangle.__version__,
                options='pQ',segments=len(segments),holes=len(holes),
                additionalVertices=len(result['vertices'])-len(uv)),
            limits=['Front chart uses authored feature rings, not a source mesh cut.',
                    'Ear folds are explicit authored rings; their shape still requires source review.',
                    'Initial source-guided placement is not bounded dense fitting.'])
(out/'layout.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if report['nonmanifoldEdges'] or report['boundaryEdges']!=120:
    raise RuntimeError('Authored initial topology gate failed; no fitting')
