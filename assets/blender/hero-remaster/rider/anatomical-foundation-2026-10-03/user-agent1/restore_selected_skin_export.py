"""Audit/restore actual native garment memberships through the exporter cutoff.

Change only already allocated JOINTS/WEIGHTS bytes; all nonskin bytes exact.
"""
import argparse,hashlib,json,struct,sys
from pathlib import Path
import numpy as np
from mathutils import Vector
from mathutils.kdtree import KDTree
ap=argparse.ArgumentParser(description=__doc__)
for k in ['input','field','baseline','out','evidence']:ap.add_argument('--'+k,required=True)
a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);input_path,field_path,baseline,out,evidence=[Path(getattr(a,k)).resolve() for k in ['input','field','baseline','out','evidence']]
assert not out.exists(),'Preserve frozen skin derivative'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(path):
    raw=bytearray(path.read_bytes());n=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+n]);return raw,doc,28+n
def offset(doc,start,accessor,row,k):
    v=doc['bufferViews'][accessor['bufferView']];size={5121:1,5123:2,5125:4,5126:4}[accessor['componentType']];components={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}[accessor['type']]
    return start+v.get('byteOffset',0)+accessor.get('byteOffset',0)+row*v.get('byteStride',size*components)+k*size
def read(raw,doc,start,id):
    accessor=doc['accessors'][id];components={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}[accessor['type']];fmt={5121:'B',5123:'H',5125:'I',5126:'f'}[accessor['componentType']]
    return np.array([[struct.unpack_from('<'+fmt,raw,offset(doc,start,accessor,row,k))[0] for k in range(components)] for row in range(accessor['count'])])
raw,doc,start=load(input_path);before=bytes(raw);base,bd,bs=load(baseline)
assert len(doc['meshes'])==len(doc['skins'])==1 and len(doc['meshes'][0]['primitives'])==1
names=[doc['nodes'][i]['name'] for i in doc['skins'][0]['joints']];oldnames=[bd['nodes'][i]['name'] for i in bd['skins'][0]['joints']]
assert len(names)==51 and names==oldnames,'Original51joint names/order must remain exact'
bind=read(raw,doc,start,doc['skins'][0]['inverseBindMatrices']);oldbind=read(base,bd,bs,bd['skins'][0]['inverseBindMatrices'])
binderror=float(np.abs(bind-oldbind).max());assert binderror<3e-6,binderror
data=np.load(field_path);native=data['nativeRestXYZ'];weights=data['weights'];native_names=data['boneNames'].tolist()
assert set(native_names)==set(names) and weights.shape==(6046,51)
expected=np.column_stack([native[:,0],native[:,2],-native[:,1]])
kd=KDTree(len(expected))
for i,p in enumerate(expected):kd.insert(Vector(p),i)
kd.balance();primitive=doc['meshes'][0]['primitives'][0];attrs=primitive['attributes'];positions=read(raw,doc,start,attrs['POSITION'])
for slot in [0,1]:assert 'JOINTS_'+str(slot) in attrs and 'WEIGHTS_'+str(slot) in attrs
mapping=[];errors=[];raw_weight_error=0.;allowed=set()
for row,p in enumerate(positions):
    # Installed skinned exporter bakes the same+.65 file frame into bind-space
    # POSITION, unlike unskinned source13's node translation. Original51IBMs
    # are checked above; center this file translation exactly once for ancestry.
    centered=p-np.array([.65,0.,0.])
    q,i,error=kd.find(Vector(centered));assert error<2e-6,(row,error);mapping.append(i);errors.append(float(error))
    actual=np.zeros(51)
    for slot in [0,1]:
        ja=doc['accessors'][attrs['JOINTS_'+str(slot)]];wa=doc['accessors'][attrs['WEIGHTS_'+str(slot)]]
        for k in range(4):
            jf={5121:'B',5123:'H'}[ja['componentType']];joint=struct.unpack_from('<'+jf,raw,offset(doc,start,ja,row,k))[0];value=struct.unpack_from('<f',raw,offset(doc,start,wa,row,k))[0]
            actual[native_names.index(names[joint])]+=value
    raw_weight_error=max(raw_weight_error,float(np.abs(actual-weights[i]).max()))
    pairs=sorted([(n,float(w)) for n,w in zip(native_names,weights[i]) if w>0],key=lambda x:(-x[1],names.index(x[0])))
    assert len(pairs)<=8
    for k in range(8):
        slot,index=k//4,k%4;ja=doc['accessors'][attrs['JOINTS_'+str(slot)]];wa=doc['accessors'][attrs['WEIGHTS_'+str(slot)]]
        jo=offset(doc,start,ja,row,index);wo=offset(doc,start,wa,row,index);jf={5121:'B',5123:'H'}[ja['componentType']]
        j=names.index(pairs[k][0]) if k<len(pairs) else 0;w=pairs[k][1] if k<len(pairs) else 0.
        struct.pack_into('<'+jf,raw,jo,j);struct.pack_into('<f',raw,wo,w)
        allowed.update(range(jo,jo+struct.calcsize(jf)));allowed.update(range(wo,wo+4))
changes=[i for i,(x,y) in enumerate(zip(before,raw)) if x!=y];assert all(i in allowed for i in changes)
error=0.
for row,i in enumerate(mapping):
    decoded=np.zeros(51,dtype=np.float32)
    for slot in [0,1]:
        ja=doc['accessors'][attrs['JOINTS_'+str(slot)]];wa=doc['accessors'][attrs['WEIGHTS_'+str(slot)]]
        for k in range(4):
            joint=struct.unpack_from('<'+{5121:'B',5123:'H'}[ja['componentType']],raw,offset(doc,start,ja,row,k))[0]
            w=struct.unpack_from('<f',raw,offset(doc,start,wa,row,k))[0];decoded[native_names.index(names[joint])]+=w
    error=max(error,float(np.abs(decoded-weights[i]).max()))
assert error==0.
out.write_bytes(raw)
report={'status':'UNACCEPTED exact native garment skin restored; native moving/actual engine qualification pending',
        'pins':{str(p):sha(p) for p in [input_path,field_path,baseline]},'recipeSHA256':sha(__file__),'outputSHA256':sha(out),
        'renderRows':len(mapping),'nativeVertices':len(native),'rawWeightMaximumError':raw_weight_error,'restoredWeightMaximumError':error,
        'rawPositionVsNativeMaximumErrorM':max(errors),'rawCoordinateMapping':'Skinned bind-space POSITION=(nativeX+.65,nativeZ,-nativeY); file translation centered once for ancestry.51IBMs remain original baseline.',
        'original51JointNamesAndOrderExact':True,'originalInverseBindMaximumFloatError':binderror,
        'changedSkinBytes':len(changes),'allNonSkinBytesExact':True,'nativeInfluenceMaximum':int((weights>0).sum(1).max()),
        'mapping':mapping,'limits':['Raw glTF cutoff restored without changing positions/normals/UV/indices/images/materials/skin hierarchy/inversebind/document bytes.',
                  'Original51bind names/order checked against frozen constructed09GLB; inversebind numeric error explicit, not hidden.',
                  'Native weights are an authored candidate, not evidence of moving wearing/game/collision/mobile. Root alone judges allM0-M5, no normal-player/Library promotion.']}
evidence.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ['rawWeightMaximumError','restoredWeightMaximumError','rawPositionVsNativeMaximumErrorM','originalInverseBindMaximumFloatError','changedSkinBytes','outputSHA256']}),flush=True)
