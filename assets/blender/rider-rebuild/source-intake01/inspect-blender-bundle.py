"""Read official anatomical asset metadata/topology; no construction or rendering."""
import bpy,json,hashlib,sys
from pathlib import Path
from collections import Counter
args=sys.argv[sys.argv.index('--')+1:];out=Path(args[0]);out.mkdir(parents=True,exist_ok=False)
source=Path(bpy.data.filepath)
report={'accepted':False,'kind':'read-only conventional foundation intake','source':str(source),'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'blenderVersion':bpy.app.version_string,'objects':[],'texts':{t.name:t.as_string() for t in bpy.data.texts},'limits':['Metadata/base topology only; no rig, dressed motion or art acceptance.']}
for obj in bpy.data.objects:
 asset=obj.asset_data
 row={'name':obj.name,'type':obj.type,'asset':None if asset is None else {'author':asset.author,'description':asset.description,'copyright':asset.copyright,'license':asset.license,'tags':[t.name for t in asset.tags]},'properties':{k:str(v) for k,v in obj.items()},'matrixWorld':[list(r) for r in obj.matrix_world],'modifiers':[{'name':m.name,'type':m.type} for m in obj.modifiers]}
 if obj.type=='MESH':
  me=obj.data;count=Counter(len(p.vertices) for p in me.polygons);uses=Counter()
  for p in me.polygons:
   for i,a in enumerate(p.vertices):uses[tuple(sorted((a,p.vertices[(i+1)%len(p.vertices)])))]+=1
  row.update(vertices=len(me.vertices),edges=len(me.edges),polygons=len(me.polygons),polygonSizes=dict(count),boundaryEdges=sum(n==1 for n in uses.values()),nonmanifoldEdges=sum(n>2 for n in uses.values()),looseEdges=len(me.edges)-len(uses),vertexGroups=[g.name for g in obj.vertex_groups],materials=[m.name if m else None for m in me.materials],uvLayers=[l.name for l in me.uv_layers],shapeKeys=[] if not me.shape_keys else [k.name for k in me.shape_keys.key_blocks],bounds=[[min(v.co[i] for v in me.vertices),max(v.co[i] for v in me.vertices)] for i in range(3)] if len(me.vertices) else [])
 if obj.type=='ARMATURE':row['bones']=[{'name':b.name,'parent':b.parent.name if b.parent else None,'deform':b.use_deform} for b in obj.data.bones]
 report['objects'].append(row)
report['collections']=[{'name':c.name,'objects':[o.name for o in c.all_objects],'asset':None if c.asset_data is None else {'author':c.asset_data.author,'description':c.asset_data.description,'copyright':c.asset_data.copyright,'license':c.asset_data.license}} for c in bpy.data.collections if c.asset_data]
body=bpy.data.objects.get('GEO-body_male_realistic')
if body is not None:
 me=body.data;neighbors={v.index:set() for v in me.vertices};oriented=Counter()
 for p in me.polygons:
  for i,a in enumerate(p.vertices):
   b=p.vertices[(i+1)%len(p.vertices)];neighbors[a].add(b);neighbors[b].add(a);oriented[(a,b)]+=1
 remaining=set(neighbors);components=[]
 while remaining:
  todo=[remaining.pop()];size=0
  while todo:
   a=todo.pop();size+=1
   for b in neighbors[a]:
    if b in remaining:remaining.remove(b);todo.append(b)
  components.append(size)
 report['realisticMaleTopology']={'components':components,'orientationConflicts':sum(n!=1 or oriented[(b,a)]!=1 for (a,b),n in oriented.items()),'euler':len(me.vertices)-len(me.edges)+len(me.polygons)}
 (out/'realistic-male-base.json').write_text(json.dumps({'positions':[list(v.co) for v in me.vertices],'polygons':[list(p.vertices) for p in me.polygons],'matrixWorld':[list(r) for r in body.matrix_world]})+'\n')
(out/'inventory.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'objects':len(report['objects']),'assets':sum(o['asset'] is not None for o in report['objects']),'output':str(out/'inventory.json')}))
