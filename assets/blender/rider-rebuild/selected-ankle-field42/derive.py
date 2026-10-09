"""CPU-only: derive selected jeans ankle fields from actual outward body triangles.

No posed fit, parameter sweep, rank pruning, geometry change or asset promotion.
The support ends at the actual canonical foot-positive triangle boundary.
"""
import hashlib
import json
import struct
import sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        while block := f.read(1048576): h.update(block)
    return h.hexdigest()

def pin(row):
    p = ROOT / row['path']; assert sha(p) == row['sha256'], row['path']; return p

class GLB:
    """Read only selected accessor ranges, never the 357 MB texture payload."""
    def __init__(self, path):
        self.file = Path(path).open('rb')
        magic, version, length, count, kind = struct.unpack('<5I', self.file.read(20))
        assert magic == 0x46546c67 and version == 2 and kind == 0x4e4f534a
        self.doc = json.loads(self.file.read(count)); self.offset = count + 28
        assert struct.unpack('<2I', self.file.read(8))[1] == 0x004e4942
    def array(self, index):
        a = self.doc['accessors'][index]; v = self.doc['bufferViews'][a['bufferView']]
        assert not a.get('sparse') and not a.get('normalized') and v['buffer'] == 0
        width = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[a['type']]
        dtype = np.dtype({5121:'u1',5123:'<u2',5125:'<u4',5126:'<f4'}[a['componentType']])
        stride = v.get('byteStride', width*dtype.itemsize)
        start = self.offset + v.get('byteOffset',0) + a.get('byteOffset',0)
        self.file.seek(start); data = self.file.read((a['count']-1)*stride + width*dtype.itemsize)
        return np.ndarray((a['count'],width),dtype,buffer=data,strides=(stride,dtype.itemsize)).copy()
    def mesh(self, name):
        node = next(n for n in self.doc['nodes'] if n.get('name') == name)
        assert 'matrix' not in node and not any(k in node for k in ['translation','rotation','scale'])
        mesh = self.doc['meshes'][node['mesh']]; assert len(mesh['primitives']) == 1
        prim = mesh['primitives'][0]; attrs = {k:self.array(v) for k,v in prim['attributes'].items()}
        ids = attrs['_NATIVE_ID'].ravel().astype(int); pos = attrs['POSITION'][:,[0,2,1]].copy(); pos[:,1] *= -1
        count = int(ids.max())+1; native = np.empty((count,3),np.float32); native[ids] = pos
        assert np.array_equal(native[ids],pos) and len(set(ids)) == count
        faces = ids[self.array(prim['indices']).reshape(-1,3)]
        names = [self.doc['nodes'][i]['name'] for i in self.doc['skins'][node['skin']]['joints']]
        fields = np.zeros((count,len(names)),float)
        for exported, native_id in enumerate(ids):
            row = np.zeros(len(names)); np.add.at(row, attrs['JOINTS_0'][exported].astype(int), attrs['WEIGHTS_0'][exported])
            if exported and np.any(fields[native_id]): assert np.array_equal(fields[native_id],row)
            fields[native_id] = row
        return native, faces, fields, names

def ray_rows(q, p, f, ankle, knee, sign):
    axis = knee-ankle
    origins = np.c_[ankle[:2]+((q[:,2]-ankle[2])/axis[2])[:,None]*axis[:2],q[:,2]]
    directions = q-origins; radius = np.linalg.norm(directions,axis=1); directions /= radius[:,None]
    valid = np.all(p[f,0]*sign>0,axis=1) & (p[f,2].max(1)>=q[:,2].min()) & (p[f,2].min(1)<=q[:,2].max())
    fi = np.flatnonzero(valid); a = p[f[fi,0]]; e1 = p[f[fi,1]]-a; e2 = p[f[fi,2]]-a; normals = np.cross(e1,e2)
    result = []
    for o,d,r in zip(origins,directions,radius):
        h = np.cross(np.broadcast_to(d,e2.shape),e2); det = (e1*h).sum(1)
        safe = np.abs(det)>1e-15; inv = np.zeros(len(det)); inv[safe] = 1/det[safe]
        s = o-a; u = inv*(s*h).sum(1); cross = np.cross(s,e1); v = inv*(cross*d).sum(1); t = inv*(cross*e2).sum(1)
        hit = safe & (u>=-1e-9) & (v>=-1e-9) & (u+v<=1+1e-9) & (t>0)
        ix = np.flatnonzero(hit); assert len(ix), 'No same-leg actual triangle ray hit'
        index = ix[np.argmin(t[ix])]; bary = np.array([1-u[index]-v[index],u[index],v[index]])
        assert np.all(bary>=-1e-9) and normals[index]@d>0 and t[index]<r
        result.append((int(fi[index]), bary, float(r-t[index]), len(ix)))
    return result

def transform(p, m): return p@m[:3,:3].T+m[:3,3]

def main():
    config = json.loads((HERE/'input.json').read_text()); out = Path(sys.argv[1]).resolve()
    assert out.is_relative_to(ROOT/'harness/out/rider-rebuild/selected-ankle-field42') and not out.exists()
    sources = {k:pin(v) for k,v in config['sources'].items()}; out.mkdir(parents=True)
    ref = np.load(sources['reference']); prefix = 'RiderBody__FullAnatomyReference'
    p = ref[prefix+'_basis'].astype(float); f = ref[prefix+'_triangles']; source_ids = ref[prefix+'__SOURCE_VERTEX_ID']
    named = json.loads(sources['canonicalFields'].read_text()); assert len(named)==len(p)
    canonical = np.load(sources['originalBody']); original_ids = canonical['nativeSourceVertexIds']; original_lookup = {int(v):i for i,v in enumerate(original_ids)}
    below = np.flatnonzero(p[:,2]<.24); assert len(below)==2638
    for i in below:
        k = original_lookup[int(source_ids[i])]; assert np.array_equal(p[i].astype(np.float32),canonical['vertices'][k].astype(np.float32))
        actual = {str(n):float(v) for n,v in zip(canonical['jointNames'],canonical['nativeCoefficients'][k]) if v>0}
        assert actual == named[i], ('Canonical source row mismatch',int(i))
    gameplay = json.loads(sources['gameplayMatrices'].read_text()); bones = {b['name']:b for b in gameplay['nativeRest']['bones']}
    glb = GLB(sources['runtime']); jp,jf,jw,loaded_names = glb.mesh('RiderJeans')
    names = gameplay['boneNames']; assert set(loaded_names)==set(names)
    jw = jw[:,[loaded_names.index(n) for n in names]]
    frozen = np.load(sources['hemSelection']); upper = set(dict(json.loads(sources['upperSelection'].read_text())['jeans']['influence']))
    body_fields = np.array([[row.get(n,0) for n in names] for row in named]); inverse = np.linalg.inv(np.array([bones[n]['matrix'] for n in names]))
    generic = np.load(sources['genericMatrices']); assert generic['boneNames'].tolist()==names
    envelopes = [(a['name'],np.asarray(a['nativeWorldMatrices'])) for a in gameplay['actions']]
    envelopes += [(a['name'],generic['pose'+str(i)]) for i,a in enumerate(json.loads(sources['genericReceipt'].read_text())['actions'])]
    all_ids=[]; all_weights=[]; all_faces=[]; all_bary=[]; all_before=[]; report={'acceptedArt':False,'status':'SOURCE_DERIVED_ANKLE_FIELDS_NATIVE_AND_MOVING_REVIEW_PENDING','recipeSHA256':sha(__file__),'sources':config['sources'],'canonicalRowsBelow24cmExactBasisAndNamedFields':len(below),'sides':{},'limits':['CPU field derivation and deformation evidence only; native execution and complete-outfit played art review pending.','Rest radial cloth/body stand-off is measured, not changed. Boot/cloth intersection, selected detail and collar overlap require actual posed triangles and clips.','Canonical anatomical field transfer is a declared lower-jeans ancestry change; upper author02 and unrelated fields stay protected.']}
    for side,sign in [('L',1),('R',-1)]:
        foot = names.index('DEF-foot.'+side); shin = names.index('DEF-shin.'+side+'.001')
        support_faces = np.flatnonzero((body_fields[f,foot].max(1)>0)&(p[f,2].max(1)>.1)&np.all(p[f,0]*sign>0,axis=1))
        ceiling = float(p[f[support_faces],2].max())
        ids = np.flatnonzero((jp[:,0]*sign>0)&(jp[:,2]<=ceiling)); frozen_ids = frozen['nativeIds'+side]
        assert np.array_equal(jp[frozen_ids],frozen['beforeLocal'+side]) and set(frozen_ids)<=set(ids) and not upper.intersection(ids)
        assert np.array_equal(jw[ids,shin],np.ones(len(ids))) and np.array_equal(jw[ids].sum(1),np.ones(len(ids)))
        hits = ray_rows(jp[ids].astype(float),p,f,np.array(bones['DEF-foot.'+side]['head']),np.array(bones['DEF-shin.'+side]['head']),sign)
        owner = np.array([r[0] for r in hits]); bary = np.array([r[1] for r in hits]); transferred = np.einsum('ij,ijk->ik',bary,body_fields[f[owner]])
        assert np.all(transferred>=-1e-10) and set(np.flatnonzero(transferred.max(0)>0)) <= {foot,shin}
        transferred /= transferred.sum(1)[:,None]; changed = transferred[:,foot]>0
        edit_ids = ids[changed]; fields = transferred[changed]; assert len(edit_ids)>0
        all_ids.extend(edit_ids); all_weights.extend(fields); all_faces.extend(owner[changed]);all_bary.extend(bary[changed]);all_before.extend(jp[edit_ids])
        boundary = jf[np.any(np.isin(jf,edit_ids),axis=1)]; edges = np.unique(np.sort(np.concatenate([boundary[:,[0,1]],boundary[:,[1,2]],boundary[:,[2,0]]]),axis=1),axis=0)
        required = np.unique(edges); old = jw[required]; new = old.copy(); lookup={int(i):k for k,i in enumerate(required)}
        for i,row in zip(edit_ids,fields):new[lookup[int(i)]]=row
        edge_index = np.array([[lookup[int(i)] for i in edge] for edge in edges]); cross = np.isin(edges,edit_ids).sum(1)==1
        rest_lengths = np.linalg.norm(jp[edges[:,0]]-jp[edges[:,1]],axis=1); assert np.all(rest_lengths>0)
        summaries=[]
        for label,worlds in envelopes:
            worst={'maximumCanonicalFieldDepartureM':0,'maximumOldEdgeStretchRatio':0,'maximumNewEdgeStretchRatio':0,'maximumBoundaryDisplacementJumpM':0}
            for frame,world in enumerate(worlds):
                matrices=world@inverse; old_pos=np.zeros((len(required),3));new_pos=np.zeros_like(old_pos)
                for j in np.flatnonzero(np.any(old+new>0,axis=0)):
                    transformed=transform(jp[required],matrices[j]);old_pos+=transformed*old[:,j,None];new_pos+=transformed*new[:,j,None]
                departure=np.linalg.norm(new_pos-old_pos,axis=1); old_len=np.linalg.norm(old_pos[edge_index[:,0]]-old_pos[edge_index[:,1]],axis=1);new_len=np.linalg.norm(new_pos[edge_index[:,0]]-new_pos[edge_index[:,1]],axis=1)
                value=float(departure.max())
                if value>worst['maximumCanonicalFieldDepartureM']:worst.update(maximumCanonicalFieldDepartureM=value,departureFrame=frame+1,departureNativeID=int(required[np.argmax(departure)]))
                worst['maximumOldEdgeStretchRatio']=max(worst['maximumOldEdgeStretchRatio'],float(np.max(old_len/rest_lengths)))
                worst['maximumNewEdgeStretchRatio']=max(worst['maximumNewEdgeStretchRatio'],float(np.max(new_len/rest_lengths)))
                jump=np.linalg.norm((new_pos-old_pos)[edge_index[:,0]]-(new_pos-old_pos)[edge_index[:,1]],axis=1)
                worst['maximumBoundaryDisplacementJumpM']=max(worst['maximumBoundaryDisplacementJumpM'],float(jump[cross].max()))
            summaries.append({'action':label,'frames':len(worlds),**worst})
        gaps=np.array([h[2] for h in hits]);report['sides'][side]={'frozenHemVertices':len(frozen_ids),'actualCanonicalSupportCeilingM':ceiling,'inspectedVertices':len(ids),'changedVertices':len(edit_ids),'additionalIdsBeyondFrozenHem':sorted(set(map(int,edit_ids))-set(map(int,frozen_ids))),'outwardSameLegHitCount':len(hits),'maximumRayHitCount':max(h[3]for h in hits),'minimumRadialBodyStandOffM':float(gaps.min()),'maximumRadialBodyStandOffM':float(gaps.max()),'minimumFootWeight':float(fields[:,foot].min()),'maximumFootWeight':float(fields[:,foot].max()),'maximumSupportCount':int((fields>0).sum(1).max()),'incidentDecodedTriangleEdges':len(edges),'boundaryCrossingEdges':int(cross.sum()),'maximumBoundaryFieldL1Jump':float(np.abs(new[edge_index[cross,0]]-new[edge_index[cross,1]]).sum(1).max()),'envelopes':summaries}
    order=np.argsort(all_ids);ids=np.array(all_ids,np.int32)[order]; weights=np.array(all_weights)[order].astype(np.float32)
    np.savez_compressed(out/'field-patch.npz',nativeIds=ids,beforeLocal=np.array(all_before,np.float32)[order],weights=weights,boneNames=np.array(names),bodyTriangle=np.array(all_faces,np.int32)[order],barycentric=np.array(all_bary)[order])
    rows=[{'nativeID':int(i),'before':{'DEF-shin.'+('L' if jp[i,0]>0 else 'R')+'.001':1},'after':{n:float(v)for n,v in zip(names,row)if v>0}}for i,row in zip(ids,weights)]
    (out/'field-rows.json').write_text(json.dumps(rows,indent=2)+'\n');report['patch']={'path':str((out/'field-patch.npz').relative_to(ROOT)),'sha256':sha(out/'field-patch.npz')};report['namedRows']={'path':str((out/'field-rows.json').relative_to(ROOT)),'sha256':sha(out/'field-rows.json')}
    (out/'receipt.json').write_text(json.dumps(report,indent=2)+'\n'); print(json.dumps(report,indent=2))
if __name__=='__main__':main()
