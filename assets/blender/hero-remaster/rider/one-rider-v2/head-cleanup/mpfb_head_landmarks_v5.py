"""One targeted fresh-anatomy correction: remove snaps, fit smooth landmarks.

No dense surface projection, remesh, historical donor, texture bake or join.
Initial authored landmark movements are not the old 4mm dense-fit bound.
"""
import argparse, hashlib, json, sys
from pathlib import Path
import bpy
import numpy as np
from mathutils import Vector
from mathutils.kdtree import KDTree

ap=argparse.ArgumentParser(description=__doc__)
ap.add_argument('--source',required=True)
ap.add_argument('--samples',required=True)
ap.add_argument('--reference',required=True)
ap.add_argument('--out',required=True)
a=ap.parse_args(sys.argv[sys.argv.index('--')+1:])
out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
if (out/'head.glb').exists():raise RuntimeError('Frozen correction exists')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
sources={p:sha(p) for p in [a.source,a.samples,a.reference]}
bpy.ops.wm.open_mainfile(filepath=a.source)
head=next(o for o in bpy.context.scene.objects if o.type=='MESH' and 'anatomical head' in o.data.name)
eye=next(o for o in bpy.context.scene.objects if o.type=='MESH' and 'eyes' in o.data.name)
samples=np.load(a.samples)['samples']
tree=KDTree(len(head.data.vertices))
for v in head.data.vertices:tree.insert(v.co,v.index)
tree.balance();restored=[]
for initial,final in samples:
    co,index,distance=tree.find(Vector(final))
    if distance>1e-7:raise RuntimeError('Recorded dense-snap vertex mismatch')
    if index in restored:raise RuntimeError('Ambiguous snap provenance')
    head.data.vertices[index].co=Vector(initial);restored.append(index)
head.data.update()
def native(co):return np.array([co.x,co.z,-co.y])
def canonical(p):return Vector((float(p[0]),float(-p[2]),float(p[1])))
# Manual front reference landmarks: pupils(481,414)/(701,414),
# chin(589,805), mouth(588,632), jawangles(400,706)/(785,706).
# Normalize using measured native eye center distance .156924.
# Depth/brow prominence remain explicitly authored 3D hypotheses.
anchors=np.array([[0,-.117967,.171723],[-.115684,-.065009,.116365],
    [.115684,-.065009,.116365],[0,-.025,.232],
    [-.081,.151,.219],[.081,.151,.219],
    [-.078462,.111,.169],[.078462,.111,.169],[0,.035,.256]])
targets=np.array([[0,-.168,.173],[-.137,-.097,.118],
    [.137,-.097,.118],[0,-.0445,.232],
    [-.081,.155,.231],[.081,.155,.231],
    [-.078462,.111,.169],[.078462,.111,.169],[0,.035,.256]])
widths=np.array([.075,.075,.075,.045,.028,.028,.032,.032,.040])
dist=np.linalg.norm(anchors[:,None,:]-anchors[None,:,:],axis=2)
kernel=np.exp(-(dist/widths[None,:])**2)
coefficients=np.linalg.solve(kernel+np.eye(len(anchors))*1e-9,targets-anchors)
def field(points):
    d=np.linalg.norm(points[:,None,:]-anchors[None,:,:],axis=2)
    return np.exp(-(d/widths[None,:])**2)@coefficients
displacement={}
for obj in [head,eye]:
    points=np.array([native(v.co) for v in obj.data.vertices])
    delta=field(points); moved=points+delta
    for v,p in zip(obj.data.vertices,moved):v.co=canonical(p)
    obj.data.update()
    length=np.linalg.norm(delta,axis=1)
    displacement[obj.name]=dict(vertices=len(points),maximumNative=float(length.max()),
        percentilesNative=np.percentile(length,[50,95,99]).tolist())
for obj in bpy.context.scene.objects:obj.select_set(obj in [head,eye])
bpy.context.view_layer.objects.active=head
bpy.ops.wm.save_as_mainfile(filepath=str(out/'head.blend'))
bpy.ops.export_scene.gltf(filepath=str(out/'head.glb'),export_format='GLB',use_selection=True,export_yup=True)
head.data.calc_loop_triangles()
vertices=np.array([native(v.co) for v in head.data.vertices],dtype=np.float32)
faces=np.array([t.vertices[:] for t in head.data.loop_triangles],dtype=np.int32)
np.savez(out/'head-skin.npz',vertices=vertices,faces=faces)
report=dict(status='UNACCEPTED single targeted landmark/scar-removal correction; gray review',
    sources=sources,sourcesAfter={p:sha(p) for p in sources},scriptSHA256=sha(__file__),
    restoredDenseSnapVertices=len(restored),laterDenseFit=dict(count=0,maximumNative=0,
        reason='Rejected narrow snap created cheek/nose scar; no surface projection in correction.'),
    authoredInitialLandmarks=dict(sourceNative=anchors.tolist(),targetNative=targets.tolist(),
        widthsNative=widths.tolist(),coefficients=coefficients.tolist(),
        interpolation='Gaussian RBF landmark field, continuous, same field for head/eyes',
        appliedDisplacements=displacement,
        targetInterpretation='Front-reference manual pixel measurements normalized by actual previous native IPD; depth hypotheses authored.'),
    referencePixelLandmarks=dict(pupils=[[481,414],[701,414]],chin=[589,805],mouth=[588,632],
        jawAngles=[[400,706],[785,706]]),
    unchangedTopology=dict(skinVertices=len(vertices),skinTriangles=len(faces)),
    limits=['No identity or geometry acceptance is claimed.',
        'Initial landmark changes exceed .004native and are distinct from zero later dense fit.',
        'Source UV coordinates remain absent; no texture/detail bake.',
        'Neck base remains source-derived, unjoined, and unaccepted.',
        'Brow prominence and depth are authored hypotheses requiring actual visual judgment.',
        'No historical donor, global remesh/projection, GPU, or new AI sampling.'])
assert sources==report['sourcesAfter']
(out/'construction.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report),flush=True)
