"""One parent-requested predicted-array diagnostic; no Blender/native edit."""
import ast,json,sys
from pathlib import Path
from types import SimpleNamespace
import numpy as np
ROOT=Path(__file__).resolve().parents[5]
LEAF=Path(__file__).resolve().parent

def extracted_functions(path,names):
 tree=ast.parse(path.read_text());module=ast.Module(body=[node for node in tree.body if isinstance(node,ast.FunctionDef)and node.name in names],type_ignores=[])
 scope={'np':np};exec(compile(module,str(path),'exec'),scope);return scope

def main():
 c=json.loads((LEAF/'controls.json').read_text());d=np.load(ROOT/c['savedPanelsIntake']['path'])
 funcs=extracted_functions(LEAF/'author_correction.py',{'curve','panel_parameters','ruled_surface','actual_components'})
 test=extracted_functions(LEAF/'diagnose_saved_arrays.py',{'inside'})['inside']
 vertices=d['vertices'];predicted=vertices.copy();starts=d['polygonStarts'];counts=d['polygonCounts'];corners=d['cornerVertexIds'];original=d['_panel04_original_vertex_id']
 mesh=SimpleNamespace(vertices=[SimpleNamespace(co=p)for p in vertices],polygons=[SimpleNamespace(vertices=corners[s:s+n])for s,n in zip(starts,counts)])
 newfaces=np.flatnonzero(d['_panel04_original_face_id']==-1).tolist();groups=funcs['actual_components'](mesh,newfaces)
 source_controls=json.loads((ROOT/c['originalPanelControls']['path']).read_text());byold={int(old):i for i,old in enumerate(original)if old>=0};records=[]
 for panel in c['panels']:
  oldspec=next(x for x in source_controls['components']if x['label']==panel['component']);boundary=[byold[i]for i in oldspec['boundaryVertexIds']]
  faceids=next(fs for fs in groups if set(boundary)<=set(v for fi in fs for v in mesh.polygons[fi].vertices))
  cornerids=[byold[i]for i in panel['anatomicalCornerOriginalVertexIds']]
  params,arcs,interior=funcs['panel_parameters'](mesh,faceids,boundary,cornerids)
  surface=funcs['ruled_surface'](vertices,arcs)
  for vi in interior:predicted[vi]=surface(*params[vi])
  records.append({'component':panel['component'],'faces':faceids,'interior':interior,'corners':[{'originalVertex':old,'actualVertex':byold[old],'XYZ':vertices[byold[old]].tolist()}for old in panel['anatomicalCornerOriginalVertexIds']]})
 assert np.array_equal(predicted[original>=0],vertices[original>=0])
 newids=np.flatnonzero(original==-1);inside=test(predicted[newids],d['canonicalBodyVertices'],d['canonicalBodyFaces']);normalbad=[];centerpoints=[]
 for fi in newfaces:
  ids=corners[starts[fi]:starts[fi]+counts[fi]];q=predicted[ids];n1=np.cross(q[1]-q[0],q[2]-q[0]);n2=np.cross(q[2]-q[0],q[3]-q[0]);den=np.linalg.norm(n1)*np.linalg.norm(n2);cos=np.dot(n1,n2)/den if den>1e-20 else -1
  if cos<0:normalbad.append({'face':fi,'vertices':ids.tolist(),'fanNormalCosine':float(cos)})
  centerpoints.append(q.mean(0))
 centerinside=test(centerpoints,d['canonicalBodyVertices'],d['canonicalBodyFaces'])
 result={'accepted':False,'stage':'ONE_PREDICTED_ARRAY_DIAGNOSTIC_SAME_FIXED_AUTHOR_FUNCTIONS_NO_NATIVE_EDIT','actualBaseline':{'opposedFanNormalQuads':10,'newVerticesInsideBody':156,'newQuadCentersInsideBody':164},'prediction':{'opposedFanNormalQuads':len(normalbad),'newVerticesInsideBody':int(inside.sum()),'newQuadCentersInsideBody':int(centerinside.sum()),'opposedFaces':normalbad,'insideVertexIds':newids[inside].tolist(),'insideFaceCenters':np.asarray(newfaces)[centerinside].tolist()},'panels':records,'allRetainedPointsExact':True,'oneSolveNoSearch':True,'limits':['These are predicted arrays, not saved authored geometry or judged rendered views.','No parameter changes are made by this diagnostic. Canonical torso parity does not certify cloth wearing.']}
 out=ROOT/'docs/evidence/rider-rebuild/hoodie-shoulder-anatomical04/correction02/prediction-once.json';assert not out.exists();out.write_text(json.dumps(result,indent=2,default=lambda value:int(value) if isinstance(value,np.integer) else float(value))+'\n');print(json.dumps({k:v for k,v in result['prediction'].items()if isinstance(v,int)}))
if __name__=='__main__':main()
