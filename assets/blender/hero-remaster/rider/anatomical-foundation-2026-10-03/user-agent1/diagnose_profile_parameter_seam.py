"""Audit side-switch discontinuities in barycentric construction parameters.

Read frozen source19 fields and unchanged branch/profile recipes. Compare
barycentric seam parameters at source midline edges with the original smooth
source-space definition; no native edit, refinement retry or new fit.
"""
import argparse, gzip, hashlib, json, sys
from pathlib import Path
import bpy, numpy as np
ap=argparse.ArgumentParser(description=__doc__)
for k in ['source','field','profiles','recipe','anchors','out']:ap.add_argument('--'+k,required=True)
a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);source,field,profiles,recipe,anchors,out=[Path(getattr(a,k)).resolve() for k in ['source','field','profiles','recipe','anchors','out']]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();pins={str(p):sha(p) for p in [source,field,profiles,recipe,anchors]};f=np.load(field);src=f['sourceDisplayXYZ'];p=f['previousNativeXYZ'];tri=f['previousTriangles'];profileRows=json.loads(gzip.decompress(profiles.read_bytes()))
bpy.ops.wm.open_mainfile(filepath=str(source));rig=bpy.data.objects['Independent anatomical foundation rig'];branches={};definition=recipe.read_text();definition=definition[definition.index("for part in sorted({r['part'] for r in profileRows}):"):definition.index('rows=[]')];exec(compile(definition,str(recipe),'exec'))
anchorData=json.loads(anchors.read_text());sourceAnchors={side:np.array(anchorData['fits'][side]['sourceShoulderElbowWristXYZ']) for side in ['R','L']}
def parameters(s):
    side='R' if s[0]>=0 else 'L';v=sourceAnchors[side];axes=np.diff(v,axis=0);axes/=np.linalg.norm(axes,axis=1)[:,None];common=axes.sum(0);common/=np.linalg.norm(common);t=float(np.clip((s-v[1])@common/.12+.5,0,1));w=t*t*(3-2*t);d=(abs(s[0])-.36)-max(.46-s[2],0)*.22;a=float(np.clip(d/.15,0,1));a=a*a*(3-2*a);return a,w
actual=np.array([parameters(s) for s in src]);alphaError=np.abs(actual[:,0]-f['armSeamWeight']);foreError=np.abs(actual[:,1]-f['forearmBlendWeight']);assert alphaError.max()<1e-12 and foreError.max()<1e-12
edges={tuple(sorted((int(ids[i]),int(ids[(i+1)%3])))) for ids in tri for i in range(3)};rows=[]
for i,j in sorted(edges):
    if src[i,0]*src[j,0]>=0:continue
    t=float(-src[i,0]/(src[j,0]-src[i,0]));s=src[i]*(1-t)+src[j]*t;v=p[i]*(1-t)+p[j]*t;a=float(f['armSeamWeight'][i]*(1-t)+f['armSeamWeight'][j]*t);w=float(f['forearmBlendWeight'][i]*(1-t)+f['forearmBlendWeight'][j]*t)
    if a<=1e-12:continue
    def correction(side):return(1-a)*branch('torso',v)[0]+a*((1-w)*branch('upperArm.'+side,v)[0]+w*branch('forearm.'+side,v)[0])
    dl=correction('L');dr=correction('R');analytic=parameters(s)
    rows.append({'sourceEdgeVertexIDs':[i,j],'crossingFraction':t,'sourceMidlineXYZ':s.tolist(),'nativeMidlineXYZM':v.tolist(),'barycentricAlpha':a,'barycentricForeWeight':w,'originalSourceAnalyticAlpha':analytic[0],'originalSourceAnalyticForeWeight':analytic[1],'leftSideDeltaM':dl.tolist(),'rightSideDeltaM':dr.tolist(),'sideSwitchJumpM':float(np.linalg.norm(dr-dl))})
rows.sort(key=lambda r:r['sideSwitchJumpM'],reverse=True)
report={'status':'UNACCEPTED side-switch hypothesis tested, no seam leak observed' if not rows else 'FAILED observed barycentric parameter side seam discontinuity','pins':pins,'recipeSHA256':sha(__file__),'existingVertexAnalyticAlphaMaximumError':float(alphaError.max()),'existingVertexAnalyticForeWeightMaximumError':float(foreError.max()),'midlineEdgesWithPositiveBarycentricAlpha':len(rows),'maximumSideSwitchJumpM':max([r['sideSwitchJumpM'] for r in rows],default=0),'allCrossingWitnesses':rows,
        'finding':('Positive barycentric arm mass at sourceX=0 creates an observed L/R branch jump; original analytic weights match existing vertices.' if rows else 'No initial source18 edge crosses sourceX=0 with positive interpolated arm mass. Original analytic construction parameters match all frozen vertices exactly. The side-switch discontinuity hypothesis is NOT supported for this failed refinement; no analytic-weight repair is justified by this result.'),
        'limits':['No new fit/radius/centre/support parameters, weights, native save, refinement retry, body/head/51bind change or capture. This is construction parameter continuity, not garment skinning.','Does not prove all full-field discontinuities absent or wearing/rig/mobile/art/M0-M5 acceptance. Native19 remains493body/35self failed; no inference/worker/Library/player promotion.']}
assert pins=={p:sha(p) for p in pins};out.write_text(json.dumps(report,indent=2)+'\n');print('CONSTRUCTION_PARAMETER_SEAM_DIAGNOSED','edges',len(rows),'maxJumpM',report['maximumSideSwitchJumpM'],'existingParameterErrors',float(alphaError.max()),float(foreError.max()),flush=True)
