"""Append the ONE canonical named patch to selected transport02; private only.

CPU-only streaming writer. Original binary, mesh geometry, UV, PBR, animations
and every unrelated skin row survive unchanged. No rank pruning or native claim.
"""
import copy
import importlib.util
import json
import shutil
import struct
import sys
from pathlib import Path
import numpy as np

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('ankle42derive',HERE/'derive.py');derive=importlib.util.module_from_spec(spec);spec.loader.exec_module(derive)
ROOT=derive.ROOT;sha=derive.sha;pin=derive.pin

def main():
    receipt_path=Path(sys.argv[1]).resolve();out=Path(sys.argv[2]).resolve()
    assert out.is_relative_to(ROOT/'harness/out/rider-rebuild/selected-ankle-field42') and not out.exists()
    receipt=json.loads(receipt_path.read_text());config=json.loads((HERE/'input.json').read_text())
    assert receipt['recipeSHA256']==sha(HERE/'derive.py') and receipt['sources']==config['sources']
    rows=json.loads(pin(receipt['namedRows']).read_text());patch=np.load(pin(receipt['patch']))
    source=pin(config['sources']['runtime']);g=derive.GLB(source);doc=copy.deepcopy(g.doc);old=copy.deepcopy(doc)
    native,faces,fields,names=g.mesh('RiderJeans');node=next(n for n in doc['nodes']if n.get('name')=='RiderJeans');prim=doc['meshes'][node['mesh']]['primitives'][0]
    attr=prim['attributes'];exported_ids=g.array(attr['_NATIVE_ID']).ravel().astype(int)
    joints=g.array(attr['JOINTS_0']).astype(np.uint8);weights=g.array(attr['WEIGHTS_0']).astype('<f4')
    edits={r['nativeID']:r for r in rows};assert len(edits)==len(rows)==len(patch['nativeIds'])
    assert np.array_equal(native[patch['nativeIds']],patch['beforeLocal'])
    for i in np.flatnonzero(np.isin(exported_ids,patch['nativeIds'])):
        row=edits[int(exported_ids[i])];before={n:float(v)for n,v in zip(names,fields[row['nativeID']])if v>0};assert before==row['before']
        after=row['after'];assert 0<len(after)<=4 and all(v>0 for v in after.values()) and abs(sum(after.values())-1)<1e-7
        joints[i]=0;weights[i]=0
        for k,(n,v)in enumerate(sorted(after.items())):joints[i,k]=names.index(n);weights[i,k]=v
    bin_length=doc['buffers'][0]['byteLength'];assert bin_length%4==0
    payloads=[]
    for semantic,array,component in [('JOINTS_0',joints,5121),('WEIGHTS_0',weights,5126)]:
        payload=array.tobytes();view=len(doc['bufferViews']);doc['bufferViews'].append({'buffer':0,'byteOffset':bin_length,'byteLength':len(payload),'target':34962})
        acc=len(doc['accessors']);doc['accessors'].append({'bufferView':view,'componentType':component,'count':len(array),'type':'VEC4'});attr[semantic]=acc
        payloads.append(payload);bin_length+=len(payload)
    doc['buffers'][0]['byteLength']=bin_length
    protected=copy.deepcopy(doc);protected['meshes'][node['mesh']]['primitives'][0]['attributes']=copy.deepcopy(old['meshes'][node['mesh']]['primitives'][0]['attributes']);protected['buffers']=old['buffers'];protected['bufferViews']=protected['bufferViews'][:-2];protected['accessors']=protected['accessors'][:-2];assert protected==old
    out.mkdir(parents=True);target=out/'rider.glb';encoded=json.dumps(doc,separators=(',',':')).encode();encoded+=b' '*((-len(encoded))%4)
    with target.open('wb')as f:
        f.write(struct.pack('<5I',0x46546c67,2,28+len(encoded)+bin_length,len(encoded),0x4e4f534a));f.write(encoded);f.write(struct.pack('<2I',bin_length,0x004e4942))
        g.file.seek(g.offset);remaining=old['buffers'][0]['byteLength']
        while remaining:
            block=g.file.read(min(1048576,remaining));assert block;f.write(block);remaining-=len(block)
        for payload in payloads:f.write(payload)
    actual=derive.GLB(target);ap,af,aw,an=actual.mesh('RiderJeans');assert np.array_equal(ap,native)and np.array_equal(af,faces)and an==names
    expected=fields.copy()
    for i,row in edits.items():expected[i]=[row['after'].get(n,0)for n in names]
    assert np.array_equal(aw,expected)
    contract_path=pin(config['previewContract']);contract=json.loads(contract_path.read_text());assert contract['glbSHA256']==config['sources']['runtime']['sha256']
    contract['glbSHA256']=sha(target);contract['accepted']=False;assert contract['qualificationState']=='UNACCEPTED_GAMEPLAY_LEAN_REVIEW';contract['weightIntervention']={'accepted':False,'kind':'canonical-ankle-field42','nativeParityPending':True}
    contract['ankleField42']={'acceptedArt':False,'kind':'same-selected-geometry-canonical-ankle-field','receipt':{'path':str(receipt_path.relative_to(ROOT)),'sha256':sha(receipt_path)},'namedRows':receipt['namedRows'],'changedNativeVertices':len(rows),'maximumInfluences':2,'rankPruning':False,'sourceRuntime':config['sources']['runtime'],'sourcePreviewContract':config['previewContract'],'limits':['Private complete-outfit art preview; native application/reopen/engine parity and played art acceptance pending.','All original binary bytes preserved; appended only JOINTS_0 and WEIGHTS_0.']}
    (out/'rider-contract.json').write_text(json.dumps(contract,indent=2)+'\n')
    result={'acceptedArt':False,'status':'PRIVATE_SELECTED_ANKLE_FIELDS_PREVIEW_NATIVE_PARITY_PENDING','recipeSHA256':sha(__file__),'source':config['sources']['runtime'],'patchReceipt':contract['ankleField42']['receipt'],'glb':{'path':str(target.relative_to(ROOT)),'sha256':contract['glbSHA256']},'contract':{'path':str((out/'rider-contract.json').relative_to(ROOT)),'sha256':sha(out/'rider-contract.json')},'changedNativeVertices':len(rows),'originalBinaryBytesPreserved':old['buffers'][0]['byteLength'],'geometryTopologyMapsAndUnrelatedRowsExact':True,'limits':contract['ankleField42']['limits']}
    (out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
