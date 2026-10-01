"""One bounded local scalar clip + actual implicit garment-volume experiment.
CPU NumPy/SciPy/scikit-image only; source meshes remain read-only.
"""
from pathlib import Path
import numpy as np,json,time,resource,hashlib,traceback
from scipy.spatial import cKDTree
from skimage.measure import marching_cubes
ROOT=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/autonomous-lanes/B-local-volume')
RUN=ROOT/'trial01';t=time.monotonic();report={'status':'UNACCEPTED trial01','method':'40 mm continuous scalar local garment clipping + 1.5 mm implicit annulus marching cubes','priorNeckFailures':6,'thisMethodAttempt':1,'threads':2}

def loops(f):
    e=np.sort(np.concatenate((f[:,[0,1]],f[:,[1,2]],f[:,[2,0]])),axis=1);u,c=np.unique(e,axis=0,return_counts=True);be=u[c==1];g={}
    for a,b in be:g.setdefault(int(a),[]).append(int(b));g.setdefault(int(b),[]).append(int(a))
    if any(len(x)!=2 for x in g.values()):raise ValueError('Boundary degree violation: '+str({k:len(v) for k,v in g.items() if len(v)!=2}))
    ls=[];seen=set()
    for a in g:
        if a in seen:continue
        p=[];prev=-1;cur=a
        while cur not in seen:
            p.append(cur);seen.add(cur);n=g[cur];nxt=n[0] if n[0]!=prev else n[1];prev,cur=cur,nxt
        if cur!=a:raise ValueError('Noncircuit boundary')
        ls.append(np.array(p,np.int32))
    return ls,{'boundaryEdges':len(be),'nonmanifoldEdges':int(np.sum(c>2))}

def inside_dist(pts,poly):
    out=np.zeros(len(pts),bool);dist=np.full(len(pts),np.inf)
    for a,b in zip(poly,np.roll(poly,-1,axis=0)):
        ab=b-a;q=pts-a;tt=np.clip(q@ab/max(ab@ab,1e-15),0,1);dist=np.minimum(dist,np.linalg.norm(q-tt[:,None]*ab,axis=1))
        cross=(a[1]>pts[:,1])!=(b[1]>pts[:,1]); xx=(b[0]-a[0])*(pts[:,1]-a[1])/(b[1]-a[1]+1e-20)+a[0];out^=cross&(pts[:,0]<xx)
    return np.where(out,-dist,dist)

try:
    b=np.load(RUN/'body-source.npz');p=np.load(RUN/'retained-preflight.npz');v=b['vertices'];f=b['faces'];uv=b['allTriangleUV'];mi=b['materialIndex'];remove=p['removeSourceHead'];rim=p['boundaryIndices']
    distance=cKDTree(v[rim]).query(v,workers=2)[0];scalar=distance-.040
    verts=list(v.astype(float));newf=[];newuv=[];newmi=[];orig=[];interp={};edgecache={}
    for fi,face in enumerate(f):
        if remove[fi]:continue
        if np.all(scalar[face]>=0):newf.append(face.tolist());newuv.append(uv[:,fi]);newmi.append(int(mi[fi]));orig.append(fi);continue
        if np.all(scalar[face]<0):continue
        nodes=[(int(vi),uv[:,fi,k]) for k,vi in enumerate(face)];out=[]
        for (a,ua),(bb,ub) in zip(nodes,nodes[1:]+nodes[:1]):
            aa=scalar[a]>=0;bbin=scalar[bb]>=0
            if aa:out.append((a,ua))
            if aa!=bbin:
                frac=float(scalar[a]/(scalar[a]-scalar[bb]));key=tuple(sorted((a,bb)))
                if key not in edgecache:
                    edgecache[key]=len(verts);verts.append(v[a]+frac*(v[bb]-v[a]));interp[str(edgecache[key])]=[a,bb,frac]
                out.append((edgecache[key],ua+frac*(ub-ua)))
        for k in range(1,len(out)-1):
            tri=[out[0],out[k],out[k+1]];newf.append([x[0] for x in tri]);newuv.append(np.stack([x[1] for x in tri],axis=1));newmi.append(int(mi[fi]));orig.append(-1)
    vv=np.asarray(verts);ff=np.asarray(newf,np.int32);lu=np.stack(newuv,axis=1)
    np.savez(RUN/'clipped-panel.npz',vertices=vv,faces=ff,allTriangleUV=lu,materialIndex=np.array(newmi),faceOrigin=np.array(orig),originalVertexCount=len(v))
    ls,a=loops(ff);report['clipTopology']=a;report['clipBoundaryLoopLengths']=[len(x) for x in ls];report['preservedFullTriangles']=sum(x>=0 for x in orig);report['removedOriginalHeadTriangles']=int(remove.sum());report['clippedTriangles']=sum(x<0 for x in orig)
    if len(ls)!=1:raise ValueError('Local clip requires exactly one outer cloth contour, got '+str(len(ls)))
    outer=vv[ls[0]];report['outerBounds']=[outer.min(0).tolist(),outer.max(0).tolist()]
    # Measurement cross-section only: whole native head is preserved unchanged.
    h=np.load(RUN/'head-source.npz');hv=h['vertices'];hf=h['faces'];z=.0+1.505;sections=[]
    for tri in hv[hf]:
        pts=[]
        for a,b in zip(tri,np.roll(tri,-1,axis=0)):
            if (a[2]<z)!=(b[2]<z):pts.append(a+(z-a[2])/(b[2]-a[2])*(b-a))
        if len(pts)==2:sections.extend(pts)
    sec=np.unique(np.round(sections,6),axis=0);center=np.median(sec[:,:2],axis=0);ang=np.arctan2(sec[:,1]-center[1],sec[:,0]-center[0]);sec=sec[np.argsort(ang)];rad=sec[:,:2]-center;inner=sec.copy();inner[:,:2]+=rad/np.maximum(np.linalg.norm(rad,axis=1)[:,None],1e-10)*.005
    report['neckMeasurementZ']=z;report['clothClearanceMetres']=.005
    step=.0015;lo=outer.min(0)-[.006,.006,.012];hi=outer.max(0)+[.006,.006,.012];lo[2]=min(lo[2],z-.012);hi[2]=max(hi[2],z+.012)
    axes=[np.arange(lo[i],hi[i]+step,step) for i in range(3)];xx,yy=np.meshgrid(axes[0],axes[1],indexing='ij');xy=np.column_stack((xx.ravel(),yy.ravel()));dsout=inside_dist(xy,outer[:,:2]);dsin=inside_dist(xy,inner[:,:2]);report['innerOutsideOuterFraction']=float(np.mean(inside_dist(inner[:,:2],outer[:,:2])>0))
    if report['innerOutsideOuterFraction']>0:raise ValueError('Native neck opening is not contained in outer garment footprint')
    guide=np.vstack((outer,inner));dd,ii=cKDTree(guide[:,:2]).query(xy,k=12,workers=2);w=1/np.maximum(dd,.0008)**2;height=(w*guide[ii,2]).sum(1)/w.sum(1)
    field=np.maximum.reduce((np.abs(axes[2][None,:]-height[:,None])-.0025,np.broadcast_to(dsout[:,None],(len(xy),len(axes[2]))),np.broadcast_to(-dsin[:,None],(len(xy),len(axes[2]))))).reshape(len(axes[0]),len(axes[1]),len(axes[2])).astype(np.float32)
    np.savez_compressed(RUN/'implicit-field.npz',field=field,origin=lo,step=step,height=height.reshape(xx.shape))
    mv,mf,mn,_=marching_cubes(field,0,spacing=(step,step,step),allow_degenerate=False);mv+=lo
    cent=mv[mf].mean(1);dd,ii=cKDTree(guide[:,:2]).query(cent[:,:2],k=12,workers=2);w=1/np.maximum(dd,.0008)**2;hh=(w*guide[ii,2]).sum(1)/w.sum(1);nf=np.cross(mv[mf[:,1]]-mv[mf[:,0]],mv[mf[:,2]]-mv[mf[:,0]])
    top=(cent[:,2]>hh+.0002)&(np.abs(nf[:,2])/(np.linalg.norm(nf,axis=1)+1e-20)>.15);tf=mf[top]
    np.savez(RUN/'marching-volume.npz',vertices=mv,faces=mf,topFaces=tf)
    tls,ta=loops(tf);report['volumeGridShape']=list(field.shape);report['volumeBytes']=int(field.nbytes);report['marchingClosedVolumeVertices']=len(mv);report['marchingClosedVolumeFaces']=len(mf);report['topFaces']=len(tf);report['topTopology']=ta;report['topLoops']=[len(x) for x in tls]
    if len(tls)!=2:raise ValueError('Top sheet must have two genuine loops, got '+str(len(tls)))
    # Outer sheet is sewn to exact retained cloth boundary through zipper triangles.
    tls.sort(key=lambda l:float(np.mean(np.linalg.norm(mv[l,:2]-center,axis=1))),reverse=True);mcouter=tls[0]
    # Orient loop and rotate nearest starts. Source vertices are fixed throughout.
    aidx=ls[0];bidx=mcouter
    def sign(p):return np.sum(p[:,0]*np.roll(p[:,1],-1)-p[:,1]*np.roll(p[:,0],-1))
    if sign(vv[aidx,:2])*sign(mv[bidx,:2])<0:bidx=bidx[::-1]
    start=int(np.argmin(np.linalg.norm(mv[bidx]-vv[aidx[0]],axis=1)));bidx=np.roll(bidx,-start)
    aa=vv[aidx];bb=mv[bidx];alen=np.r_[0,np.cumsum(np.linalg.norm(np.roll(aa,-1,axis=0)-aa,axis=1))];blen=np.r_[0,np.cumsum(np.linalg.norm(np.roll(bb,-1,axis=0)-bb,axis=1))];alen/=alen[-1];blen/=blen[-1];offset=len(vv);bridge=[];i=j=0
    while i<len(aidx) or j<len(bidx):
        a0=int(aidx[i%len(aidx)]);b0=int(bidx[j%len(bidx)])+offset
        if j==len(bidx) or (i<len(aidx) and alen[i+1]<blen[j+1]):bridge.append([a0,int(aidx[(i+1)%len(aidx)]),b0]);i+=1
        else:bridge.append([a0,int(bidx[(j+1)%len(bidx)])+offset,b0]);j+=1
    finalv=np.vstack((vv,mv));newpart=np.vstack((tf+offset,np.asarray(bridge)));finalf=np.vstack((ff,newpart));puv=np.zeros((uv.shape[0],len(newpart),3,2),np.float32);puv[:]=((finalv[newpart,:,:2]-lo[:2])/(hi[:2]-lo[:2]))[None]
    finaluv=np.concatenate((lu,puv),axis=1);finalmi=np.r_[newmi,np.full(len(newpart),2)];finalorigin=np.r_[orig,np.full(len(newpart),-2)]
    fl,fa=loops(finalf);report['finalBodyTopology']=fa;report['finalBodyLoops']=[len(x) for x in fl];report['outerSeamSharedVertices']=len(aidx);report['nativeHeadGeometryChanged']=False
    np.savez(RUN/'reconstructed-body.npz',vertices=finalv,faces=finalf,allTriangleUV=finaluv,materialIndex=finalmi,faceOrigin=finalorigin,originalVertexCount=len(v));(RUN/'interpolated-vertex-weights.json').write_text(json.dumps(interp))
    report['status']='UNACCEPTED geometry constructed; requires actual visual judgment'
except Exception as e:
    report['status']='FAILED geometry gate, one lane B attempt';report['error']=str(e);report['traceback']=traceback.format_exc()
finally:
    report['elapsedSeconds']=time.monotonic()-t;report['peakRSSBytes']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss;report['recipeSHA256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest();(RUN/'volume-report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
