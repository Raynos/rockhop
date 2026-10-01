"""Independent polygon/area proof that surgery removes only declared apertures."""
from pathlib import Path
import json,numpy as np
ROOT=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/rig-adapter01/body-bind20')
EVIDENCE=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/body-bind20/construction01')
s=np.load(ROOT/'construction01/geometry-preexport.npz');sel=np.load(ROOT/'sheet-preflight01/sheet-selection.npz')
v=sel['sourcePositions'].astype(float);faces=sel['sourceTriangles'];positions=s['positions'].astype(float);updated=s['sourceTriangles'];origins=s['sourceTriangleProvenance']
inner=set(map(int,sel['inwardSourceFaces']));outer=set(map(int,sel['exteriorSourceFaces']))
order=np.argsort(origins,kind='stable');counts=np.bincount(origins,minlength=len(faces));offsets=np.r_[0,np.cumsum(counts)]
def polygon_area(poly):
    if len(poly)<3:return 0.
    p=np.array(poly);return abs(np.sum(p[:,0]*np.roll(p[:,1],-1)-p[:,1]*np.roll(p[:,0],-1)))/2
maximum_error=0.;modified=0;removed=0;rows=[]
for fi in inner|outer:
    width,height,minx=(.022,.017,.69) if fi in inner else (.018,.009,.72)
    triangle=v[faces[fi]];seed=None
    if triangle[:,0].min()>minx:
        for cy,cz in [(1.6965,.032),(1.697,-.0332)]:
            if triangle[:,1].min()<=cy+height and triangle[:,1].max()>=cy-height and triangle[:,2].min()<=cz+width and triangle[:,2].max()>=cz-width:
                seed=(cy,cz);break
    if seed is None:continue
    poly=[np.array([0.,0.]),np.array([1.,0.]),np.array([0.,1.])]
    yz=triangle[:,1:]-seed
    # Independent 2D polygon clipping in the original face's coefficient plane.
    for k in range(64):
        a=(k+.5)*2*np.pi/64
        plane=np.array([np.sin(a)/height,np.cos(a)/width]);value=yz@plane-np.cos(np.pi/64)
        def side(p):return value[0]+p[0]*(value[1]-value[0])+p[1]*(value[2]-value[0])
        output=[]
        for p,q in zip(poly,poly[1:]+poly[:1]):
            dp,dq=side(p),side(q);ip,iq=dp<=1e-12,dq<=1e-12
            if ip:output.append(p)
            if ip!=iq:output.append(p+(q-p)*dp/(dp-dq))
        poly=output
        if not poly:break
    clipped_fraction=2*polygon_area(poly)
    source_area=np.linalg.norm(np.cross(triangle[1]-triangle[0],triangle[2]-triangle[0]))/2
    expected=source_area*(1-clipped_fraction)
    ids=order[offsets[fi]:offsets[fi+1]];child=positions[updated[ids]]
    actual=np.linalg.norm(np.cross(child[:,1]-child[:,0],child[:,2]-child[:,0]),axis=1).sum()/2 if len(child) else 0.
    # Two float32 ULP coordinate bound, declared independently of the result.
    p32=np.concatenate([triangle,child.reshape(-1,3)]).astype('<f4')
    ulp=2*np.maximum(abs(np.nextafter(p32,np.float32(np.inf)).astype(float)-p32),abs(np.nextafter(p32,np.float32(-np.inf)).astype(float)-p32)).max(0)
    delta=np.linalg.norm(ulp)
    budget=np.sum(delta*(np.linalg.norm(child[:,1]-child[:,0],axis=1)+np.linalg.norm(child[:,2]-child[:,0],axis=1))+2*delta**2) if len(child) else 1e-14
    error=abs(actual-expected)
    assert error<=budget,(fi,error,budget,expected,actual)
    maximum_error=max(maximum_error,error)
    if clipped_fraction>1e-10:
        modified+=1;removed+=int(not len(child));rows.append({'sourceFace':int(fi),'removedFraction':float(clipped_fraction),'retainedChildren':len(child),'areaErrorM2':float(error),'float32AreaBudgetM2':float(budget)})
report={'status':'PASS independent declared-aperture retained-area proof','testedSourceFaces':len(rows),'completelyRemovedSourceFaces':removed,
    'maximumAreaErrorM2':float(maximum_error),'rows':rows,
    'limits':['Area proof complements protected-source union/interpolation coverage; it does not replace winding or texture checks.','This is CPU pre-export geometry evidence.']}
(EVIDENCE/'surgical-area-preexport.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='rows'},indent=2))
