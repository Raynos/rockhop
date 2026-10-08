"""One offline authored garment source-pose construction; no Blender, mesh fitting or search.

Actual selected sleeve section centers establish the source pose. Canonical75
upperarm/forearm/wrist landmarks establish the wearer pose. These authoring
controls freeze explicit editable authoring-bone frames, not a clearance claim.
"""
import hashlib
import json
import struct
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent

def pin(path):
    p = ROOT/path
    return {'path':path, 'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}

def smooth(a,b,x):
    t=np.clip((x-a)/(b-a),0,1)
    return t*t*(3-2*t)

def rotation(a,b):
    a=a/np.linalg.norm(a);b=b/np.linalg.norm(b)
    v=np.cross(a,b);c=float(a@b)
    k=np.array([[0,-v[2],v[1]],[v[2],0,-v[0]],[-v[1],v[0],0]])
    return np.eye(3)+k+k@k/(1+c)

def main():
    original='.tmp/generation-comparison-2026-10-03/user-agent2/qualified-hunyuan-paint06/paint/painted.glb'
    data=(ROOT/original).read_bytes();size=struct.unpack_from('<I',data,12)[0]
    gltf=json.loads(data[20:20+size]);offset=20+size
    accessor=gltf['accessors'][gltf['meshes'][0]['primitives'][0]['attributes']['POSITION']]
    view=gltf['bufferViews'][accessor['bufferView']]
    xyz=np.ndarray((accessor['count'],3),dtype='<f4',buffer=data,
        offset=offset+8+view.get('byteOffset',0)+accessor.get('byteOffset',0),
        strides=(view.get('byteStride',12),4))
    raw=xyz[:,[0,2,1]].astype(float);raw[:,1]*=-1
    scale=np.array([.52,.5,17/36]);translation=np.array([.007,0,1.2266666666666666])
    canonical='docs/evidence/rider-rebuild/native-hand-repair01/native02/native-body.npz'
    body=np.load(ROOT/canonical);names=list(body['jointNames']);heads=body['jointHeads']
    sections={};arms={};landmarks={}
    for side,sign in [('L',1),('R',-1)]:
        source=[];rows=[]
        for x in [.43,.68,.94]:
            subset=raw[(abs(raw[:,0]-sign*x)<.012)&(raw[:,2]>-.5)]
            lo=subset[:,1:].min(0);hi=subset[:,1:].max(0)
            center=np.r_[sign*x,(lo+hi)/2]
            source.append(center*scale+translation)
            rows.append({'rawX':sign*x,'bandHalfWidth':.012,'points':len(subset),
                         'rawYZMin':lo.tolist(),'rawYZMax':hi.tolist(),'rawCenter':center.tolist()})
        shoulder=heads[names.index('DEF-upper_arm.'+side)].astype(float)
        elbow=heads[names.index('DEF-forearm.'+side)].astype(float)
        wrist=heads[names.index('DEF-hand.'+side)].astype(float)
        # The source cap center is distal to its shoulder seam. Place it one
        # fifth down the canonical upper arm, with 15mm longitudinal cloth ease.
        cap=shoulder+.2*(elbow-shoulder)+np.array([0,0,.015])
        target=np.array([cap,elbow,wrist]);source=np.array(source)
        arms[side]={'source':source,'target':target}
        sections[side]=rows
        for role,i in [('deltoid',0),('upperArm',0),('elbow',1),('cuff',2)]:
            landmarks[role+'.'+side]={'source':source[i].tolist(),'target':target[i].tolist()}
        # These are surface-side editing handles. Their pose follows the same
        # cross-section rotation as the garment, never a constant-Y wall.
        for role,delta in [('frontArmhole',[0,-.075,0]),('rearArmhole',[0,.075,0]),
                           ('lowerAxilla',[-sign*.035,0,-.075])]:
            r=rotation(source[1]-source[0],target[1]-target[0])
            landmarks[role+'.'+side]={'source':(source[0]+delta).tolist(),
                'target':(target[0]+r@np.array(delta)).tolist()}
        landmarks['shoulderSlope.'+side]={'source':[sign*.15,0,1.51],
            'target':[sign*.15,0,1.49]}
    landmarks['neck']={'source':[0,0,1.56],'target':[0,0,1.56]}
    bones=[]
    bones.append({'name':'AUTHOR_Chest','parent':None,'sourceHead':[0,0,1.15],
                  'sourceTail':[0,0,1.48],'targetHead':[0,0,1.15],'targetTail':[0,0,1.48]})
    for side,sign in [('L',1),('R',-1)]:
        source=arms[side]['source'];target=arms[side]['target']
        bridge=np.array([sign*.14,0,1.49])
        chain=[('ShoulderBridge',bridge,source[0],bridge,target[0],'AUTHOR_Chest'),
               ('UpperArm',source[0],source[1],target[0],target[1],'AUTHOR_ShoulderBridge.'+side),
               ('Forearm',source[1],source[2],target[1],target[2],'AUTHOR_UpperArm.'+side)]
        for role,sh,st,th,tt,parent in chain:
            bones.append({'name':'AUTHOR_'+role+'.'+side,'parent':parent,
                'sourceHead':sh.tolist(),'sourceTail':st.tolist(),
                'targetHead':th.tolist(),'targetTail':tt.tolist()})
    controls={'accepted':False,'stage':'ONE_ACTUAL_SELECTED_SOURCE_GARMENT_ONLY_AUTHORING_RIG_TRANSPORT',
        'incomingNative':pin('harness/out/rider-rebuild/hoodie-shoulder-anatomical04/corrected04/selected-tailored-outfit.blend'),
        'incomingReceipt':pin('harness/out/rider-rebuild/hoodie-shoulder-anatomical04/corrected04/author.json'),
        'originalDensePBR':pin(original),'canonicalBodyArrays':pin(canonical),
        'originalSelectedCompact':pin('assets/blender/hero-remaster/rider/anatomical-foundation-2026-10-03/user-agent1/selected-hoodie25/crease-normal-candidate.blend'),
        'signatureHelper':pin('assets/blender/rider-rebuild/production-hoodie01/author.py'),
        'bodyRigSignature':'50ff787c680d754368deaca8efbbb488a23e50a932b47d49abc86fe587345bb2',
        'visibleOldHoodie':'Hoodie__RiderHoodie','body':'RiderBody','rig':'RiderSkeleton',
        'sourceVertices':716971,'sourcePolygons':921722,
        'gltfToBlenderRows':[[1,0,0],[0,0,-1],[0,1,0]],
        'sourceDisplayAffine':{'scale':scale.tolist(),'translation':translation.tolist()},
        'originalPBRHashes':['1eb934f396df30e3cd881211ff4e195c4460f8fa8db5bfa22ddb3b5ef28e5d09',
                             '2e598ae796f89acf741389a67635d4fa7b8d99f2ba39b0e46d0516c95db6dfae'],
        'sourceSleeveSections':sections,'landmarks':landmarks,
        'authoringBones':bones,
        'sourcePoseWeightControls':{'lateralTransition':[.12,.255], 'radialTransition':[.13,.25],
            'capCrossfadeHalfWidth':.035,'elbowCrossfadeHalfWidth':.045},
        'limits':['One frozen garment-only authoring armature pose, no outside/projection/patch/atlas/gain search.',
                  'Original mesh topology, UVs and packed original4K maps remain exact; object affine and one source-pose transport change positions.',
                  'Source has original interior surfaces; no new thickness or new interior is inferred.',
                  'Visible evaluated derivative is saved before field transfer; original selected surface plus temporary7-bone rig remains an editable hidden authoring aid, never a second final skeleton.',
                  '15mm cap longitudinal ease is an artist control, not proven clearance.',
                  'Static unrigged dense working context. Full native75 binding and neutral/reach/raised/return clip remain pending rest-fit judgment.',
                  'Current body/rest75 and every other visible garment remain untouched. AllR0–R5 open. No player export.']}
    (HERE/'controls.json').write_text(json.dumps(controls,indent=2)+'\n')

if __name__=='__main__':main()
