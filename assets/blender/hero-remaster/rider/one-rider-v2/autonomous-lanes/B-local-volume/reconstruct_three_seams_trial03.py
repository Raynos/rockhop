"""Actual local implicit garment volumes for three physical cloth seams.
Frozen failed Euclidean/intrinsic annulus gates remain unchanged. CPU only.
Architecture: one neck annulus + two posterior hole caps; entire native skin fixed.
"""
from pathlib import Path
import numpy as np,json,time,resource,hashlib,traceback
from scipy.spatial import cKDTree
from skimage.measure import marching_cubes
ROOT=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/autonomous-lanes/B-local-volume');SRC=ROOT/'trial02';RUN=ROOT/'trial03';RUN.mkdir(exist_ok=True)
t=time.monotonic();report={'status':'UNACCEPTED trial03','architecture':'actual implicit neck annulus plus two implicit cloth cap volumes; top-sheet extraction and indexed source-cloth seams','priorLaneBFailures':2,'priorOriginalNeckFailures':6,'parentDefectFamilyAtStart':11,'threads':2,'voxelStepMetres':.0015,'volumeHalfThicknessMetres':.0025,'nativeHeadChanged':False,'patches':[]}
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def loops(f):
    ed=np.concatenate((f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]));e=np.sort(ed,axis=1);u,c=np.unique(e,axis=0,return_counts=True);be=u[c==1];g={}
    for a,b in be:g.setdefault(int(a),[]).append(int(b));g.setdefault(int(b),[]).append(int(a))
    if any(len(x)!=2 for x in g.values()):raise ValueError('Boundary degree violation '+str({k:len(x) for k,x in g.items() if len(x)!=2}))
    ls=[];seen=set()
    for a in g:
        if a in seen:continue
        p=[];prev=-1;cur=a
        while cur not in seen:
            p.append(cur);seen.add(cur);ns=g[cur];nx=ns[0] if ns[0]!=prev else ns[1];prev,cur=cur,nx
        if cur!=a:raise ValueError('Noncircuit')
        pp=np.array(p,np.int32)
        if not np.any(np.all(ed==pp[:2],axis=1)):pp=pp[::-1]
        ls.append(pp)
    return ls,dict(boundaryEdges=len(be),nonmanifoldEdges=int(np.sum(c>2)))

def inside_dist(pts,poly):
    out=np.zeros(len(pts),bool);dist=np.full(len(pts),np.inf)
    for a,b in zip(poly,np.roll(poly,-1,axis=0)):
        ab=b-a;q=pts-a;tt=np.clip(q@ab/max(ab@ab,1e-15),0,1);dist=np.minimum(dist,np.linalg.norm(q-tt[:,None]*ab,axis=1));cross=(a[1]>pts[:,1])!=(b[1]>pts[:,1]);xx=(b[0]-a[0])*(pts[:,1]-a[1])/(b[1]-a[1]+1e-20)+a[0];out^=cross&(pts[:,0]<xx)
    return np.where(out,-dist,dist)

def guideheight(xy,guide):
    dd,ii=cKDTree(guide[:,:2]).query(xy,k=min(12,len(guide)),workers=2);w=1/np.maximum(dd,.0008)**2;return (w*guide[ii,2]).sum(1)/w.sum(1)

def volume_patch(label,outer,inner=None):
    step=.0015;guide=outer if inner is None else np.vstack((outer,inner));lo=guide.min(0)-[.006,.006,.012];hi=guide.max(0)+[.006,.006,.012];axes=[np.arange(lo[i],hi[i]+step,step) for i in range(3)];xx,yy=np.meshgrid(axes[0],axes[1],indexing='ij');xy=np.column_stack((xx.ravel(),yy.ravel()));dsout=inside_dist(xy,outer[:,:2]);height=guideheight(xy,guide);annulus=(inner is not None)
    field=np.maximum(np.abs(axes[2][None,:]-height[:,None])-.0025,dsout[:,None])
    pr=dict(name=label,gridShape=[len(a) for a in axes],step=step,outerSeamVertices=len(outer),innerOpeningVertices=0 if inner is None else len(inner))
    if annulus:
        outside=float(np.mean(inside_dist(inner[:,:2],outer[:,:2])>0));pr['innerOutsideOuterFraction']=outside
        if outside>0:raise ValueError('Measured native neck opening is outside main cloth footprint '+str(outside))
        field=np.maximum(field,-inside_dist(xy,inner[:,:2])[:,None])
    field=field.reshape(len(axes[0]),len(axes[1]),len(axes[2])).astype(np.float32);pr['fieldBytes']=int(field.nbytes);np.savez_compressed(RUN/(label+'-field.npz'),field=field,origin=lo,step=step)
    mv,mf,_,_=marching_cubes(field,0,spacing=(step,step,step),allow_degenerate=False);mv+=lo
    cls,ct=loops(mf);pr['closedVolumeTopology']=ct;pr['closedVolumeBoundaryLoops']=len(cls);pr['volumeVertices']=len(mv);pr['volumeFaces']=len(mf)
    if cls or ct['nonmanifoldEdges']:raise ValueError('Actual implicit volume not closed manifold')
    # Surgically cut volume at its measured middle height: retain top + upper rim.
    scalar=mv[:,2]-guideheight(mv[:,:2],guide);vs=list(mv);fs=[];edgecache={}
    for face in mf:
        if np.all(scalar[face]>=0):fs.append(face.tolist());continue
        if np.all(scalar[face]<0):continue
        nodes=[int(x) for x in face];out=[]
        for a,b in zip(nodes,nodes[1:]+nodes[:1]):
            if scalar[a]>=0:out.append(a)
            if (scalar[a]>=0)!=(scalar[b]>=0):
                key=tuple(sorted((a,b)));frac=float(scalar[a]/(scalar[a]-scalar[b]))
                if key not in edgecache:edgecache[key]=len(vs);vs.append(mv[a]+frac*(mv[b]-mv[a]))
                out.append(edgecache[key])
        for k in range(1,len(out)-1):fs.append([out[0],out[k],out[k+1]])
    vv=np.array(vs);ff=np.array(fs,np.int32);norm=np.cross(vv[ff[:,1]]-vv[ff[:,0]],vv[ff[:,2]]-vv[ff[:,0]])
    if np.sum(norm[:,2])<0:ff=ff[:,::-1]
    ls,topo=loops(ff);pr['sheetTopology']=topo;pr['sheetLoopLengths']=[len(x) for x in ls]
    np.savez(RUN/(label+'-volume-and-sheet.npz'),vertices=mv,closedFaces=mf,sheetVertices=vv,sheetFaces=ff)
    report['patches'].append(pr)
    if len(ls)!=(2 if annulus else 1):raise ValueError('Unexpected actual extracted sheet contours: '+label+' '+str([len(x) for x in ls]))
    return vv,ff,ls

def sew(verts,sourceLoop,pv,pf,ploop):
    aa=verts[sourceLoop];bb=pv[ploop]
    # Match cyclic ordering geometrically, then reverse body-directed seam edges.
    def sg(p):return np.sum(p[:,0]*np.roll(p[:,1],-1)-p[:,1]*np.roll(p[:,0],-1))
    if sg(aa)*sg(bb)<0:ploop=ploop[::-1];bb=pv[ploop]
    j=int(np.argmin(np.linalg.norm(bb-aa[0],axis=1)));ploop=np.roll(ploop,-j);bb=pv[ploop];off=len(verts)
    al=np.r_[0,np.cumsum(np.linalg.norm(np.roll(aa,-1,axis=0)-aa,axis=1))];bl=np.r_[0,np.cumsum(np.linalg.norm(np.roll(bb,-1,axis=0)-bb,axis=1))];al/=al[-1];bl/=bl[-1];fs=[];i=j=0
    while i<len(aa) or j<len(bb):
        a0=int(sourceLoop[i%len(aa)]);b0=int(ploop[j%len(bb)])+off
        if j==len(bb) or (i<len(aa) and al[i+1]<bl[j+1]):fs.append([int(sourceLoop[(i+1)%len(aa)]),a0,b0]);i+=1
        else:fs.append([a0,b0,int(ploop[(j+1)%len(bb)])+off]);j+=1
    return np.vstack((verts,pv)),np.vstack((pf+off,np.array(fs))),dict(sharedSourceBoundaryVertices=len(sourceLoop),sewnSheetBoundaryVertices=len(ploop),bridgeTriangles=len(fs),maximumBridgeNearestDistance=float(cKDTree(aa).query(bb,workers=2)[0].max()))
try:
    d=np.load(SRC/'clipped-panel.npz');v=d['vertices'];f=d['faces'];uv=d['allTriangleUV'];mi=d['materialIndex'];origin=d['faceOrigin'];ls,top=loops(f);ls.sort(key=len,reverse=True);assert [len(x) for x in ls]==[194,43,23]
    report['sourceSHA256']={str(p):sha(p) for p in [SRC/'clipped-panel.npz',SRC/'head-source.npz',SRC/'exact-three-loops.json']};report['sourceClothLoops']=[len(x) for x in ls]
    # Native skin cross-section used only as a clearance measurement; skin never cut.
    h=np.load(SRC/'head-source.npz');hv=h['vertices'];hf=h['faces'];z=1.515;sec=[]
    for tri in hv[hf]:
        pts=[]
        for a,b in zip(tri,np.roll(tri,-1,axis=0)):
            if (a[2]<z)!=(b[2]<z):pts.append(a+(z-a[2])/(b[2]-a[2])*(b-a))
        if len(pts)==2:sec.extend(pts)
    sec=np.unique(np.round(sec,6),axis=0);center=np.median(sec[:,:2],axis=0);sec=sec[np.argsort(np.arctan2(sec[:,1]-center[1],sec[:,0]-center[0]))];rad=sec[:,:2]-center;inner=sec.copy();inner[:,:2]+=rad/np.maximum(np.linalg.norm(rad,axis=1)[:,None],1e-12)*.005;report['neckMeasurementZ']=z;report['nominalNeckClothClearance']=.005
    allv=v.copy();allf=[f];alluv=[uv];allmi=[mi];allorigin=[origin]
    for n,l in enumerate(ls):
        label='neck-lining-annulus' if n==0 else 'posterior-cloth-cap'+str(n);pv,pf,pl=volume_patch(label,v[l],inner if n==0 else None)
        if n==0:pl.sort(key=lambda a:np.linalg.norm(pv[a,:2]-center,axis=1).mean(),reverse=True)
        newv,newf,sr=sew(allv,l,pv,pf,pl[0]);report['patches'][-1]['seam']=sr
        # Lining has authored dark cloth; caps inherit nearest local source garment UV.
        uvs=np.zeros((uv.shape[0],len(newf),3,2),np.float32)
        if n>0:
            local=np.linalg.norm(v[f].mean(1)-v[l].mean(0),axis=1)<.06;localidx=np.where(local)[0];qq=newv[newf];_,ix=cKDTree(v[f[localidx]].mean(1)).query(qq.reshape(-1,3),workers=2);sfi=localidx[ix];tri=v[f[sfi]];pt=qq.reshape(-1,3);ab=tri[:,1]-tri[:,0];ac=tri[:,2]-tri[:,0];ap=pt-tri[:,0];d00=(ab*ab).sum(1);d01=(ab*ac).sum(1);d11=(ac*ac).sum(1);d20=(ap*ab).sum(1);d21=(ap*ac).sum(1);den=d00*d11-d01*d01;bv=(d11*d20-d01*d21)/np.maximum(den,1e-20);bw=(d00*d21-d01*d20)/np.maximum(den,1e-20);bary=np.clip(np.column_stack((1-bv-bw,bv,bw)),0,1);bary/=bary.sum(1)[:,None]
            for k in range(uv.shape[0]):uvs[k]=np.einsum('nc,ncd->nd',bary,uv[k,sfi]).reshape(-1,3,2)
        else:uvs[:]=(newv[newf,:,:2]-center)[None]*5+.5
        allv=newv;allf.append(newf);alluv.append(uvs);allmi.append(np.full(len(newf),2 if n==0 else 0));allorigin.append(np.full(len(newf),-3-n))
    finalf=np.vstack(allf);fl,fa=loops(finalf);report['finalBodyTopology']=fa;report['finalBodyLoopLengths']=[len(x) for x in fl]
    if len(fl)!=1 or fa['nonmanifoldEdges']:raise ValueError('Complete garment must have only genuine neck opening boundary')
    norms=np.cross(allv[finalf[:,1]]-allv[finalf[:,0]],allv[finalf[:,2]]-allv[finalf[:,0]]);report['zeroAreaTriangles']=int(np.sum(np.linalg.norm(norms,axis=1)<1e-12))
    np.savez(RUN/'reconstructed-body.npz',vertices=allv,faces=finalf,allTriangleUV=np.concatenate(alluv,axis=1),materialIndex=np.concatenate(allmi),faceOrigin=np.concatenate(allorigin),originalVertexCount=d['originalVertexCount']);report['status']='UNACCEPTED actual three-volume geometry constructed; requires parent actual views'
except Exception as e:report['status']='FAILED trial03 geometry gate';report['error']=str(e);report['traceback']=traceback.format_exc()
finally:
    report['elapsedSeconds']=time.monotonic()-t;report['peakRSSBytes']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss;report['recipeSHA256']=sha(__file__);(RUN/'volume-report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
