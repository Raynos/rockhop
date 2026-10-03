from pathlib import Path
import sys,json,hashlib
import numpy as np
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE.parent));from chart_labels import SourceCharts,unit,smooth
c=SourceCharts();src=HERE/'source-sleeve-tube-rest04-normal.npz';f=dict(np.load(src));cut=np.load(HERE.parent/'armhole-construction/source-armhole-cut.npz');allq=c.unique[c.ct];report=[]
for side in ['L','R']:
 mask=cut['sleeveFaces'+side];faceIDs=np.flatnonzero(mask);q=allq[mask];e1=q[:,1]-q[:,0];e2=q[:,2]-q[:,0];normal=np.cross(e1,e2);rows=f['tubeRows'+side];controls=f['curveControlRest'+side];matched=[];ancestry=[];hitdist=[]
 for ri,ids in enumerate(rows[1:-1],1):
  s=ri/(len(rows)-1);cc=(1-s)**3*controls[0]+3*(1-s)**2*s*controls[1]+3*(1-s)*s*s*controls[2]+s**3*controls[3];radial=f['p0'][ids]-cc;directions=unit(radial);radnorm=np.linalg.norm(radial,axis=1);out=f['p0'][ids].copy();donor=np.full(len(ids),-1,int);hd=np.full(len(ids),np.nan)
  for j,d in enumerate(directions):
   h=np.cross(np.broadcast_to(d,e2.shape),e2);det=np.einsum('ij,ij->i',e1,h);valid=abs(det)>1e-12;inv=np.zeros(len(q));inv[valid]=1/det[valid];v=cc-q[:,0];u=inv*np.einsum('ij,ij->i',v,h);qq=np.cross(v,e1);vv=inv*np.einsum('j,ij->i',d,qq);t=inv*np.einsum('ij,ij->i',e2,qq);outward=np.einsum('ij,j->i',normal,d)>0;ok=valid&(u>=-1e-8)&(vv>=-1e-8)&(u+vv<=1+1e-8)&(t>.005)&(t<.18)&outward
   if not ok.any():continue
   candidates=np.flatnonzero(ok);k=candidates[np.argmin(abs(t[candidates]-radnorm[j]))];delta=np.clip(t[k]-radnorm[j],-.025,.025);factor=np.sin(np.pi*s)**.5;out[j]+=d*delta*factor;donor[j]=faceIDs[k];hd[j]=t[k]
  f['p0'][ids]=out;matched.extend(donor>=0);ancestry.append(donor);hitdist.append(hd)
 f['tubeRaySourceFace'+side]=np.array(ancestry);f['tubeRayHitRadius'+side]=np.array(hitdist);f['tubeRestRows'+side]=f['p0'][rows].copy();report.append({'side':side,'rayRows':len(matched),'validSourceOutwardHits':int(np.sum(matched)),'boundedMaxDisplacementM':float(np.linalg.norm(f['p0'][rows]-np.load(src)['p0'][rows],axis=2).max()),'protectedEndpointPositionExact':bool(np.array_equal(f['p0'][rows[[0,-1]]],np.load(src)['p0'][rows[[0,-1]]]))})
# Recompute only interior tube normals; hold all boundary/source seam normals04.
for side in ['L','R']:
 rows=f['tubeRows'+side];tt=f['tr0'][f['newTubeFaceIDs'+side]];p=f['p0'];n=np.zeros_like(p);q=p[tt];fn=np.cross(q[:,1]-q[:,0],q[:,2]-q[:,0]);
 for j in range(3):np.add.at(n,tt[:,j],fn)
 interior=rows[1:-1].ravel();geom=unit(n[interior]);old=np.load(src)['n0'][interior];r=np.repeat(np.linspace(0,1,len(rows))[1:-1],rows.shape[1]);blend=np.minimum(1,np.minimum(r,1-r)*6);f['n0'][interior]=unit((1-blend[:,None])*old+blend[:,None]*geom)
for pi in range(5):
 q=f[f'p{pi}'][f[f'tr{pi}']];f[f'restDoubleArea{pi}']=np.linalg.norm(np.cross(q[:,1]-q[:,0],q[:,2]-q[:,0]),axis=1)
out=HERE/'source-sleeve-tube-rest05-envelope.npz';np.savez_compressed(out,**f);(HERE/'source-sleeve-tube-rest05-envelope-provenance.json').write_text(json.dumps({'status':'UNACCEPTED STANDING SOURCE-ENVELOPE CLONE; literal rest/render pending','parentSHA256':hashlib.sha256(src.read_bytes()).hexdigest(),'candidateSHA256':hashlib.sha256(out.read_bytes()).hexdigest(),'method':'For every interior tube row ray, nearest outward intersection on original mincut-selected sleeve triangles supplies actual radial source envelope/fold. Radial displacement clamped25mm with endpointzero taper. Endpoint positions/sourceprefix/caps/head/gloves/UV/denseW untouched. Per-row sourceface ancestry and hit radius stored. New interior tube normal only follows actual new triangles; seam normals retained04.','rows':report,'sourcePrefixExact':all(np.array_equal(f[f'p{i}'][:len(c.pos[i])],c.pos[i])for i in range(5)),'runtimeFiveInfluencesUnchanged':True},indent=2));print(json.dumps(report,indent=2));print(hashlib.sha256(out.read_bytes()).hexdigest())
