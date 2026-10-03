"""Read-only attribution of independently reported cage182 collapse witnesses."""
from pathlib import Path
import numpy as np,json,collections,hashlib
H=Path(__file__).resolve().parent;c=np.load(H/'cage01.npz');P=c['p'];F=c['f'];tags=json.loads((H/'quad-face-tags.json').read_text());faceTags=[];polygons=[];cursor=0
for pi,tag in enumerate(tags):
 count=1 if tag.endswith(' triangle') else 2
 faceTags.extend([tag]*count);polygons.extend([pi]*count);cursor+=count
assert cursor==len(F)
X=P[F].astype('f8');area=np.linalg.norm(np.cross(X[:,1]-X[:,0],X[:,2]-X[:,0]),axis=1)/2
zero=area<1e-12;groups=collections.defaultdict(list)
for i,p in enumerate(P):groups[tuple(p)].append(i)
repeated=[g for g in groups.values() if len(g)>1];blocks=[]
for row,h in enumerate([.98,1.08,1.18,1.28],1):
 start=row*64;local=collections.defaultdict(list)
 for i in range(start,start+64):local[tuple(P[i])].append(i)
 dup=[g for g in local.values() if len(g)>1];blocks.append({'rowY':h,'nodes':64,'uniquePositions':len(local),'duplicateGroups':dup,'firstWitnessPositions':[P[g[0]].tolist() for g in dup[:2]],'cause':'Nearest eight angular source vertices followed by maximum radius selects the same discrete donor for multiple bins. Each bin has its own semantic node ID despite identical positions; no continuous source segment interpolation.'})
hems=[]
for i,tag in enumerate(faceTags):
 if tag.startswith('hem transition') and zero[i]:hems.append({'face':i,'tag':tag,'vertices':F[i].tolist(),'areaM2':float(area[i]),'positionsM':P[F[i]].tolist()})
sleeves=[]
for side,start in [(0,847),(1,1012)]:
 for row in range(5):
  ids=range(start+20*row,start+20*(row+1));dd=collections.defaultdict(list)
  for i in ids:dd[tuple(P[i])].append(i)
  dup=[g for g in dd.values() if len(g)>1]
  sleeves.append({'side':side,'row':row,'uniquePositions':len(dd),'duplicateGroups':dup})
bytag={tag:{'triangles':int(sum(t==tag for t in faceTags)),'areaBelow1e12':int(sum(bool(z) and t==tag for z,t in zip(zero,faceTags))),'exactZeroArea':int(sum(a==0 and t==tag for a,t in zip(area,faceTags)))} for tag in sorted(set(faceTags))}
report={'status':'FAILED_FINAL_GEOMETRY_CAUSE_ATTRIBUTED_READ_ONLY','cageSHA256':hashlib.sha256((H/'cage01.npz').read_bytes()).hexdigest(),'storedFloat32EvaluatedFloat64':True,'degenerateBelow1e12':int(zero.sum()),'exactZeroArea':int((area==0).sum()),'rawDuplicatePositionGroups':len(repeated),'rawExcessCoincidentRows':sum(len(g)-1 for g in repeated),'faceTagStats':bytag,'discreteProfilePlateaus':blocks,'sleeveAngleTransfer':{'rows':sleeves,'mechanism':'Each sleeve row uses atan2 of the root perimeter projected into X/Y, discarding lateral coordinate; repeated root profile points therefore transfer repeated angles into every circular sleeve row. This is a consequence of profile plateaus/parametrization, not a cuff-height mapping bug.'},'zeroWidthHemTransition':{'mechanism':'torso0 is an arc-length resampling of exactly the same final hem curve as exacthem. Zippering between those two co-located representations gives no positive material strip width. bco0 and exacthem0 are exactly identical. Points on the same source edge create collinear triangles; float32 interpolation does not supply a coherent finite surface. Separate semantic IDs do not prevent literal coincidence.','firstRowPoint':P[0].tolist(),'exactHemFirstPoint':P[c['hemIDs'][0]].tolist(),'firstPointsEqual':bool(np.array_equal(P[0],P[c['hemIDs'][0]])),'affectedAreaBelow1e12':len(hems),'firstWitnesses':hems[:6]},'minimalBuilderActions':['Use one physical hem boundary: integrate the existing156-node ring directly, or author a genuinely distinct nonzero-width interior row with explicit material correspondence. A zipper between two samplings of the same curve is not a material patch.','Use continuous ordered measured section segments with triangle/barycentric provenance, rather than repeatedly selecting a discrete maximum-radius donor among eight angular neighbors. Check each profile cycle is injective and simple before connecting rows.','Recompute sleeve section parameterization on an injective material perimeter; projecting the root into X/Y alone can merge distinct lateral points. Require final float32 distinct physical IDs/edges and nonzero face areas, while preserving exact hood/cuff boundaries.'],'limits':'No repairs, original edits, build execution, rendering, rigging or motion tests. Full incidence/winding/seam judgments remain independent QA outputs. Protected source/cut checks are separate PASS contracts, not a final cage PASS.'}
(H/'source-guided-cage182-collapse-attribution.json').write_text(json.dumps(report,indent=2))
summary={'reportSHA256':hashlib.sha256((H/'source-guided-cage182-collapse-attribution.json').read_bytes()).hexdigest(),'degenerateBelow1e12':int(zero.sum()),'rawGroups':len(repeated),'rawExcess':sum(len(g)-1 for g in repeated),'faceTagStats':bytag,'hemWitnesses':hems[:2],'sleeveDuplicateRows':[x for x in sleeves if x['duplicateGroups']]}
print(json.dumps(summary,indent=2))
