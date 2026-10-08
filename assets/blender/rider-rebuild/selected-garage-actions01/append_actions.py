"""Append rig-only animation data without rewriting any selected surface/image bytes."""
import copy
import hashlib
import json
import struct
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[4]


def sha(path):
    digest=hashlib.sha256()
    with Path(path).open('rb') as stream:
        while block:=stream.read(1024*1024): digest.update(block)
    return digest.hexdigest()


def pin(row):
    path=ROOT/row['path']; assert sha(path)==row['sha256'],('Changed source',row); return path


def glb(path):
    with Path(path).open('rb') as stream:
        magic,version,total=struct.unpack('<III',stream.read(12))
        assert magic==0x46546c67 and version==2 and total==Path(path).stat().st_size
        size,kind=struct.unpack('<II',stream.read(8)); assert kind==0x4e4f534a
        document=json.loads(stream.read(size))
        length,kind=struct.unpack('<II',stream.read(8)); assert kind==0x004e4942
        offset=stream.tell(); assert offset+length==total
    assert len(document['buffers'])==1 and 'uri' not in document['buffers'][0]
    assert 0<=length-document['buffers'][0]['byteLength']<=3
    return document,offset,length


def segment_sha(path,offset,length):
    digest=hashlib.sha256()
    with Path(path).open('rb') as stream:
        stream.seek(offset)
        while length:
            block=stream.read(min(length,1024*1024)); assert block
            digest.update(block); length-=len(block)
    return digest.hexdigest()


def accessor(document,binary,identity):
    row=document['accessors'][identity]; assert not row.get('sparse') and not row.get('normalized')
    view=document['bufferViews'][row['bufferView']]; assert view['buffer']==0
    assert row['componentType']==5126
    width={'SCALAR':1,'VEC3':3,'VEC4':4}[row['type']]
    return np.ndarray((row['count'],width),dtype='<f4',buffer=binary,
        offset=view.get('byteOffset',0)+row.get('byteOffset',0),
        strides=(view.get('byteStride',width*4),4)).astype(float)


def matrix(node):
    if 'matrix' in node:
        assert not any(key in node for key in ('translation','rotation','scale'))
        return np.asarray(node['matrix'],float).reshape(4,4).T
    x,y,z,w=node.get('rotation',[0,0,0,1]); assert abs(x*x+y*y+z*z+w*w-1)<2e-5
    rotation=np.asarray([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],
                         [2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],
                         [2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
    result=np.eye(4); result[:3,:3]=rotation*np.asarray(node.get('scale',[1,1,1]))
    result[:3,3]=node.get('translation',[0,0,0]); return result


def parents(document):
    result={}
    for index,node in enumerate(document['nodes']):
        for child in node.get('children',[]): assert child not in result; result[child]=index
    return result


def append(config,config_path,out,rig_report):
    source=pin(config['sourceGLB']); base,base_offset,base_length=glb(source)
    rig_path=out/'rig-actions.glb'; small,small_offset,small_length=glb(rig_path)
    with rig_path.open('rb') as stream: stream.seek(small_offset); animation_bytes=stream.read(small_length)
    assert not base.get('animations') and len(base['skins'])==1 and len(base['skins'][0]['joints'])==75
    assert not any(small.get(key) for key in ('meshes','materials','images','skins','textures'))
    assert not small.get('extensionsRequired'), 'Unreviewed animation extension'
    names={node['name']:index for index,node in enumerate(base['nodes'])}
    small_names={node['name']:index for index,node in enumerate(small['nodes'])}
    assert len(names)==len(base['nodes']) and len(small_names)==len(small['nodes'])
    joint_names={base['nodes'][index]['name'] for index in base['skins'][0]['joints']}
    contract=json.loads(pin(config['contract']).read_text())
    assert joint_names=={bone['name'] for bone in contract['nativeRest']['bones']}
    assert set(small_names)==joint_names|{'RiderSkeleton'}
    base_parents,small_parents=parents(base),parents(small)
    maximum_rest_residual=0.
    for name,index in small_names.items():
        target=names[name]
        parent_name=small['nodes'][small_parents[index]]['name'] if index in small_parents else None
        target_parent=base['nodes'][base_parents[target]]['name'] if target in base_parents else None
        assert parent_name==target_parent,('Rest hierarchy differs',name,parent_name,target_parent)
        error=float(np.max(abs(matrix(small['nodes'][index])-matrix(base['nodes'][target]))))
        maximum_rest_residual=max(maximum_rest_residual,error)
        assert error<2e-6,('Serialized rest differs',name,error)
    expected=np.load(out/'native-action-matrices.npz'); bone_names=expected['boneNames'].tolist()
    actions_by_name={row['name']:row for row in config['actions']}
    assert {row['name'] for row in small['animations']}==set(actions_by_name)
    assert len(small['animations'])==len(actions_by_name)==2
    animation_readback=[]
    for action in small['animations']:
        specification=actions_by_name[action['name']]
        count=specification['frameRange'][1]-specification['frameRange'][0]+1
        samples={}; visited=set()
        for channel in action['channels']:
            assert set(channel['target'])=={'node','path'} and not channel.get('extensions')
            name=small['nodes'][channel['target']['node']]['name']; path=channel['target']['path']
            assert name in joint_names and path in {'translation','rotation','scale'}
            assert (name,path) not in visited; visited.add((name,path))
            sampler=action['samplers'][channel['sampler']]; assert sampler.get('interpolation','LINEAR')=='LINEAR'
            times=accessor(small,animation_bytes,sampler['input']).reshape(-1)
            values=accessor(small,animation_bytes,sampler['output'])
            assert len(times)==len(values)==count and np.isfinite(values).all()
            assert np.max(abs(times-np.arange(count)/24))<5e-7
            samples[name,path]=values
        assert visited=={(name,path) for name in joint_names for path in ('translation','rotation','scale')}
        action_index=next(index for index,row in enumerate(config['actions']) if row['name']==action['name'])
        wanted=expected[f'pose{action_index}']; assert wanted.shape==(count,75,4,4)
        maximum_pose_residual=0.
        for frame in range(count):
            cache={}
            def world(index):
                if index in cache: return cache[index]
                node=small['nodes'][index]; name=node['name']
                if name in joint_names:
                    local=matrix({path:samples[name,path][frame] for path in ('translation','rotation','scale')})
                else: local=matrix(node)
                cache[index]=world(small_parents[index])@local if index in small_parents else local
                return cache[index]
            actual=np.asarray([world(small_names[name]) for name in bone_names])
            error=float(np.max(abs(actual-wanted[frame])))
            maximum_pose_residual=max(maximum_pose_residual,error)
        assert maximum_pose_residual<2e-5,('Decoded action differs from exact native matrices',action['name'],maximum_pose_residual)
        animation_readback.append({'name':action['name'],'fps':24,'frameRange':specification['frameRange'],
            'sampleCountPerChannel':count,'channels':len(visited),'startSeconds':0,'durationSeconds':(count-1)/24,
            'maximumDecodedNativeWorldMatrixResidual':maximum_pose_residual,'sourceSlot':specification['slot']})
    merged=copy.deepcopy(base); view_start=len(base['bufferViews']); accessor_start=len(base['accessors'])
    for view in small['bufferViews']:
        assert view['buffer']==0 and not view.get('extensions')
        copied=copy.deepcopy(view); copied['byteOffset']=base_length+view.get('byteOffset',0)
        merged['bufferViews'].append(copied)
    for row in small['accessors']:
        assert 'bufferView' in row and not row.get('sparse')
        copied=copy.deepcopy(row); copied['bufferView']+=view_start; merged['accessors'].append(copied)
    merged['animations']=copy.deepcopy(small['animations'])
    for action in merged['animations']:
        for sampler in action['samplers']: sampler['input']+=accessor_start; sampler['output']+=accessor_start
        for channel in action['channels']:
            original=channel['target']['node']; channel['target']['node']=names[small['nodes'][original]['name']]
    merged['buffers'][0]['byteLength']=base_length+small_length
    for key,value in base.items():
        if key in {'buffers','bufferViews','accessors','animations'}: continue
        assert merged[key]==value,('Original selected JSON changed',key)
    assert merged['bufferViews'][:view_start]==base['bufferViews']
    assert merged['accessors'][:accessor_start]==base['accessors']
    encoded=json.dumps(merged,separators=(',',':')).encode(); encoded+=b' '*((-len(encoded))%4)
    total=12+8+len(encoded)+8+base_length+small_length
    output=out/'rider.glb'
    with output.open('xb') as destination,source.open('rb') as original:
        destination.write(struct.pack('<III',0x46546c67,2,total))
        destination.write(struct.pack('<II',len(encoded),0x4e4f534a)); destination.write(encoded)
        destination.write(struct.pack('<II',base_length+small_length,0x004e4942))
        original.seek(base_offset); remaining=base_length
        while remaining:
            block=original.read(min(1024*1024,remaining)); assert block
            destination.write(block); remaining-=len(block)
        destination.write(animation_bytes)
    readback,new_offset,new_length=glb(output)
    assert readback==merged and new_length==base_length+small_length
    source_binary_sha=segment_sha(source,base_offset,base_length)
    assert segment_sha(output,new_offset,base_length)==source_binary_sha
    assert segment_sha(output,new_offset+base_length,small_length)==hashlib.sha256(animation_bytes).hexdigest()
    new_sha=sha(output); new_contract=copy.deepcopy(contract)
    assert new_contract['glbSHA256']==config['sourceGLB']['sha256']
    new_contract['glbSHA256']=new_sha; new_contract['sourceSHA256']=new_sha
    new_contract['genericActions']={row['name']:row for row in animation_readback}
    new_contract['qualificationState']['movingArt']='PARENT_ACTUAL_GARAGE_ACTION_REVIEW_PENDING'
    calibration=json.loads(pin(config['calibration']).read_text())
    assert calibration['sourceSHA256']==config['sourceGLB']['sha256']
    new_calibration=copy.deepcopy(calibration); new_calibration['sourceSHA256']=new_sha
    assert {k:v for k,v in new_calibration.items() if k!='sourceSHA256'}=={k:v for k,v in calibration.items() if k!='sourceSHA256'}
    contract_path=out/'rider-contract.json'; calibration_path=out/'pose-calibration.json'
    contract_path.write_text(json.dumps(new_contract,indent=2)+'\n')
    calibration_path.write_text(json.dumps(new_calibration,indent=2)+'\n')
    report={'accepted':False,'status':'SAME_SELECTED_RIDER_ORIGINAL_NATIVE_ACTION_TRANSPORT_REVIEW_PENDING',
        'source':config['sourceGLB'],'glb':{'path':str(output.relative_to(ROOT)),'sha256':new_sha},
        'contract':{'path':str(contract_path.relative_to(ROOT)),'sha256':sha(contract_path)},
        'calibration':{'path':str(calibration_path.relative_to(ROOT)),'sha256':sha(calibration_path)},
        'editableNative':rig_report['native'],'recipeSHA256':sha(__file__),'inputSHA256':sha(config_path),
        'originalBINByteLength':base_length,'originalBINPayloadSHA256':source_binary_sha,
        'originalAllGeometryImageAndSkinBytesExact':True,'originalNodesMeshesImagesMaterialsTexturesSkinsExact':True,
        'originalAccessorAndBufferViewPrefixExact':True,'rigHierarchyNamesExact':True,
        'maximumSerializedLocalRestMatrixResidual':maximum_rest_residual,'actions':animation_readback,
        'newAnimationBINByteLength':small_length,'normalPlayerAssetsChanged':False,
        'limits':['Complete actual Garage/action playback, moving source-GPU parity, contacts and device gates remain open.',
                  'Only original145/193 authored action transport; no new action, geometry, textures, weights, mask or solver change.',
                  'Calibration semantics copied exactly; source SHA rebound because original complete geometry/rest bytes are unchanged.']}
    (out/'export.json').write_text(json.dumps(report,indent=2)+'\n')
