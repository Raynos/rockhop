"""Read-only atlas/geodesic shape correspondence; never use old skin weights."""
from pathlib import Path
import hashlib, io, json, struct
import numpy as np
from PIL import Image

repo = Path('/Users/raynos/projects/games/rockhop')
root = Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2')
run = root / 'garment-rebuild01/silhouette02'
out = repo / 'docs/evidence/hero-remaster/one-rider-v2/garment-rebuild01/silhouette02'
run.mkdir(exist_ok=True); out.mkdir(exist_ok=True)
source = root / 'rig-adapter01/body-bind34/rider.glb'
raw = source.read_bytes(); length = struct.unpack_from('<I', raw, 12)[0]
doc = json.loads(raw[20:20+length]); binary = raw[28+length:]
def acc(index):
    a = doc['accessors'][index]; view = doc['bufferViews'][a['bufferView']]
    width = {'SCALAR':1, 'VEC2':2, 'VEC3':3, 'VEC4':4}[a['type']]
    dtype = {5126:'<f4', 5125:'<u4', 5123:'<u2', 5121:'u1'}[a['componentType']]
    assert 'byteStride' not in view and 'sparse' not in a
    return np.frombuffer(binary, dtype=dtype, count=a['count']*width,
                         offset=view.get('byteOffset',0)+a.get('byteOffset',0)).reshape(a['count'],width)
p = doc['meshes'][0]['primitives'][0]
P = acc(p['attributes']['POSITION']); T = acc(p['indices']).reshape(-1,3)
N = acc(p['attributes']['NORMAL']); UV = acc(p['attributes']['TEXCOORD_0'])
material = doc['materials'][p['material']]['pbrMetallicRoughness']
imageIndex = doc['textures'][material['baseColorTexture']['index']]['source']
view = doc['bufferViews'][doc['images'][imageIndex]['bufferView']]
image = Image.open(io.BytesIO(binary[view['byteOffset']:view['byteOffset']+view['byteLength']])).convert('RGB')
uv = UV[T].mean(1)
pixels = np.array(image)[np.clip((uv[:,1]*image.height).astype(int),0,image.height-1),
                         np.clip((uv[:,0]*image.width).astype(int),0,image.width-1)].astype(float)
centers = P[T].mean(1)
# Atlas is a semantic clue with explicit height guards, not a geometric fix.
shirt = (pixels[:,0]>pixels[:,2]+25) & (pixels[:,0]>pixels[:,1]+12) & (centers[:,1]>.82)
jeans = (pixels[:,2]>pixels[:,0]+10) & (pixels[:,1]>pixels[:,0]+3) & (centers[:,1]>.18) & (centers[:,1]<1.03)
branch = np.load(root/'rig-adapter01/body-bind32/branch-fields.npz')
assert np.array_equal(branch['source'][branch['inverse']], P)
assert np.array_equal(branch['triangles'],branch['inverse'][T])
left = branch['L_distanceArm'] < branch['L_distanceTorso']
right = branch['R_distanceArm'] < branch['R_distanceTorso']
physicalTriangles = branch['triangles']
leftTriangles = left[physicalTriangles].any(1)
rightTriangles = right[physicalTriangles].any(1)
scopes = {'shirtTorso':shirt & ~leftTriangles & ~rightTriangles,
          'shirtL':shirt & leftTriangles, 'shirtR':shirt & rightTriangles,
          'jeans':jeans}
assert not left[physicalTriangles[[6340,6403,27413,27805]]].any()
assert not right[physicalTriangles[[6340,6403,27413,27805]]].any()
normals = np.cross(P[T[:,1]]-P[T[:,0]],P[T[:,2]]-P[T[:,0]])
dots = np.einsum('ij,ij->i',normals,N[T].mean(1))
assert np.count_nonzero(dots>0)>len(T)*.95
target = run/'source-target.npz'; assert not target.exists()
np.savez_compressed(target, positions=P, triangles=T, normals=N,
                    centroidRGB=pixels, **scopes)
report = {'sourceSHA256':hashlib.sha256(raw).hexdigest(),
          'targetSHA256':hashlib.sha256(target.read_bytes()).hexdigest(),
          'sourceVertices':len(P),'sourceTriangles':len(T),
          'scopes':{k:int(v.sum()) for k,v in scopes.items()},
          'textureSize':list(image.size),'textureFlipY':False,
          'method':'Raw GLTF atlas centroid RGB plus preserved source32 explicit-landmark geodesic branches. No source skin-weight eligibility.',
          'settings':{'shirt':'R>B+25, R>G+12, Y>.82',
                      'jeans':'B>R+10, G>R+3, .18<Y<1.03',
                      'arm':'Reviewed32 surface arm distance<torso distance, no old Y cutoff; any triangle corner in branch'},
          'limits':['Masks guide one bounded clean-topology shape fit; not complete material semantics or sewn boundaries.',
                    'Full source high-detail geometry and protected head/hood/gloves/shoes remain untouched.']}
assert source.read_bytes()==raw
(out/'target-report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
