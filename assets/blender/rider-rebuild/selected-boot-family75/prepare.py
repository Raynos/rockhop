"""CPU-only genuine L/R source ancestry and native02 foot evidence."""
import hashlib
import json
from pathlib import Path
import struct
import sys
import numpy as np

ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'assets/blender/rider-rebuild/selected-boot-native70'))
import intake
PRODUCTION=ROOT/'harness/out/rider-rebuild/selected-boot-native70/native01/production.json'
PRODUCTION_SHA='518fe4ce2f7da86adc176c45d3d3393f70d1b1a4daaae0701ff245baa2681465'
NATIVE=PRODUCTION.with_name('UNACCEPTED-selected-production-full.blend')
NATIVE_SHA='ffac10be163895d2ecb76d6552c9e357b86122d522543b7117974884be0ea52c'
BODY=ROOT/'docs/evidence/rider-rebuild/native-hand-repair01/native02/native-body.npz'
BODY_SHA='e62e9969503b7761e99463eccc3ca7be39e0c230a2948f2f87a224db52d0f9a2'


def cyclic(f):return np.take_along_axis(f,(np.argmin(f,axis=1)[:,None]+np.arange(3))%3,axis=1)


def source_arrays():
    intake.pin(PRODUCTION,PRODUCTION_SHA);intake.pin(NATIVE,NATIVE_SHA)
    witness=json.loads(PRODUCTION.read_text())['sourceWitness'];wanted={}
    for name,row in witness['sources'].items():
        for key,length in [('positionSHA256',row['vertices']*12),('loopVertexSHA256',row['polygons']*12)]:
            wanted[(length,row[key])]=(name[-1],key)
    found={};blocks=[]
    # Blender's installed primary implementation: scripts/modules/_blendfile_header.py,
    # BlendFileHeader format1 LargeBHead8: 17-byte header, <4siQqq block headers.
    # This reader admits only the exact pinned native70, and identifies arrays by
    # the saved witness's entire byte SHA, never by guessed offsets or object names.
    with NATIVE.open('rb') as stream:
        assert stream.read(17)==b'BLENDER17-01v0502'
        while True:
            code,dna,address,size,count=struct.unpack('<4siQqq',stream.read(32))
            assert size>=0 and stream.tell()+size<=NATIVE.stat().st_size
            if code==b'ENDB':break
            offset=stream.tell()
            if size not in {length for length,digest in wanted}:stream.seek(size,1);continue
            raw=stream.read(size);key=wanted.get((size,hashlib.sha256(raw).hexdigest()))
            if key is None:continue
            assert key not in found and code==b'DATA'
            found[key]=np.frombuffer(raw,dtype='<f4' if key[1]=='positionSHA256' else '<i4').reshape(-1,3)
            blocks.append({'side':key[0],'field':key[1],'offset':offset,'bytes':size,'sha256':hashlib.sha256(raw).hexdigest()})
    assert set(found)==set(wanted.values())
    return {side:{'positions':found[side,'positionSHA256'],'triangles':found[side,'loopVertexSHA256']} for side in ('L','R')},blocks


def normals(p,f):
    p=p.astype(float);tri=p[f];n=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);length=np.linalg.norm(n,axis=1)
    assert (length>0).all();n/=length[:,None];total=np.zeros_like(p)
    for corner in range(3):
        a=tri[:,(corner+1)%3]-tri[:,corner];b=tri[:,(corner+2)%3]-tri[:,corner]
        angle=np.arctan2(np.linalg.norm(np.cross(a,b),axis=1),np.einsum('ij,ij->i',a,b))
        np.add.at(total,f[:,corner],n*angle[:,None])
    length=np.linalg.norm(total,axis=1);assert (length>0).all()
    return (total/length[:,None]).astype('<f4')


def package(path,arrays):
    layout={};offset=0
    with path.open('wb') as stream:
        for key,array in arrays.items():
            array=np.ascontiguousarray(array);raw=array.tobytes();stream.write(raw)
            layout[key]={'dtype':array.dtype.str,'shape':list(array.shape),'byteOffset':offset,'byteLength':len(raw)};offset+=len(raw)
    return dict(intake.pin(path,intake.sha(path)),layout=layout)


def main():
    assert len(sys.argv)==2;out=Path(sys.argv[1]).resolve()
    assert out.is_relative_to(ROOT/'harness/out/rider-rebuild/selected-boot-family75') and not out.exists();out.mkdir(parents=True)
    meshes,blocks=source_arrays();intake.pin(BODY,BODY_SHA);body=dict(np.load(BODY))
    intake.pin(intake.RECEIPT,intake.RECEIPT_SHA);constructor=json.loads(intake.RECEIPT.read_text())
    left_source=intake.arrays(constructor['sourceArrayPackage']);candidate=intake.arrays(constructor['candidate'])
    assert np.array_equal(meshes['L']['positions'].ravel(),left_source['positions'])
    assert np.array_equal(meshes['L']['triangles'].ravel(),left_source['triangles'])
    assert np.array_equal(cyclic(meshes['L']['triangles'][:,::-1]),cyclic(meshes['R']['triangles']))
    original=candidate['originalVertexIds'];left_faces=original[candidate['triangles'].reshape(-1,3)];right_faces=left_faces[:,[0,2,1]]
    reflected=meshes['L']['positions'].astype(float)*[-1,1,1];delta=np.linalg.norm(reflected-meshes['R']['positions'],axis=1)
    feet={};foot_ids={};names=body['jointNames'].tolist()
    for side in ('L','R'):
        foot_ids[side]=np.flatnonzero(body['nativeCoefficients'][:,[names.index('DEF-foot.'+side),names.index('DEF-toe.'+side)]].sum(1)>.25).astype('<i4')
        feet[side]=body['vertices'][foot_ids[side]]
    foot_delta=np.sqrt(((feet['L'].astype(float)[:,None]*[-1,1,1]-feet['R'][None])**2).sum(2).min(1))
    arrays={}
    for side,indices in [('L',left_faces),('R',right_faces)]:
        arrays.update({side+'Positions':meshes[side]['positions'],side+'Triangles':meshes[side]['triangles'],
            side+'Normals':normals(meshes[side]['positions'],meshes[side]['triangles']),side+'CandidateOriginalTriangles':indices.astype('<u4'),
            side+'FootPoints':feet[side],side+'FootOriginalIds':foot_ids[side]})
    report={'status':'ACTUAL_BILATERAL_SOURCE_ANCESTRY_CPU_PREFLIGHT_PENDING','acceptedArt':False,
        'recipe':intake.pin(Path(__file__),intake.sha(__file__)),'native70':intake.pin(NATIVE,NATIVE_SHA),'production70':intake.pin(PRODUCTION,PRODUCTION_SHA),
        'canonicalNative02':intake.pin(BODY,BODY_SHA),'sourceWitnessBlocks':blocks,'leftCandidate':constructor['candidate'],
        'sameOriginalVertexCount':len(meshes['L']['positions']),'everySourceFaceHasOppositeCyclicRightAncestry':True,
        'selectedRightVersusReflectedLeftM':{'maximum':float(delta.max()),'p50p95p99':np.percentile(delta,[50,95,99]).tolist(),'differentVertices':int(np.count_nonzero(delta))},
        'native02ReflectedLeftFootNearestRightVertexM':{'maximum':float(foot_delta.max()),'p50p95p99':np.percentile(foot_delta,[50,95,99]).tolist()},
        'footSelection':'Existing native foot/toe coefficient sum >0.25; all selected points retained, no hidden-body claim or clearance threshold.',
        'sourceReadPrimaryImplementation':'/Applications/Blender.app/Contents/Resources/5.2/scripts/modules/_blendfile_header.py',
        'arrays':package(out/'preflight-arrays.bin',arrays),
        'limits':'No reflection fit assumption: right candidate uses actual separately authored right coordinates at shared source IDs and opposite winding. CPU normals are geometric angle-weighted proxies; independent native gates remain. Enclosure and allocation are not implied.'}
    (out/'source.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ['status','selectedRightVersusReflectedLeftM','native02ReflectedLeftFootNearestRightVertexM']}))


if __name__=='__main__':main()
