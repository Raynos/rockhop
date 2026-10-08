"""Exact current GLB and captured live palettes, read-only bounded wrist audit."""
import hashlib, json, mmap, runpy, struct
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
SOURCE = ROOT/'harness/out/rider-rebuild/selected-complete-engine01/engine05/rider.glb'
CAPTURE = ROOT/'harness/out/rider-rebuild/selected-complete-engine01/garage09-wrist-current-triangles/report.json'
capture = json.loads(CAPTURE.read_text())['wristFragmentIdentity']
stream = SOURCE.open('rb'); data = mmap.mmap(stream.fileno(), 0, access=mmap.ACCESS_READ)
size = struct.unpack_from('<I', data, 12)[0]; doc = json.loads(data[20:20+size]); offset = 28+size
def accessor(index):
    row=doc['accessors'][index]; view=doc['bufferViews'][row['bufferView']]
    dtype=np.dtype({5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[row['componentType']])
    width={'VEC3':3,'VEC4':4,'SCALAR':1,'MAT4':16}[row['type']]
    return np.ndarray((row['count'],width),dtype=dtype,buffer=data,
        offset=offset+view.get('byteOffset',0)+row.get('byteOffset',0),
        strides=(view.get('byteStride',width*dtype.itemsize),dtype.itemsize))
def mesh(name):
    node=next(n for n in doc['nodes'] if n.get('name')==name)
    prim=doc['meshes'][node['mesh']]['primitives'][0]; attrs=prim['attributes']
    frame=next(f for f in capture['skinFrames'] if f['name']==name.replace('.',''))
    return {'v':accessor(attrs['POSITION']), 'f':accessor(prim['indices']).reshape(-1,3),
      'id':accessor(attrs['_NATIVE_ID']).ravel().astype(int),
      'j':accessor(attrs['JOINTS_0']).astype(int), 'w':accessor(attrs['WEIGHTS_0']), 'frame':frame}
def matrix(a): return np.asarray(a).reshape(4,4).T
def transform(v,m): return np.einsum('ij,kj->ik',np.asarray(v),m[:3,:3])+m[:3,3]
def skin(v,j,w,frame):
    bind=transform(v,matrix(frame['bindMatrix'])); result=np.zeros_like(bind,dtype=float)
    palette=np.asarray([matrix(b['skinMatrix']) for b in frame['bones']])
    for slot in range(4):
        mm=palette[j[:,slot]]
        result+=(np.einsum('nij,nj->ni',mm[:,:3,:3],bind)+mm[:,:3,3])*w[:,slot,None]
    return transform(result,matrix(frame['matrixWorld'])@matrix(frame['bindMatrixInverse']))
def skin_field(p,weights,frame):
    bound=transform(np.asarray([p]),matrix(frame['bindMatrix']))[0]; result=np.zeros(3)
    for j,w in weights.items(): result+=transform(np.asarray([bound]),matrix(frame['bones'][j]['skinMatrix']))[0]*w
    return transform(np.asarray([result]),matrix(frame['matrixWorld'])@matrix(frame['bindMatrixInverse']))[0]
closest=runpy.run_path(str(ROOT/'assets/blender/rider-rebuild/glove-anatomical04/audit_local04.py'))['closest']
controls=json.loads((ROOT/'assets/blender/rider-rebuild/glove-anatomical04/controls-orientation02.json').read_text())
frozen=json.loads((ROOT/'assets/blender/rider-rebuild/glove-anatomical04/guide-controls02.json').read_text())
dense=np.load(ROOT/controls['pins']['denseSelected']['path'])['vertices']
guide=np.load(ROOT/frozen['selectedGuide']['path'])['vertices']
native_rig=np.load(ROOT/controls['pins']['nativeArrays']['path']); joint_names=native_rig['jointNames'].tolist()
hood=mesh('RiderHoodie'); report={'acceptedArt':False,'capture':str(CAPTURE.relative_to(ROOT)),
 'captureSHA256':hashlib.sha256(CAPTURE.read_bytes()).hexdigest(),
 'sourceSHA256':hashlib.sha256(data).hexdigest(),'recipeSHA256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'hands':{}}
witness_ids=[120752,120746,119253,143964,144364,144043]
for side in ('R','L'):
    glove=mesh('ActualSelectedGlove.'+side)
    byid=np.zeros(len(dense),int); byid[glove['id']]=np.arange(len(glove['id']))
    indices=byid[witness_ids]; points=glove['v'][indices].astype(float)
    poses=skin(points,glove['j'][indices],glove['w'][indices],glove['frame'])
    # Wrist-local triangles only; a 100 mm rest neighborhood is far wider than any measured gap.
    center=points.mean(0); near=np.linalg.norm(hood['v']-center,axis=1)<.10
    face_numbers=np.flatnonzero(near[hood['f']].any(axis=1)); faces=hood['f'][face_numbers]
    used,inverse=np.unique(faces,return_inverse=True); local_faces=inverse.reshape(-1,3)
    hv=hood['v'][used].astype(float); hp=skin(hv,hood['j'][used],hood['w'][used],hood['frame'])
    rest_world=transform(hv,matrix(hood['frame']['matrixWorld']))
    valid=np.ones(len(local_faces),bool)
    for vertices in (rest_world,hp):
        tri=vertices[local_faces]
        valid &= np.linalg.norm(np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]),axis=1)>1e-14
    local_faces=local_faces[valid]; face_numbers=face_numbers[valid]
    point_rest_world=transform(points,matrix(glove['frame']['matrixWorld']))
    nearest_rest=closest(point_rest_world,rest_world,local_faces); nearest_pose=closest(poses,hp,local_faces)
    cuff_file=np.load(ROOT/f'assets/blender/rider-rebuild/glove-cuff-fit05/cuff-offsets-{side}.npz'); cuff=cuff_file['offsets']
    previous=np.load(ROOT/f'assets/blender/rider-rebuild/glove-anatomical04/local-offsets04-{side}.npz')['offsets']
    linear=np.asarray(controls['hands'][side]['initialPlacement']['linear'])
    wrist=native_rig['jointHeads'][joint_names.index('DEF-hand.'+side)]
    axis=native_rig['jointHeads'][joint_names.index('DEF-forearm.'+side)]-wrist; axis/=np.linalg.norm(axis)
    rows=[]
    for k,native in enumerate(witness_ids):
        gi=int(np.argmin(np.linalg.norm(guide-dense[native],axis=1))); rr=nearest_rest[k]; pp=nearest_pose[k]
        tri=local_faces[rr['face']]; a,b,c=rest_world[tri]
        q=np.asarray(rr['point']); vw=np.linalg.lstsq(np.stack([b-a,c-a],axis=1),q-a,rcond=None)[0]
        bary=[1-vw.sum(),*vw]; field={}
        for local,weight in zip(tri,bary):
            for j,w in zip(hood['j'][used[local]],hood['w'][used[local]]): field[int(j)]=field.get(int(j),0)+float(weight*w)
        point_in_hood=transform(point_rest_world[k:k+1],np.linalg.inv(matrix(hood['frame']['matrixWorld'])))[0]
        counter=skin_field(point_in_hood,field,hood['frame'])
        row={'nativeVertex':native,'glbVertex':int(indices[k]),'originalSelectedSource':dense[native].tolist(),
          'nearestOriginalGuideVertex':gi,'guideSourcePosition':guide[gi].tolist(),
          'cuff05GuideDeltaM':float(np.linalg.norm(linear@cuff[gi])),
          'previousAnatomical04GuideDeltaM':float(np.linalg.norm(linear@previous[gi])),
          'restGLB':points[k].tolist(),'posedWorld':poses[k].tolist(),
          'gloveWeights':[[glove['frame']['bones'][j]['name'],float(w)] for j,w in zip(glove['j'][indices[k]],glove['w'][indices[k]]) if w],
          'nearestHoodieRest':rr,'nearestHoodiePosed':pp,
          'hoodieRestSurfaceWeights':[[hood['frame']['bones'][j]['name'],float(w)] for j,w in field.items() if w>1e-9],
          'gloveVsHoodieFieldDisplacementM':float(np.linalg.norm(counter-poses[k])),
          'hoodieFieldCounterfactualWorld':counter.tolist()}
        if side=='R':
            actual=next(v for r in capture['rows'] for hit in r['hits'] if hit['mesh']=='ActualSelectedGloveR' for v in hit['vertices'] if v['nativeId']==native)
            row['liveCaptureReconstructionErrorM']=float(np.linalg.norm(poses[k]-actual['posedWorld']))
            assert row['liveCaptureReconstructionErrorM']<1e-8
        row['nearestHoodieRest']['globalFace']=int(face_numbers[rr['face']]); row['nearestHoodiePosed']['globalFace']=int(face_numbers[pp['face']])
        rows.append(row)
    guide_rows=[]
    translation=np.asarray(controls['hands'][side]['initialPlacement']['translation'])
    for gi in (3384,3593,3635,4118):
        p=np.einsum('ij,j->i',linear,cuff_file['corrected'][gi])+translation
        axial=float(np.dot(p-wrist,axis)); radial=p-wrist-axial*axis
        glb=p[[0,2,1]].copy(); glb[2]*=-1
        world=transform(np.asarray([glb]),matrix(glove['frame']['matrixWorld']))[0]
        rr=closest([world],rest_world,local_faces)[0]; tri=rest_world[local_faces[rr['face']]]
        normal=np.cross(tri[1]-tri[0],tri[2]-tri[0]); normal/=np.linalg.norm(normal)
        radial_glb=radial[[0,2,1]].copy(); radial_glb[2]*=-1
        radial_world=np.einsum('ij,j->i',matrix(glove['frame']['matrixWorld'])[:3,:3],radial_glb)
        projection=float(np.dot(radial_world,normal)); assert projection>.005
        fraction=max(0.,rr['signedNormalDistance']+.0015)/projection
        delta=-radial*fraction
        proposal=closest([world-radial_world*fraction],rest_world,local_faces)[0]
        rr['globalFace']=int(face_numbers[rr['face']]); proposal['globalFace']=int(face_numbers[proposal['face']])
        guide_rows.append({'guideVertex':gi,'sourcePosition':guide[gi].tolist(),'currentNativeXYZ':p.tolist(),
          'axialM':axial,'radialM':float(np.linalg.norm(radial)), 'nearestHoodieRest':rr,
          'radialNormalProjectionM':projection,'linearizedRadialContractionFraction':fraction,
          'linearizedNativeOffsetFor1p5mmInside':delta.tolist(),
          'linearizedSourceOffsetFor1p5mmInside':np.linalg.solve(linear,delta).tolist(),
          'proposalNearestHoodieRest':proposal,
          'priorAnatomical04OffsetExactlyZero':bool(np.all(previous[gi]==0))})
    report['hands'][side]={'hoodieLocalVertices':len(used),'hoodieLocalTriangles':len(faces),
      'witnesses':rows,'proposedGuideControls':guide_rows}
report['limits']=['Measured live right fragment plus corresponding left source IDs; not moving-art acceptance.',
 'Nearest normal signed distances are local crossings, not watertight containment.',
 'Counterfactual uses nearest rest sleeve field only to measure field contribution; it is not a weight-edit proposal.']
(HERE/'receipt.json').write_text(json.dumps(report,indent=2)+'\n')
for side, hand in report['hands'].items():
    print(side,[(r['nativeVertex'],r['nearestOriginalGuideVertex'],round(r['cuff05GuideDeltaM']*1000,3),
      round(r['nearestHoodieRest']['signedNormalDistance']*1000,3),round(r['nearestHoodiePosed']['signedNormalDistance']*1000,3),
      round(r['gloveVsHoodieFieldDisplacementM']*1000,3)) for r in hand['witnesses']])
