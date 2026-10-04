"""Controlled shading-only comparison on exact source24; reuse flat pixels."""
import argparse, collections, hashlib, json, math, shutil, sys, time
from pathlib import Path
import bpy, numpy as np
from mathutils import Vector
ap=argparse.ArgumentParser(description=__doc__)
for k in ['source','reuse-review','out']:ap.add_argument('--'+k,required=True)
a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);source,reuse,out=[Path(getattr(a,k.replace('-','_'))).resolve() for k in ['source','reuse-review','out']];reuseData=json.loads(reuse.read_text());setup=Path(__file__).with_name('render_actual_donor_rest_review.py');sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();assert sha(setup)==reuseData['recipeSHA256'];assert sha(source)==reuseData['nativeCandidateSHA256'];registration=next(Path(p) for p in reuseData['pins'] if p.endswith('/construct_selected_hoodie.py'));transfer=next(Path(p) for p in reuseData['pins'] if p.endswith('/repair_selected_texture_transfer.py'));pins={str(p):sha(p) for p in [source,reuse,setup,registration,transfer]};assert all(sha(Path(p))==digest for p,digest in reuseData['pins'].items());ownFile=Path(__file__).resolve()
# Replay the identical studio setup only; no renderer loop or source save.
sys.argv=sys.argv[:sys.argv.index('--')+1]+['--source',str(source),'--registration-recipe',str(registration),'--transfer-recipe',str(transfer),'--out',str(out)];code=setup.read_text();exec(compile(code[:code.index('for index in range(48):')],str(setup),'exec'));pins={str(p):sha(p) for p in [source,reuse,setup,registration,transfer]}
m=actual.data;positions=np.array([v.co[:] for v in m.vertices]);m.calc_loop_triangles();triangles=np.array([t.vertices[:] for t in m.loop_triangles]);cycles=[list(p.vertices) for p in m.polygons];uvs=np.array([v.uv[:] for v in m.uv_layers.active.data]);normals=np.array([v.vector[:] for v in m.corner_normals]);edges=collections.defaultdict(list)
for poly in m.polygons:
    ids=list(poly.vertices)
    for i in range(len(ids)):edges[tuple(sorted((ids[i],ids[(i+1)%len(ids)])))].append(poly.index)
face=np.array([p.normal[:] for p in m.polygons]);sharp=set()
for edge,adj in edges.items():
    if len(adj)==2 and np.degrees(np.arccos(np.clip(face[adj[0]]@face[adj[1]],-1,1)))>30:sharp.add(edge)
assert len(sharp)==2671
controls=[]
for key,label,keep in [('smoothAll','SAME GEOMETRY / ALL-SMOOTH NORMALS',False),('smooth30','SAME GEOMETRY / 30 DEGREE CREASES',True)]:
    obj=actual.copy();obj.data=actual.data.copy();bpy.context.collection.objects.link(obj);obj.name='Display-only '+key+' actual donor24';obj.data.polygons.foreach_set('use_smooth',np.ones(len(obj.data.polygons),dtype=np.bool_))
    for e in obj.data.edges:e.use_edge_sharp=keep and tuple(sorted(e.vertices)) in sharp
    obj.data.update();obj.data.calc_loop_triangles();assert np.array_equal(np.array([v.co[:] for v in obj.data.vertices]),positions);assert np.array_equal(np.array([t.vertices[:] for t in obj.data.loop_triangles]),triangles);assert [list(p.vertices) for p in obj.data.polygons]==cycles;assert np.array_equal(np.array([v.uv[:] for v in obj.data.uv_layers.active.data]),uvs);assert obj.data.materials[0] is actual.data.materials[0];obj.hide_render=True;controls.append((key,label,obj));(out/key).mkdir(exist_ok=True)
(out/'flat').mkdir(exist_ok=True);arrays={'nativePositions':positions,'triangles':triangles,'UVs':uvs,'flatCornerNormals':normals}
for key,label,obj in controls:arrays[key+'CornerNormals']=np.array([n.vector[:] for n in obj.data.corner_normals])
archive=out/'normal-display.npz'
if archive.exists():
    previous=np.load(archive);assert set(previous.files)==set(arrays);assert all(np.array_equal(previous[k],v) for k,v in arrays.items())
else:np.savez_compressed(archive,**arrays)
frames=[];start=time.monotonic()
for index in range(48):
    oldFrame=reuseData['frames'][index];yaw=oldFrame['yawRadians'];camera.location=target+Vector((4*math.cos(yaw),4*math.sin(yaw),.30));camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler();bpy.context.view_layer.update();assert np.array_equal(np.array([list(r) for r in camera.matrix_world]),np.array(oldFrame['cameraWorldRows']));existing=reuse.parent/'fitted24'/f'{index:04d}.png';oldHash=next(v['PNG_SHA256'] for v in oldFrame['views'] if v['variant']=='fitted24');assert sha(existing)==oldHash;shutil.copyfile(existing,out/'flat'/f'{index:04d}.png');views=[{'variant':'flat','PNG_SHA256':oldHash,'reusedFrom':str(existing)}]
    for key,label,obj in controls:
        obj.hide_render=False;obj.hide_set(False);font.body=label+'\nDISPLAY TEST / NO VERTEX+UV CHANGE';scene.render.filepath=str(out/key/f'{index:04d}.png');bpy.ops.render.render(write_still=True);views.append({'variant':key,'PNG_SHA256':sha(scene.render.filepath),'object':obj.name});obj.hide_render=True
    frames.append({'index':index,'yawRadians':yaw,'cameraWorldRows':[list(r) for r in camera.matrix_world],'views':views})
    if index%4==0:print('FROZEN_NORMAL_COMPARISON',index,'elapsedS',round(time.monotonic()-start,1),flush=True)
record={'status':'UNACCEPTED display-only actual donor24 normal comparison','pins':pins,'recipeSHA256':sha(ownFile),'nativeCandidateSHA256':sha(source),'variants':[{'key':'flat','label':'ACTUAL24 / CURRENT FLAT','reusedAll48Frames':True}]+[{'key':k,'label':label,'allSmoothFaces':len(obj.data.polygons),'sharpEdges':sum(e.use_edge_sharp for e in obj.data.edges)} for k,label,obj in controls],'frames':frames,'movieFrameSequence':reuseData['movieFrameSequence'],'sourceFramesPerSecond':reuseData['sourceFramesPerSecond'],'durationS':reuseData['durationS'],'normalDisplayFieldSHA256':sha(out/'normal-display.npz'),'geometryTrianglesPolygonCyclesUVOriginalMaterialExact':True,'render':'Exact review85camera/studio/CyclesCPU2threads8samples/AgX/640square; flat48frames reusedbyteforbyte; two new shading-only controls.','limits':['All-smooth is a diagnostic control and can hide actual crease shading;30degree control preserves2671measurededges. Neither alters vertices/silhouette/triangulation or repairs geometry/inflated ease.','No source save, actualnormalasset adoption/recolor/shrink/rig/motion/body-head-51bind change/inference/worker/Library/player promotion. Parentalonejudges/allM0-M5/mobile and24coverage remain open.']};assert pins=={p:sha(Path(p)) for p in pins};(out/'review.json').write_text(json.dumps(record,indent=2)+'\n');print('FROZEN_NORMAL_COMPARISON_READY',flush=True)
