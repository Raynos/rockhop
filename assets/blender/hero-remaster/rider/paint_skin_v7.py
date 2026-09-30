"""Blender image paint: geometry-selected skin texels, unrelated UV aliases vetoed.

Produces only a material image and measurements. No mesh is imported or edited.
"""
import bpy,sys,argparse,json,math
from pathlib import Path
import numpy as np
ap=argparse.ArgumentParser();ap.add_argument('--geometry',required=True);ap.add_argument('--image',required=True);ap.add_argument('--out',required=True);a=ap.parse_args(sys.argv[sys.argv.index('--')+1:])
g=json.loads(Path(a.geometry).read_text());img=bpy.data.images.load(str(Path(a.image).resolve()),check_existing=False);img.colorspace_settings.name='Non-Color';w,h=img.size
pixels=np.empty(w*h*4,np.float32);img.pixels.foreach_get(pixels);pixels=pixels.reshape(h,w,4);original=pixels.copy()
positions=np.asarray(g['positions']);uv=np.asarray(g['uv']);tri=np.asarray(g['triangles']);forearm=np.asarray(g['forearmWeight']);head=np.asarray(g['headDominant'])
def sample(points):
 xy=np.asarray(points);xx=np.clip((xy[:,0]*w).astype(int),0,w-1);yy=np.clip((xy[:,1]*h).astype(int),0,h-1);return original[yy,xx,:3]
def skin_colour(c):
 maximum=np.max(c,axis=-1);minimum=np.min(c,axis=-1);sat=(maximum-minimum)/np.maximum(maximum,.001)
 return (maximum>.32)&(sat<.38)&(c[...,0]>=c[...,1]-.035)&(c[...,0]>=c[...,2]-.015)
# The palette is authored from observed source face/albedo and Concept A's
# forearm. It is an albedo choice, not a copied lighting/shadow gradient.
reference=bpy.data.images.load(str(Path('assets/blender/hero-remaster/rider/refs/street-apose.png').resolve()),check_existing=False);reference.colorspace_settings.name='Non-Color';rw,rh=reference.size;rp=np.empty(rw*rh*4,np.float32);reference.pixels.foreach_get(rp);rp=rp.reshape(rh,rw,4)
ref_samples=[]
for x0,y0,x1,y1 in [(151,570,198,605),(825,570,874,606)]:
 patch=rp[rh-y1:rh-y0,x0:x1,:3].reshape(-1,3);ref_samples.extend(patch[skin_colour(patch)].tolist())
referenceTone=np.median(np.asarray(ref_samples),axis=0)
headSamples=sample(uv[head]);headSamples=headSamples[skin_colour(headSamples)];sourceHeadTone=np.median(headSamples,axis=0)
# Remove photographic directional shading from the finish: a bounded clean
# neutral warm albedo, biased toward the existing head so wrists share its hue.
target=np.clip(sourceHeadTone*.65+referenceTone*.35,[.60,.43,.32],[.80,.65,.55])
# Geometric bounds cover exposed forearms and the sleeve transition; a per-
# texel skin classifier protects the mustard fabric within those UV triangles.
centres=positions[tri].mean(axis=1);weights=forearm[tri].mean(axis=1)
candidate=(weights>.65)&(centres[:,0]>.83)&(centres[:,1]>.86)&(centres[:,1]<1.11)&(np.abs(centres[:,2])>.27)
selected=np.zeros((h,w),bool);unrelated=np.zeros((h,w),bool)
def raster(ids,dest):
 for ids0 in ids:
  p=uv[ids0]*[w,h];lo=np.maximum(np.floor(p.min(axis=0)-1).astype(int),0);hi=np.minimum(np.ceil(p.max(axis=0)+1).astype(int),[w-1,h-1]);xs=np.arange(lo[0],hi[0]+1)+.5;ys=np.arange(lo[1],hi[1]+1)+.5
  if not len(xs) or not len(ys):continue
  x,y=np.meshgrid(xs,ys);v0=p[1]-p[0];v1=p[2]-p[0];det=v0[0]*v1[1]-v0[1]*v1[0]
  if abs(det)<1e-10:continue
  dx=x-p[0,0];dy=y-p[0,1];s=(dx*v1[1]-dy*v1[0])/det;t=(v0[0]*dy-v0[1]*dx)/det;inside=(s>=-1e-7)&(t>=-1e-7)&(s+t<=1+1e-7)
  dest[lo[1]:hi[1]+1,lo[0]:hi[0]+1]|=inside
raster(tri[candidate],selected);raster(tri[~candidate],unrelated)
# Two-texel padding covers bilinear filtering at a skin island boundary, while
# a matching unrelated-face pad vetoes every alias and its filtering footprint.
def expand(mask,steps):
 result=mask.copy()
 for _ in range(steps):
  old=result.copy()
  for dy,dx in [(-1,0),(1,0),(0,-1),(0,1)]:
   shifted=np.roll(old,(dy,dx),(0,1));
   if dy==-1:shifted[-1]=False
   if dy==1:shifted[0]=False
   if dx==-1:shifted[:,-1]=False
   if dx==1:shifted[:,0]=False
   result|=shifted
 return result
candidateMask=expand(selected,2);veto=expand(unrelated,2);colourSkin=skin_colour(original[:,:,:3]);paint=candidateMask&colourSkin&~veto
assert np.count_nonzero(paint)>100,'meaningful exposed forearm paint area'
# Skin colour is constant authored albedo; geometry and runtime lighting retain
# their shading. No painted hard shadows or geometry-scale colour mottling.
pixels[paint,:3]=target
out=bpy.data.images.new('Street clean forearm skin albedo V7',width=w,height=h,alpha=True,is_data=True);out.colorspace_settings.name='Non-Color';out.pixels.foreach_set(pixels.ravel());out.filepath_raw=str(Path(a.out).resolve());out.file_format='PNG';out.save()
# Re-open the lossless image and prove unrelated decoded pixels are identical.
check=bpy.data.images.load(str(Path(a.out).resolve()),check_existing=False);check.colorspace_settings.name='Non-Color';cp=np.empty(w*h*4,np.float32);check.pixels.foreach_get(cp);cp=cp.reshape(h,w,4)
before=np.round(original*255).astype(np.uint8);after=np.round(cp*255).astype(np.uint8);changed=np.any(before!=after,axis=2)
assert not np.any(changed&~paint),'unrelated decoded pixel changed'
report={'dimensions':[w,h],'candidateForearmTriangles':int(np.count_nonzero(candidate)),'candidateUVTexels':int(np.count_nonzero(selected)),'paintedTexels':int(np.count_nonzero(paint)),'changedTexels':int(np.count_nonzero(changed)),'unrelatedUVTexels':int(np.count_nonzero(unrelated)),'aliasedCandidateTexelsVetoed':int(np.count_nonzero(candidateMask&veto&colourSkin)),'unrelatedChangedTexels':int(np.count_nonzero(changed&unrelated)),'outsidePaintChangedTexels':int(np.count_nonzero(changed&~paint)),'targetSRGB':target.tolist(),'sourceHeadMedianSRGB':sourceHeadTone.tolist(),'referenceForearmMedianSRGB':referenceTone.tolist(),'targetLinear':[float(c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4) for c in target],'skinRoughness':.72,'method':'Blender lossless forearm-UV albedo paint selected through skinned geometry bounds, exact non-forearm triangle UV raster alias veto, two-texel filtering protection; retained original pixels everywhere else.'}
Path(a.out+'.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
