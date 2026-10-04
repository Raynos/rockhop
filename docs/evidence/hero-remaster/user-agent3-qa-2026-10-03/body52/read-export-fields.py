"""Decode existing export fields and prove current native-body ancestry; no export."""
import hashlib, itertools, json, struct
from pathlib import Path
import numpy as np

root = Path.cwd(); out = Path(__file__).resolve().parent
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
native = np.load(out / 'native-fields.npz')
inventory = json.loads((out / 'inventory.json').read_text())
source = root / 'assets/blender/hero-remaster/rider/anatomical-foundation-2026-10-03/user-agent1/appearance10/rider-source-normals.glb'
expected = '8e4c5cff0e35b00a7ebc1686e8494fde9ef6388e012c8eebda31a508b3bc343c'
assert sha(source) == expected and not (out / 'export-fields.npz').exists()
data = source.read_bytes(); length = struct.unpack_from('<I', data, 12)[0]
g = json.loads(data[20:20+length]); binary = data[28+length:]
def acc(index):
    a = g['accessors'][index]; v = g['bufferViews'][a['bufferView']]
    assert 'sparse' not in a and 'extensions' not in v
    n = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}[a['type']]
    dtype = np.dtype({5126: '<f4', 5125: '<u4', 5123: '<u2', 5121: '<u1'}[a['componentType']])
    offset = v.get('byteOffset', 0) + a.get('byteOffset', 0)
    x = np.ndarray((a['count'], n), dtype=dtype, buffer=binary, offset=offset,
                   strides=(v.get('byteStride', n*dtype.itemsize), dtype.itemsize)).copy()
    if a.get('normalized'): x = x.astype(float)/np.iinfo(dtype).max
    return x
def local(n):
    if 'matrix' in n: return np.array(n['matrix']).reshape(4, 4).T
    x,y,z,w = n.get('rotation', [0,0,0,1])
    r = np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],
                  [2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],
                  [2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
    m = np.eye(4); m[:3,:3] = r@np.diag(n.get('scale', [1,1,1])); m[:3,3] = n.get('translation', [0,0,0]); return m
parents = {c:i for i,n in enumerate(g['nodes']) for c in n.get('children', [])}
world = {}
def matrix(i):
    if i not in world: world[i] = (matrix(parents[i]) if i in parents else np.eye(4))@local(g['nodes'][i])
    return world[i]
C = np.array([[1,0,0,0],[0,0,1,0],[0,-1,0,0],[0,0,0,1]],dtype=float)
names = native['boneNames'].tolist(); canonical = lambda n: n.replace('.','').replace('_','')
skin = g['skins'][0]; joint_names = [g['nodes'][i]['name'] for i in skin['joints']]
assert set(map(canonical,joint_names)) == set(map(canonical,names))
native_order=[list(map(canonical,names)).index(canonical(n)) for n in joint_names]
ibm = acc(skin['inverseBindMatrices']).reshape(-1,4,4).transpose(0,2,1).astype(float)
rest_world = np.array([matrix(i) for i in skin['joints']])
rest_native = np.einsum('ab,jbc->jac', C@native['rigWorld'], native['rigRest'][native_order])
rig_gap = float(np.abs(rest_world-rest_native).max()); assert rig_gap < 5e-6
report = {'status':'READ_ONLY_CURRENT_EXPORT_BODY_FIELDS_VERIFIED', 'GLBSHA256':expected,
          'nativeSourceSHA256':inventory['sourceSHA256'], 'recipeSHA256':sha(__file__),
          'jointOrder':joint_names, 'nativeBindWorldMaxAbsResidual':rig_gap,
          'nativeBindWorldMaxTranslationResidualM':float(np.linalg.norm(rest_world[:,:3,3]-rest_native[:,:3,3],axis=1).max()),
          'bodyHasSecondaryInfluenceSet':False, 'parts':{},
          'rootConditioningExtras':[{ 'name': n.get('name'), 'extras':n['extras']} for n in g['nodes'] if 'extras' in n and any('ondition' in k for k in n['extras'])],
          'limits':['Current existing appearance10 export is decoded only; no GLB/skin/geometry/rig/material rewrite or new capture.',
                    'Protected-head co-located native points can make nearest-point ancestry ambiguous; quantification is separate from fidelity acceptance.',
                    'Raw/loader four-slot normalization and current rendering policy are separated from full-native five-influence loss.']}
loader=root/'node_modules/three/examples/jsm/loaders/GLTFLoader.js'
assert 'mesh.bind( skeleton, _identityMatrix )' in loader.read_text()
report['GLTFLoaderSHA256']=sha(loader)
report['skinFrameDefinition']='Existing GLB positions are baked file-world XYZ. GLTFLoader binds at identity; attached-mode meshWorld cancels mesh bindMatrixInverse. Skin world=jointWorld*inverseBind*rawPosition, not mesh node world multiplied a second time.'
def condition_meta(value, trail=''):
    if isinstance(value,dict):
        for k,v in value.items():
            if 'ondition' in k: report.setdefault('conditioningMetadata',[]).append({'path':trail+'/'+k,'value':v})
            condition_meta(v,trail+'/'+k)
    elif isinstance(value,list):
        for i,v in enumerate(value):condition_meta(v,trail+'/'+str(i))
condition_meta(g)
arrays = {'inverseBinds':ibm, 'jointRestWorld':rest_world, 'jointNames':np.array(joint_names)}
labels = {'renderedBody':'base.002', 'protectedHead':'Protected textured head above hidden neck interface', 'cheek':'Protected coherent cheek patch'}
for label, wanted in labels.items():
    candidates = [(i,n) for i,n in enumerate(g['nodes']) if 'mesh' in n and (g['meshes'][n['mesh']]['name']==wanted or n.get('name')==wanted)]
    assert len(candidates)==1, (label,[(g['nodes'][i].get('name'),g['meshes'][n['mesh']]['name']) for i,n in candidates])
    i,node = candidates[0]; mesh=g['meshes'][node['mesh']]; assert len(mesh['primitives'])==1
    p=mesh['primitives'][0]; xyz=acc(p['attributes']['POSITION']).astype(float); triangles=acc(p['indices']).reshape(-1,3).astype('<i4')
    ids=acc(p['attributes']['JOINTS_0']).astype(int); weights=acc(p['attributes']['WEIGHTS_0']).astype(float)
    sums=weights.sum(1); assert np.min(sums)>0
    normalized=weights/sums[:,None]; dense=np.zeros((len(xyz),51))
    for k in range(4): np.add.at(dense,(np.arange(len(xyz)),ids[:,k]),normalized[:,k])
    mw=matrix(i); exported_world=xyz.copy()
    native_world=(np.column_stack([native[label+'XYZ'],np.ones(len(native[label+'XYZ']))])@(C@native[label+'World']).T)[:,:3]
    if label=='renderedBody':
        exported_ids=acc(p['attributes']['_SOURCE_ID']).reshape(-1).astype(int)
        by_id={int(s):n for n,s in enumerate(native[label+'SourceIDs'])}; map_ids=np.array([by_id[int(s)] for s in exported_ids])
        assert set(exported_ids)==set(native[label+'SourceIDs'].astype(int))
        assert set(tuple(t) for t in map_ids[triangles])==set(tuple(t) for t in native[label+'Triangles'])
        report['bodyHasSecondaryInfluenceSet']='JOINTS_1' in p['attributes']
    else:
        cell=3e-7; bins={}
        for vertex, q in enumerate(np.floor(native_world/cell).astype(int)):
            bins.setdefault(tuple(q),[]).append(vertex)
        chosen=[]; ambiguous=0
        for point in exported_world:
            q=np.floor(point/cell).astype(int)
            candidates=[vertex for offset in itertools.product([-1,0,1],repeat=3)
                        for vertex in bins.get(tuple(q+offset),[])]
            assert candidates, (label,point)
            distances=np.linalg.norm(native_world[candidates]-point,axis=1)
            best=float(distances.min()); ties=np.where(distances<=best+1e-12)[0]
            ambiguous+=len(ties)>1; chosen.append(candidates[int(ties[0])])
        map_ids=np.array(chosen)
        exported_ids=map_ids
    gap=np.linalg.norm(exported_world-native_world[map_ids],axis=1)
    original=native[label+'Weights'][map_ids][:,native_order]; original/=original.sum(1)[:,None]
    weight_gap=float(np.abs(original-dense).max()); assert gap.max()<2e-7 and weight_gap<2e-7
    arrays.update({label+'XYZ':xyz, label+'FileWorldXYZ':exported_world, label+'Triangles':triangles,
                   label+'NativeIDs':map_ids.astype('<i4'), label+'JointIndices':ids,
                   label+'NormalizedWeights':normalized,label+'RawWeights':weights,label+'MeshWorld':mw})
    report['parts'][label]={'nodeName':node.get('name'), 'exportRows':len(xyz),'uniqueNativeIDs':len(set(map_ids)),
                           'nativeVertices':len(native[label+'XYZ']),'triangles':len(triangles),
                           'nativeRestWorldMaxResidualM':float(gap.max()),'nativeMembershipMaxAbsResidual':weight_gap,
                           'rawWeightSumMaxResidual':float(np.abs(sums-1).max()),
                           'loaderNormalizationMaxAbsChange':float(np.abs(weights-normalized).max()),
                           'morphTargets':len(p.get('targets',[])),
                           'nativeOrientedTriangleAncestryExact':True if label=='renderedBody' else None}
    if label!='renderedBody': report['parts'][label]['nearestNativePointAmbiguousRows']=ambiguous
assert sha(source)==expected
np.savez_compressed(out/'export-fields.npz',**arrays);report['exportFieldsSHA256']=sha(out/'export-fields.npz')
(out/'export-inventory.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report['parts']),flush=True)
