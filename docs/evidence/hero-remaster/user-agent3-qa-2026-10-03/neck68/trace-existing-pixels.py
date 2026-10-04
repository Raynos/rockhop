"""Trace already-played pixels using frozen camera/actual triangles; no raster."""
import hashlib,json
from pathlib import Path
import numpy as np
from PIL import Image
out=Path(__file__).resolve().parent;qa=out.parent;root=out.parents[4];ev=root/'docs/evidence/hero-remaster/anatomical-foundation-2026-10-03/user-agent1';played=ev/'neck-interface99/played';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();prep=json.loads((qa/'neck67/preparation.json').read_text());s=json.loads((out/'source-assessment.json').read_text())
for p,h in prep['pins'].items():assert sha(root/p)==h['sha256'],p
n=dict(np.load(qa/'body52/native-fields.npz'));f=dict(np.load(root/'assets/blender/hero-remaster/rider/anatomical-foundation-2026-10-03/user-agent1/neck-interface27/triangulated-neck-fields.npz'));pose=np.load(ev/'neck-interface99/pose-witnesses.npz');render=json.loads((played/'render.json').read_text());cam=np.array(render['settings']['cameraWorldRows']);rotation=cam[:3,:3];origin=cam[:3,3];width=render['settings']['orthographicWidthM'];height=width*1280/1920;free_head=set(s['actualEditableHeadIDsAfterAliasProtection']);fixed_head=set(s['fixedHeadIDs']);free_body=set(json.loads((qa/'body59/proposal.json').read_text())['preciseInitialAuthoringMargin']['bodyExistingRenderedNativeVertices']);original_head_count=len(n['protectedHeadXYZ']);original_body_count=len(n['renderedBodyXYZ']);H=n['protectedHeadXYZ'];target_ids={29738,16669}
for axis in range(3):
 ids=np.array(sorted(fixed_head));target_ids.add(int(ids[np.argmin(H[ids,axis])]));target_ids.add(int(ids[np.argmax(H[ids,axis])]))
rows=[];views_summary=[]
def manual(part,S):
 p=np.column_stack([n[part+'XYZ'],np.ones(len(n[part+'XYZ']))]);w=n[part+'Weights'].astype(float);w/=w.sum(1)[:,None];result=np.einsum('vj,jab,vb->va',w,S,p,optimize=True);return (result@n[part+'World'].T)[:,:3]
def project(p):return np.column_stack([(.5+p[:,0]/width)*1920,(.5-p[:,1]/height)*1280])
for domain,index,encoded in [('native',72,'0329.png'),('actual47',668,'0611.png')]:
 frame=next(x for x in render['frames'] if x['domain']==domain and x['sourceIndex']==index);archive_row=frame['archiveRow'];S=pose['rigLocalSkinMatrices'][archive_row].astype(float);assert pose['boneNames'].tolist()==n['boneNames'].tolist()==f['boneNames'].tolist();points={'body':pose[domain+str(index)+'bodyfourActualWorld'].astype(float),'head':pose[domain+str(index)+'headfourActualWorld'].astype(float),'cheek':manual('cheek',S),'boxers':manual('boxers',S)};tris={'body':f['bodyTriangles'],'head':f['headTriangles'],'cheek':n['cheekTriangles'],'boxers':n['boxersTriangles']};im=Image.open(played/'encoded-frames'/encoded).convert('RGB');rgb=np.asarray(im);assert im.size==(1920,1440)
 for view in [x for x in frame['views'] if x['label']=='candidate']:
  col=view['column'];transform=np.array(view['displayFromSourceRows']);crop=np.array(view['neckContextCropXYWH']);base=np.array([col*640+20,760]);scale=np.array([600/crop[2],560/crop[3]]);projected={};camera_tri={};boxes={}
  for part,p in points.items():
   display=p@transform[:3,:3].T+transform[:3,3];camera=(display-origin)@rotation;projected[part]=project(camera);q=camera[tris[part]];camera_tri[part]=q;boxes[part]=(q[:,:,:2].min(1),q[:,:,:2].max(1))
  def encoded_point(raw):return base+(raw-crop[:2])*scale
  def ray(xy):
   raw=crop[:2]+(np.array(xy)+.5-base)/scale;pos=np.array([(raw[0]/1920-.5)*width,(.5-raw[1]/1280)*height]);best=None
   for part,q in camera_tri.items():
    mn,mx=boxes[part];ids=np.flatnonzero(np.all(pos>=mn-1e-10,axis=1)&np.all(pos<=mx+1e-10,axis=1))
    if not len(ids):continue
    a=q[ids,0];u=q[ids,1]-a;v=q[ids,2]-a;d=pos-a[:,:2];den=u[:,0]*v[:,1]-u[:,1]*v[:,0];ok=np.abs(den)>1e-14;bb=np.zeros(len(ids));cc=np.zeros(len(ids));bb[ok]=(d[ok,0]*v[ok,1]-d[ok,1]*v[ok,0])/den[ok];cc[ok]=(u[ok,0]*d[ok,1]-u[ok,1]*d[ok,0])/den[ok];aa=1-bb-cc;ok&=(aa>=-1e-8)&(bb>=-1e-8)&(cc>=-1e-8);depth=aa*a[:,2]+bb*q[ids,1,2]+cc*q[ids,2,2];ok&=depth<0
    if not ok.any():continue
    j=int(np.argmax(np.where(ok,depth,-np.inf)));hit={'part':part,'candidateTriangle':int(ids[j]),'barycentric':[float(aa[j]),float(bb[j]),float(cc[j])],'cameraDepthM':float(depth[j])}
    if best is None or hit['cameraDepthM']>best['cameraDepthM']:best=hit
   if best:
    part=best['part'];ti=best['candidateTriangle'];vertices=tris[part][ti];best['candidateVertexIDs']=vertices.tolist()
    if part in ['body','head']:
     free=free_head if part=='head' else free_body;orig=original_head_count if part=='head' else original_body_count;editable=np.array([(int(v) in free or int(v)>=orig) for v in vertices]);fixed=~editable;best['geometryScope']='fully_fixed' if fixed.all() else 'mixed_fixed_editable' if fixed.any() else 'fully_editable';best['fixedOriginalVertexIDs']=[int(v) for v in vertices[fixed]];best['fixedBarycentricMass']=float(np.array(best['barycentric'])[fixed].sum());best['originalSourcePolygonID']=int(f[part+'TriangleSourcePolygonIDs'][ti]);best['sourceRestNativePositionM']=(np.array(best['barycentric'])@f[part+'RestXYZ'][vertices]).tolist();best['withinLowHeadInspectionProxy1_60M']=part=='head' and best['sourceRestNativePositionM'][2]<=1.60;best['touchesFixedHeadOneCornerWitnesses']=part=='head' and bool(set(map(int,vertices))&fixed_head)
    else:best['geometryScope']='protected_other_part'
   return raw,best
  tests=[]
  for v in sorted(target_ids):
   continuous=encoded_point(projected['head'][v]);pixel=np.round(continuous-.5).astype(int)
   offsets=[(dx,dy) for dx in [-1,0,1] for dy in [-1,0,1]] if v==29738 else [(0,0)]
   for dx,dy in offsets:tests.append({'selection':'fixed_vertex_projection','targetNativeHeadVertex':v,'projectedEncodedEdgeXY':continuous.tolist(),'playedPixelXY':(pixel+np.array([dx,dy])).tolist()})
  # Fixed 3x6 skin-colour-minimum subcells over the projected original lower neck and body patch.
  local_ids=np.flatnonzero(n['protectedHeadXYZ'][:,2]<=1.56);hxy=encoded_point(projected['head'][local_ids]);bxy=encoded_point(projected['body'][np.array(sorted(free_body))]);roi=np.vstack([hxy,bxy]);lo=np.floor(roi.min(0)-1).astype(int);hi=np.ceil(roi.max(0)+2).astype(int);lo=np.maximum(lo,base);hi=np.minimum(hi,base+[600,560]);edgesx=np.linspace(lo[0],hi[0],7).astype(int);edgesy=np.linspace(lo[1],hi[1],4).astype(int)
  for yy in range(3):
   for xx in range(6):
    x0,x1=edgesx[xx:xx+2];y0,y1=edgesy[yy:yy+2]
    if x1<=x0 or y1<=y0:continue
    patch=rgb[y0:y1,x0:x1].astype(int);skin=(patch[:,:,0]>patch[:,:,1]+2)&(patch[:,:,1]>patch[:,:,2]+1)&(patch[:,:,0]>15);lum=patch.mean(2);score=np.where(skin,lum,np.inf) if skin.any() else lum;iy,ix=np.unravel_index(np.argmin(score),score.shape);tests.append({'selection':'neck_roi3x6_low_skin_rgb_cell','cellXY':[xx,yy],'cellBoxXYXY':[int(x0),int(y0),int(x1),int(y1)],'skinRGBEligiblePixels':int(skin.sum()),'playedPixelXY':[int(x0+ix),int(y0+iy)]})
  for test in tests:
   x,y=map(int,test['playedPixelXY'])
   if not (base[0]<=x<base[0]+600 and base[1]<=y<base[1]+560):test['outsideFocusTile']=True;hit=None;raw=None
   else:
    raw,hit=ray([x,y]);neighbours=[ray([x+dx,y+dy])[1] for dx,dy in [(-.2,0),(.2,0),(0,-.2),(0,.2)]]
    if hit:
     hit['partStableWithinPoint2Pixel']=all(h is not None and h['part']==hit['part'] for h in neighbours);hit['scopeStableWithinPoint2Pixel']=all(h is not None and h['part']==hit['part'] and h['geometryScope']==hit['geometryScope'] for h in neighbours);hit['neighbourScopeClasses']=[None if h is None else [h['part'],h['geometryScope']] for h in neighbours]
   rows.append({'domain':domain,'sourceIndex':index,'view':['front','left side','rear'][col],'encodedPNG':encoded,**test,'RGB':None if not (0<=x<1920 and 0<=y<1440) else rgb[y,x].tolist(),'rawCaptureEdgeXY':None if raw is None else raw.tolist(),'hit':hit})
  views_summary.append({'domain':domain,'sourceIndex':index,'view':['front','left side','rear'][col],'neckROIEncodedXYXY':[lo.tolist(),hi.tolist()],'tests':len(tests)})
report={'status':'UNACCEPTED_EXISTING_PLAYED_PIXEL_GEOMETRIC_OWNERSHIP','recipeSHA256':sha(__file__),'sourceAssessmentSHA256':sha(out/'source-assessment.json'),'all21InputPinsUnchanged':True,'views':views_summary,'rows':rows,'limits':['No new image, crop, raster, renderer, capture, pose/controller or source edit. Existing encoded PNG pixels read directly. Raw/crop camera projection and original actual frozen world triangles used.','Nearest two-sided geometry only; no alpha/shader/photon/shadow visibility model. Skin-RGB cell selection is explicit, all tests/misses retained. This is sampled attribution, not complete ledge segmentation or moving cause proof.','Protected cheek and boxers use existing manual normalized skin fields; head/body use archived actual Float32 vertices. Frozen99render-field maximum1.65µm remains reported, actual47source identity failure not waived.','Fully-fixed scope means stored positions and semantic fields are protected under exact lists plus partial alias pinning. It does not promise unchanged pixel lighting/occlusion after a legitimate future local construction, nor prove whole-transition infeasibility.']}
for p,h in prep['pins'].items():assert sha(root/p)==h['sha256'],p
(out/'pixel-ownership.json').write_text(json.dumps(report,indent=2)+'\n');hits=[x for x in rows if x['hit']];fixed=[x for x in hits if x['hit']['part']=='head' and x['hit']['geometryScope']=='fully_fixed' and x['hit']['scopeStableWithinPoint2Pixel']];print(json.dumps({'rows':len(rows),'hits':len(hits),'stableFullyFixedHeadHits':len(fixed),'stableFixedDarkRGBUnder100':len([x for x in fixed if max(x['RGB'])<100]),'vertex29738ProjectionHits':[{'domain':x['domain'],'view':x['view'],'pixel':x['playedPixelXY'],'part':None if x['hit'] is None else x['hit']['part'],'scope':None if x['hit'] is None else x['hit']['geometryScope'],'tri':None if x['hit'] is None else x['hit']['candidateTriangle']} for x in rows if x.get('targetNativeHeadVertex')==29738 and x['playedPixelXY']==np.round(np.array(x['projectedEncodedEdgeXY'])-.5).astype(int).tolist()]},indent=2))
