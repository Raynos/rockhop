"""Freeze one small cuff taper from actual selected sleeve measurements.

NumPy source preparation only: no Blender, fitting solver, rig or bind. The
geodesic brush contracts radial cuff extent around5713 through5187/4968;
the measured current hoodie plane sets its amount, never a global6mm offset.
"""
import hashlib
import heapq
import json
import mmap
import runpy
import struct
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
OLD = ROOT/'assets/blender/rider-rebuild/glove-anatomical04'


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        while block := stream.read(1024*1024): h.update(block)
    return h.hexdigest()


def pin(path):
    return {'path': str(path.relative_to(ROOT)), 'sha256': sha(path)}


def geodesic(points, faces, seeds, radius):
    edges = np.unique(np.sort(np.concatenate([faces[:, [0,1]], faces[:, [1,2]], faces[:, [2,0]]]), axis=1), axis=0)
    neighbors = [[] for _ in points]
    for a, b in edges:
        length = float(np.linalg.norm(points[a]-points[b])); neighbors[a].append((b, length)); neighbors[b].append((a, length))
    distances = np.full(len(points), np.inf); distances[seeds] = 0.; queue = [(0., seed) for seed in seeds]; heapq.heapify(queue)
    while queue:
        distance, index = heapq.heappop(queue)
        if distance != distances[index]: continue
        for other, length in neighbors[index]:
            candidate = distance+length
            if candidate <= radius and candidate < distances[other]:
                distances[other] = candidate; heapq.heappush(queue, (candidate, other))
    return distances


def main():
    assert not (HERE/'controls.json').exists(), 'Frozen controls already exist'
    source = ROOT/'harness/out/rider-rebuild/selected-complete-engine01/engine03/rider.glb'
    assert sha(source) == '7d826b835ca07c7c584d6b3a9606e9e89780f1c7b92e4030e1f1b58aff4127ed'
    frozen = json.loads((OLD/'guide-controls02.json').read_text())
    placement = json.loads((OLD/'controls-orientation02.json').read_text())
    original = np.load(ROOT/frozen['selectedGuide']['path'])['vertices']
    native = np.load(ROOT/placement['pins']['nativeArrays']['path']); names = native['jointNames'].tolist()
    closest = runpy.run_path(str(OLD/'audit_local04.py'))['closest']
    with source.open('rb') as stream, mmap.mmap(stream.fileno(), 0, access=mmap.ACCESS_READ) as raw:
        size = struct.unpack_from('<I', raw, 12)[0]; doc = json.loads(raw[20:20+size]); binary_start = 28+size
        node = next(n for n in doc['nodes'] if n.get('name') == 'RiderHoodie')
        assert not any(k in node for k in ('matrix','translation','rotation','scale'))
        primitives = doc['meshes'][node['mesh']]['primitives']; assert len(primitives) == 1
        primitive = primitives[0]
        def accessor(index):
            row = doc['accessors'][index]; view = doc['bufferViews'][row['bufferView']]
            dtype = np.dtype({5126:'<f4', 5125:'<u4', 5123:'<u2'}[row['componentType']])
            width = {'VEC3':3, 'SCALAR':1}[row['type']]
            return np.ndarray((row['count'],width), dtype=dtype, buffer=raw,
                offset=binary_start+view.get('byteOffset',0)+row.get('byteOffset',0),
                strides=(view.get('byteStride',width*dtype.itemsize),dtype.itemsize)).copy()
        hood = accessor(primitive['attributes']['POSITION'])[:, [0,2,1]]; hood[:,1] *= -1
        hood_faces = accessor(primitive['indices']).reshape(-1,3)
    result = {'acceptedArt':False, 'operation':'BILATERAL_LOCAL_PROXIMAL_CUFF_RADIAL_TAPER',
        'master':{'path':'harness/out/rider-rebuild/selected-complete-engine01/engine03/rider-private-masked.blend',
                  'sha256':'fdff3433c26c345d6f0555f196033f5ba76791d5d566b448991bd1fab2eff384'},
        'fullGloves':{'path':'harness/out/rider-rebuild/glove-anatomical04/local04/editable-selected-bilateral-gloves.blend',
                      'sha256':'fa21e40445bfb2dcd75789674adcea28ef7af7877d4ef74b22ac55bafc683d59'},
        'sourceGLB':pin(source), 'placement':pin(OLD/'controls-orientation02.json'),
        'guideHelpers':pin(OLD/'author_guide02.py'), 'fingerprintHelper':pin(ROOT/'assets/blender/rider-rebuild/head-neck-anatomical02/author-clothed-neck-motion.py'),
        'restHelper':pin(ROOT/'assets/blender/rider-rebuild/production-authoring01/assemble.py'),
        'sourceGuide':frozen['selectedGuide'], 'localControls':pin(OLD/'local-controls04.json'),
        'diagnosis':pin(ROOT/'docs/evidence/rider-rebuild/astra-glove-cuff07/receipt.json'),
        'seed':5713, 'ringControls':[5187,4968], 'falloffMeters':.025, 'sleeveEaseMeters':.0015,
        'axialTaperStartM':.018, 'axialTaperFullM':.030, 'hands':{}, 'freezeRecipeSHA256':sha(__file__),
        'limits':['Source brush only, no moving-art acceptance.','Local hoodie planes constrain amount; not watertight containment or body clearance fitting.']}
    for side in ('L','R'):
        local_path = OLD/f'local-offsets04-{side}.npz'; local = np.load(local_path); points = local['corrected'].copy(); faces = local['faces']
        linear = np.asarray(placement['hands'][side]['initialPlacement']['linear']); translation = np.asarray(placement['hands'][side]['initialPlacement']['translation'])
        world = points@linear.T+translation; wrist = native['jointHeads'][names.index('DEF-hand.'+side)]
        axis = native['jointHeads'][names.index('DEF-forearm.'+side)]-wrist; axis /= np.linalg.norm(axis)
        t = (world-wrist)@axis; radial = world-wrist-t[:,None]*axis; radius = np.linalg.norm(radial, axis=1)
        witnesses = [5713,5187,4968]
        distances = geodesic(world, faces, witnesses, result['falloffMeters'])
        x = np.clip(1-distances/result['falloffMeters'],0,1); brush = x*x*(3-2*x)
        x = np.clip((t-.018)/.012,0,1); brush *= x*x*(3-2*x); brush[original[:,1] >= -.52] = 0
        triangles = hood_faces[np.linalg.norm(hood[hood_faces].mean(1)-wrist,axis=1)<.12]
        tri = hood[triangles]; normals = np.cross(tri[:,1]-tri[:,0], tri[:,2]-tri[:,0]); valid = np.linalg.norm(normals,axis=1)>1e-14
        triangles = triangles[valid]; normals = normals[valid]; normals /= np.linalg.norm(normals,axis=1)[:,None]
        observations = closest(world[witnesses], hood, triangles); stations = []
        for index, observation in zip(witnesses, observations):
            normal = normals[observation['face']]; projection = float(radial[index]@normal)
            observation.update(guideVertex=index,world=world[index].tolist(),brushWeight=float(brush[index]),radialNormalProjectionM=projection)
            # Inside controls remain measurements, never force the whole lip to
            # follow a different closest face. Only exposed witnesses set depth.
            assert projection > .01 and brush[index] == 1.
            amount = max(0., observation['signedNormalDistance']+.0015)/projection
            assert 0 < amount <= .25
            stations.append((float(t[index]), amount))
        stations.sort(); fraction = np.full(len(points), stations[0][1])
        for (a, x), (b, y) in zip(stations, stations[1:]):
            q = np.clip((t-a)/(b-a),0,1); q = q*q*(3-2*q)
            mask = t >= a; fraction[mask] = x*(1-q[mask])+y*q[mask]
        offsets_world = -radial*(fraction*brush)[:,None]
        offsets_source = offsets_world@np.linalg.inv(linear).T; corrected = points+offsets_source
        changed = np.linalg.norm(offsets_world,axis=1)>0
        assert np.array_equal(corrected[~changed], points[~changed])
        assert not np.any(changed & (np.linalg.norm(local['offsets'],axis=1)>0)), 'Brush touches an existing local04 anatomical edit'
        crosses = np.linalg.norm(np.cross(corrected[faces[:,1]]-corrected[faces[:,0]],corrected[faces[:,2]]-corrected[faces[:,0]]),axis=1)
        assert crosses.min() > np.finfo(np.float32).eps
        output = HERE/f'cuff-offsets-{side}.npz'; np.savez_compressed(output, original=points, corrected=corrected, offsets=offsets_source, faces=faces)
        result['hands'][side] = {'offsets':pin(output), 'previousLocalOffsets':pin(local_path), 'axialTaperStations':stations,
            'changedGuideVertices':int(changed.sum()), 'maximumWorldOffsetM':float(np.linalg.norm(offsets_world,axis=1).max()),
            'existingLocal04EditedVerticesExactlyUntouched':True, 'minimumTriangleCrossSourceUnits':float(crosses.min()),
            'hoodieWitnessMeasurements':observations}
    (HERE/'controls.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({s:{k:v for k,v in r.items() if k not in ('offsets','previousLocalOffsets','hoodieWitnessMeasurements')} for s,r in result['hands'].items()},indent=2))


if __name__ == '__main__': main()
