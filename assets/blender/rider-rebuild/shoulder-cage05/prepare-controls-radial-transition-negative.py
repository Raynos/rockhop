"""One offline authored cage construction; no Blender, mesh fitting or search.

Actual selected sleeve section centers establish the source pose. Canonical75
upperarm/forearm/wrist landmarks establish the wearer pose. These authoring
controls produce explicit editable lattice coordinates, not a clearance claim.
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
    low=np.array([-.58,-.23,.78]);high=np.array([.58,.23,1.68]);counts=[17,5,13]
    points=[];groups={name:[] for name in landmarks}
    for w,z in enumerate(np.linspace(low[2],high[2],counts[2])):
        for v,y in enumerate(np.linspace(low[1],high[1],counts[1])):
            for u,x in enumerate(np.linspace(low[0],high[0],counts[0])):
                p=np.array([x,y,z]);q=p.copy();side='L' if x>=0 else 'R'
                s=arms[side]['source'];t=arms[side]['target'];candidates=[]
                for i in range(2):
                    d=s[i+1]-s[i];parameter=np.clip((p-s[i])@d/(d@d),0,1)
                    distance=np.linalg.norm(p-(s[i]+parameter*d))
                    r=rotation(d,t[i+1]-t[i]);along=(p-s[i])@d/(d@d)
                    # Preserve rounded cross sections; scale only the sleeve
                    # axis to its canonical rest-pose length.
                    perpendicular=p-s[i]-along*d
                    mapped=t[i]+along*(t[i+1]-t[i])+r@perpendicular
                    candidates.append((distance,mapped,parameter))
                # A smooth elbow transition, one fixed pose, no pointwise solve.
                upper_axis=s[1]-s[0]
                elbow_parameter=(p-s[1])@upper_axis/(upper_axis@upper_axis)
                lower_weight=smooth(-.22,.22,elbow_parameter)
                posed=(1-lower_weight)*candidates[0][1]+lower_weight*candidates[1][1]
                distance=min(c[0] for c in candidates)
                weight=smooth(.13,.265,abs(x))*(1-smooth(.12,.23,distance))
                q+=weight*(posed-p)
                # Neck remains fixed; broad original shoulder slope lowers20mm.
                slope=smooth(.055,.15,abs(x))*(1-smooth(.20,.29,abs(x)))
                slope*=smooth(1.39,1.49,z)*(1-smooth(1.54,1.62,z))
                q[2]-=.020*slope*(1-weight)
                i=len(points)
                points.append({'index':i,'uvw':[u,v,w],'sourceWorld':p.tolist(),
                               'deformedWorld':q.tolist(),'sleevePoseWeight':float(weight)})
                for name,handle in landmarks.items():
                    if np.linalg.norm((p-np.array(handle['source']))/np.array([.12,.14,.12]))<1.4:
                        groups[name].append(i)
    controls={'accepted':False,'stage':'ONE_ACTUAL_SELECTED_SOURCE_EDITABLE_CAGE_REST_CONTEXT',
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
        'lattice':{'counts':counts,'interpolation':'KEY_BSPLINE','worldMin':low.tolist(),
                   'worldMax':high.tolist(),'points':points,'namedControlPointGroups':groups},
        'limits':['One frozen editable cage pose, no outside/projection/patch/atlas/gain search.',
                  'Original mesh topology, UVs and packed original4K maps remain exact; only object affine and cage deform appearance.',
                  'Source has original interior surfaces; no new thickness or new interior is inferred.',
                  '15mm cap longitudinal ease and20mm shoulder slope are artist controls, not proven clearance.',
                  'Static unrigged dense working context. Full native75 binding and neutral/reach/raised/return clip remain pending rest-fit judgment.',
                  'Current body/rest75 and every other visible garment remain untouched. AllR0–R5 open. No player export.']}
    (HERE/'controls.json').write_text(json.dumps(controls,indent=2)+'\n')

if __name__=='__main__':main()
