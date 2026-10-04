"""Analytic ownership rays at already-played pixels; no new image/capture."""
import gzip,hashlib,json
from pathlib import Path
import numpy as np
from PIL import Image
out=Path(__file__).resolve().parent;qa=out.parent;n=np.load(qa/'body52/native-fields.npz');e=np.load(qa/'body52/export-fields.npz');witness=np.load(out/'neck-witnesses.npz');sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();names=n['boneNames'].tolist();normal=lambda x:x.replace('.','').replace('_','');order=[list(map(normal,names)).index(normal(x)) for x in e['jointNames']];C=np.array([[1.,0,0,0],[0,0,1,0],[0,-1,0,0],[0,0,0,1]]);base=Path('docs/evidence/hero-remaster/anatomical-foundation-2026-10-03/user-agent1/diagnostic02');driver=json.loads((base/'driver.json').read_text());stream=np.memmap(base/'body-native-four.f64',dtype='<f8',mode='r',shape=(529,13380,3))
with gzip.open(qa/'garment47/first.weights.ndjson.gz','rt') as f:actual=[json.loads(line) for line in f]
rest={};weights={}
for key in ['renderedBody','protectedHead','cheek']:
 p=n[key+'XYZ'];rest[key]=np.column_stack([p,np.ones(len(p))])@(C@n[key+'World']).T;w=n[key+'Weights'][:,order].copy();w/=w.sum(1)[:,None];weights[key]=w
source_ids=n['renderedBodySourceIDs'].astype(int)
def skin(key,K):return np.einsum('vj,jab,vb->va',weights[key],K,rest[key],optimize=True)[:,:3]
def ray(origin,direction,triangles):
 a=triangles[:,0];ab=triangles[:,1]-a;ac=triangles[:,2]-a;p=np.cross(direction,ac);det=np.einsum('ij,ij->i',ab,p);valid=np.abs(det)>1e-12;inv=np.divide(1,det,out=np.zeros_like(det),where=valid);s=origin-a;u=np.einsum('ij,ij->i',s,p)*inv;q=np.cross(s,ab);v=q@direction*inv;t=np.einsum('ij,ij->i',ac,q)*inv;valid&=(u>=-1e-9)&(v>=-1e-9)&(u+v<=1+1e-9)&(t>0)
 if not valid.any():return None
 i=int(np.argmin(np.where(valid,t,np.inf)));return i,float(t[i]),np.array([1-u[i]-v[i],u[i],v[i]])
results=[];pins={};domains=[('native',72,'native_shoulder.png',[(240,270,405,295),(904,273,1010,289),(1483,275,1635,297)]),('actual47',668,'actual_shoulder.png',[(235,265,410,310),(934,287,1016,320),(1490,282,1640,311)])]
for domain,index,file,boxes in domains:
 with gzip.open(qa/'body56'/(domain+'-render.json.gz'),'rt') as f:r=json.load(f)
 row=next(x for x in r['frames'] if x['sourceIndex']==index and x['kind']=='paused exact witness');prep=json.loads((qa/'body56'/(domain+'-preparation.json')).read_text());cm=np.array(prep['settings']['cameraWorldRows']);width=prep['settings']['orthoWidthM'];height=width*1280/1920
 if domain=='native':W=np.array([np.array(driver['frames'][index]['jointWorldColumnMajor'][names[j]]).reshape(4,4).T for j in order]);K=W@e['inverseBinds'];body=stream[index][source_ids]
 else:K=np.array(actual[index-1]['matrices']).reshape(51,4,4).transpose(0,2,1);body=skin('renderedBody',K)
 fields={'renderedBody':body,'protectedHead':skin('protectedHead',K),'cheek':skin('cheek',K)};keys=list(fields);triangle_points=np.concatenate([fields[k][n[k+'Triangles']] for k in keys]);ends=np.cumsum([len(n[k+'Triangles']) for k in keys]);starts=np.r_[0,ends[:-1]];image_path=qa/'body56/played'/file;pixels=np.array(Image.open(image_path).convert('RGB'));pins[str(image_path)]=sha(image_path);pins[str(qa/'body56'/(domain+'-render.json.gz'))]=sha(qa/'body56'/(domain+'-render.json.gz'))
 for col,box in enumerate(boxes):
  view=next(v for v in row['views'] if v['weight']=='four' and v['column']==col);transform=np.array(view['displayFromSourceRotationRows']);translation=np.array(view['displayTranslationM']);x0,y0,w,h=view['focusCrops']['shoulders']['pixelXYWH'];dw,dh=600,446;tile_x=col*640+20;tile_y=88
  def source_ray(px,py):
   rawx=x0+(px-tile_x+.5)*w/dw;rawy=y0+(py-tile_y+.5)*h/dh;origin=cm[:3,3]+((rawx/1920)-.5)*width*cm[:3,0]+(.5-rawy/1280)*height*cm[:3,1];return transform.T@(origin-translation),transform.T@(-cm[:3,2])
  # Read darkest existing pixel in each fixed box subcell, including misses.
  left,top,right,bottom=box
  for iy in range(2):
   for ix in range(6):
    xa=left+(right-left)*ix//6;xb=left+(right-left)*(ix+1)//6;ya=top+(bottom-top)*iy//2;yb=top+(bottom-top)*(iy+1)//2;rgb=pixels[ya:yb,xa:xb];j,i=np.unravel_index(np.argmin(rgb.astype(float).mean(2)),rgb.shape[:2]);px,py=xa+i,ya+j;origin,direction=source_ray(px,py);hit=ray(origin,direction,triangle_points);entry={'domain':domain,'sourceIndex':index,'view':['front','left side','rear'][col],'playedImage':str(image_path),'playedPixelXY':[int(px),int(py)],'RGB':pixels[py,px].tolist(),'fixedSearchBoxXYXY':list(box),'hit':None}
    if hit:
     tri,depth,bary=hit;part=int(np.searchsorted(ends,tri,side='right'));key=keys[part];local=tri-int(starts[part]);ids=n[key+'Triangles'][local];rest_point=bary@n[key+'XYZ'][ids];neighbour=[]
     for ox,oy in [(-.2,0),(.2,0),(0,-.2),(0,.2)]:
      other=ray(*source_ray(px+ox,py+oy),triangle_points);neighbour.append(None if other is None else keys[int(np.searchsorted(ends,other[0],side='right'))])
     entry['hit']={'part':key,'nativeTriangle':int(local),'nativeVertexIDs':ids.tolist(),'barycentric':bary.tolist(),'restNativeXYZM':rest_point.tolist(),'rayDistanceM':depth,'stablePartWithinPoint2Pixel':all(v==key for v in neighbour),'neighbourParts':neighbour}
     if key=='protectedHead':entry['hit'].update({'originalDonorTriangle':int(witness['headOriginalDonorTriangleIDs'][local]),'originalDonorVertices':witness['headOriginalDonorVertexIDs'][ids].tolist(),'withinLowHeadProxy1_60M':bool(n[key+'XYZ'][ids,2].max()<=1.60)})
     elif key=='renderedBody':entry['hit']['fullBodySourceVertexIDs']=source_ids[ids].tolist()
    results.append(entry)
 report={'status':'READ_ONLY_EXISTING_PLAYED_PIXEL_ANALYTIC_OWNERSHIP','domain':domain,'rows':len(results)};print(json.dumps(report),flush=True)
report={'status':'UNACCEPTED_EXISTING_COLLAR_PIXELS_ANALYTIC_SURFACE_OWNERSHIP','recipeSHA256':sha(__file__),'pins':pins,'rows':results,'method':'Use existing held FOUR shoulder crops and recorded orthographic camera/source transforms. Fixed boxes split2x6; darkest existingRGBpixel read in each cell, retaining misses. Trace nearest two-sided geometric ray with +/-0.2pixel ownership checks. No new raster/image edit/capture.','limits':['Geometry rays have no alpha/culling/texture/shader visibility model. Boundary pixels can blend/alias; stable interior ownership supports attribution only at listed pixels.','No universal flange segmentation or penetration/repair sufficiency claim. Existing source fields,weights and camera retained; root alone judges appearance.']};(out/'pixel-ownership.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'stableDarkLowHeadHits':sum(x['hit'] is not None and x['hit']['part']=='protectedHead' and x['hit']['stablePartWithinPoint2Pixel'] and x['hit'].get('withinLowHeadProxy1_60M') and max(x['RGB'])<100 for x in results),'byPart':{k:sum(x['hit'] is not None and x['hit']['part']==k for x in results) for k in keys},'misses':sum(x['hit'] is None for x in results)},indent=2))
