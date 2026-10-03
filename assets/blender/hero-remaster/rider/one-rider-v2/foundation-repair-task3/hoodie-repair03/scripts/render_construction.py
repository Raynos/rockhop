"""CPU diagnostic images of a frozen local construction, with recorded D304.
The exporter supplies materials/attributes; NPZ supplies literal topology and
fresh weights. This is visual evidence, not stock WebGL or gameplay acceptance.
"""
from pathlib import Path
import sys, json, math, hashlib
import numpy as np
import bpy
from mathutils import Vector, Matrix, Quaternion

ROOT = Path('/Users/raynos/projects/games/rockhop/assets/blender/hero-remaster/rider/one-rider-v2/foundation-repair-task3')
args = sys.argv[sys.argv.index('--') + 1:]
candidate, exported, label = Path(args[0]), Path(args[1]), args[2]
assert label.replace('-', '').replace('_', '').isalnum()
data = np.load(candidate)
record = json.loads((ROOT / 'hoodie-repair03/inputs/recorded-side304.json').read_text())
sample = record['sample']
setup = (ROOT / 'scripts/render_stills.py').read_text().split('cases=sys.argv')[0]
setup = setup.replace('root=Path.cwd()', 'root=ROOT')
setup = setup.replace('lookup={}', "lookup={};primitive_offsets=np.r_[0,np.cumsum([len(g.array(p['attributes']['POSITION']))for p in prims])];referenced=np.unique(np.concatenate([g.array(p['indices']).reshape(-1).astype(int)+primitive_offsets[i]for i,p in enumerate(prims)]))")
setup = setup.replace('for i,v in enumerate(r):lookup.setdefault', 'for i in referenced:\n v=r[i];lookup.setdefault')
# Rest positions alone cannot distinguish a physically separated hem whose
# coincident shirt and pants rows have different skin weights. Match both.
setup = setup.replace('maps=[]', "joint_names=[g.j['nodes'][j]['name']for j in g.j['skins'][0]['joints']];source_weights=[]\nfor pr in prims:\n wi=np.zeros((len(g.array(pr['attributes']['POSITION'])),len(joint_names)));jj=g.array(pr['attributes']['JOINTS_0']).astype(int);ww=g.array(pr['attributes']['WEIGHTS_0']).astype(float);wi[np.arange(len(wi))[:,None],jj]=ww;wi/=wi.sum(1,keepdims=True);source_weights.append(wi)\nsource_weights=np.concatenate(source_weights);maps=[]")
setup = setup.replace('for v in world:', 'for vertex_index,v in enumerate(world):')
setup = setup.replace('best=min(cand,key=lambda j:np.linalg.norm(r[j]-v));', "distance=np.array([np.linalg.norm(r[j]-v)for j in cand]);near=[j for j,dd in zip(cand,distance)if dd<=distance.min()+2e-7];imported_weight=np.zeros(len(joint_names))\n  for assignment in o.data.vertices[vertex_index].groups:\n   group_name=o.vertex_groups[assignment.group].name\n   if group_name in joint_names:imported_weight[joint_names.index(group_name)]+=assignment.weight\n  imported_weight/=imported_weight.sum();best=min(near,key=lambda j:np.max(abs(source_weights[j]-imported_weight)));assert np.max(abs(source_weights[best]-imported_weight))<2e-6,(o.name,vertex_index); ")
setup = setup.replace("root/'baseline/rider.glb'", 'Path(' + repr(str(exported)) + ')')
exec(compile(setup, str(ROOT / 'scripts/render_stills.py'), 'exec'))
if '--map-only' in args:
    exported.with_suffix('.map-proof.json').write_text(json.dumps({'importMap':'Referenced coordinate+normalized joint weights', 'candidateSHA256':hashlib.sha256(candidate.read_bytes()).hexdigest(), 'meshes':[{ 'name':o.name,'mappedVertices':len(ix)}for o,ix in zip(meshes,maps)],'status':'Import mapping verified only; no visual approval'},indent=2)+'\n')
    print('REFERENCED WEIGHT MAPPING PASS');sys.exit(0)
CC = np.array([[1, 0, 0], [0, 0, -1], [0, 1, 0]])
offset = np.r_[0, np.cumsum([len(data[f'p{i}']) for i in range(5)])]
actual = np.load(ROOT / 'hoodie-repair03/poses/game304-v7-plain.npz')
D304 = actual['matrices']
dest = ROOT / 'hoodie-repair03/renders/construction' / label
dest.mkdir(parents=True, exist_ok=True)
original = {o: list(o.data.materials) for o in meshes}
gray = mat('construction geometry diagnostic', (.42, .42, .42))
sc.cycles.samples = 6
for o in bikeobjects:
    o.hide_render = True

for state in (['recorded304'] if '--pose-only' in args else ['rest', 'recorded304']):
    D = np.repeat(np.eye(4)[None], 19, axis=0) if state == 'rest' else D304
    posed = [np.einsum('vj,jab,vb->va', data[f'W{i}'], D[:, :3, :], np.c_[data[f'p{i}'], np.ones(len(data[f'p{i}']))], optimize=False) for i in range(5)]
    if state == 'recorded304':
        # Original closed-grip hand geometry is held to the recorded control.
        # New clothing is only LBS; no old49 fitted correctives are applied.
        posed[1] = actual['p1']
    points = np.concatenate(posed) @ CC.T
    normals = np.concatenate([np.einsum('vj,jab,vb->va', data[f'W{i}'], D[:, :3, :3], data[f'n{i}'], optimize=False) for i in range(5)])
    normals /= np.maximum(np.linalg.norm(normals, axis=1, keepdims=True), 1e-15)
    normals = normals @ CC.T
    for obj, ix in zip(meshes, maps):
        obj.data.vertices.foreach_set('co', points[ix].astype('f4').ravel())
        obj.data.update()
        obj.data.normals_split_custom_set_from_vertices(normals[ix].tolist())
    if state == 'rest':
        views = [('front', 0), ('side', 90), ('back', 180)]
        sc.render.resolution_x = sc.render.resolution_y = 640
        d.type = 'ORTHO'
        d.shift_x = d.shift_y = 0
        d.ortho_scale = 1.95
    else:
        views = [('exact-side', None)]
        centres = np.load(ROOT / 'experiments/C19-bind.npz')['centres']
        Q = np.einsum('nij,nj->ni', D[:, :3, :], np.c_[centres, np.ones(19)])
        indices = [0, 2, 4, 6, 10]
        names = ['pelvis', 'chest', 'head', 'upperArmL', 'upperArmR']
        X = Q[indices]
        Y = np.array([sample['bones'][n]['position'] for n in names])
        xc, yc = X.mean(0), Y.mean(0)
        u, _, vt = np.linalg.svd((X - xc).T @ (Y - yc))
        rot = u @ vt
        translation = yc - xc @ rot
        error = float(np.linalg.norm(X @ rot + translation - Y, axis=1).max())
        assert error < 1e-6, error
        position = (np.array(sample['camera']['position']) - translation) @ rot.T
        q = sample['camera']['quaternion']
        camera_rotation = rot @ np.array(Quaternion([q[3], *q[:3]]).to_matrix())
        cam.location = Vector(CC @ position)
        cam.rotation_euler = Matrix((CC @ camera_rotation).tolist()).to_euler()
        d.type = 'PERSP'
        d.sensor_fit = 'HORIZONTAL'
        fovy = 2 * math.atan(math.tan(math.radians(sample['camera']['fov']) / 2) / sample['camera']['zoom'])
        d.lens = d.sensor_width / (2 * math.tan(fovy / 2) * (1280 / 720))
        view = sample['camera']['view']
        d.shift_x = view['offsetX'] / view['fullWidth']
        d.shift_y = -view['offsetY'] / view['fullWidth']
        sc.render.resolution_x, sc.render.resolution_y = 1280, 720
    for view, angle in views:
        if angle is not None:
            target = Vector((.63, 0, .91))
            cam.location = target + Vector((4 * math.cos(math.radians(angle)), 4 * math.sin(math.radians(angle)), .15))
            cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
        for appearance in ['pbr', 'gray']:
            for obj in meshes:
                for i in range(len(obj.data.materials)):
                    obj.data.materials[i] = gray if appearance == 'gray' else original[obj][i]
            sc.render.filepath = str(dest / f'{state}-{view}-{appearance}.png')
            bpy.ops.render.render(write_still=True)

(dest / 'render-provenance.json').write_text(json.dumps({
    'candidateNPZ': str(candidate), 'candidateSHA256': hashlib.sha256(candidate.read_bytes()).hexdigest(),
    'renderOnlyGLB': str(exported), 'glbSHA256': hashlib.sha256(exported.read_bytes()).hexdigest(),
    'frame': 304, 'cameraSource': record['sourceReportSHA256'], 'renderer': 'CPU Cycles 2 threads, 6 samples',
    'geometry': 'Rest and literal LBS with exact recorded19jointD; original closed hands held; no49correctives',
    'importMap': 'Referenced vertex only, coordinate tolerance plus normalized19joint weight matching; distinct physical coincident seam rows are disambiguated',
    'status': 'Unaccepted diagnostic; separate literal triangle and stock Three/Garage gates required.'
}, indent=2) + '\n')
print('CONSTRUCTION DIAGNOSTIC RENDER COMPLETE')
