"""One fixed correction03 pattern prediction; no native/scene changes."""
import ast,hashlib,json,runpy
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[5]
def main():
 leaf=Path(__file__).parent;c=json.loads((leaf/'controls.json').read_text());d=np.load(ROOT/c['savedArrays']['path']);cut=json.loads((ROOT/c['expandedCut']['path']).read_text())
 f=runpy.run_path(str(ROOT/c['patternSource']['path']));scope={'np':np};tree=ast.parse((leaf.parent/'correction02/diagnose_saved_arrays.py').read_text());exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='inside'],type_ignores=[]),'body-parity','exec'),scope)
 records=[];positions=d['vertices'];raw=d['actual_donor_display_xyz'];fields=np.ones((len(positions),1))
 for p in c['panels']:
  sidecut=next(s for s in cut['sides']if s['side']==p['side']);boundary=sidecut['orientedBoundaryCycles'][p['boundaryCycle']]
  outer=next(x for x in c['panels']if x['side']==p['side']and not x['interior']);outer_anchors=positions[outer['anchors']]
  result=f['patch'](boundary,p['anchors'],positions,raw,fields,p['side'],p['interior'],outer_anchors,c['cloth'])
  points=result['positions'];fold=[];centers=[];triangles=[]
  for fi,face in enumerate(result['faces']):
   q=np.asarray([positions[-k-1]if k<0 else points[k]for k in face]);centers.append(q.mean(0))
   if len(q)==4:
    n1=np.cross(q[1]-q[0],q[2]-q[0]);n2=np.cross(q[2]-q[0],q[3]-q[0]);den=np.linalg.norm(n1)*np.linalg.norm(n2)
    if den<1e-20 or n1@n2<0:fold.append(fi)
   for j in range(1,len(q)-1):triangles.append(q[[0,j,j+1]])
  inside=scope['inside'](points,d['canonicalBodyVertices'],d['canonicalBodyFaces']);faceinside=scope['inside'](centers,d['canonicalBodyVertices'],d['canonicalBodyFaces'])
  records.append({'role':p['role'],'side':p['side'],'interior':p['interior'],'generatedPoints':len(points),'quads':result['regularQuads'],'transitionTriangles':result['transitionTriangles'],'opposedOrDegenerateFanQuads':fold,'generatedPointsInsideBody':np.flatnonzero(inside).tolist(),'faceCentersInsideBody':np.flatnonzero(faceinside).tolist()})
 report={'accepted':False,'stage':'SAME_FIXED_PATTERN_SINGLE_ANATOMICAL_SEAM_LANDMARK_CORRECTION_NO_NATIVE_EDIT','patternSHA256':hashlib.sha256((ROOT/c['patternSource']['path']).read_bytes()).hexdigest(),'controlsSHA256':hashlib.sha256((leaf/'controls.json').read_bytes()).hexdigest(),'panels':records,'limits':['Predicted arrays only; no native geometry/atlas/model job.','Fan tests apply to quads; transition triangles require intersection checks and actual viewed review.','Outside/parity counts do not prove full wearing or selected form. No parameter search.']}
 out=ROOT/'docs/evidence/rider-rebuild/hoodie-shoulder-anatomical04/correction03/prediction-landmark-fix.json';assert not out.exists();out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps([{k:(len(v)if isinstance(v,list)else v)for k,v in r.items()}for r in records]))
if __name__=='__main__':main()
