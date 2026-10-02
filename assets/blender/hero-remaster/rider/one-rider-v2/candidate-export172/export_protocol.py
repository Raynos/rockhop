"""Explicitly authored diagnostic extension; not lossless-all-fields or accepted art."""
import os
os.environ.setdefault('OPENBLAS_NUM_THREADS', '2')
os.environ.setdefault('OMP_NUM_THREADS', '2')
import copy, hashlib, importlib.util, json, subprocess
from pathlib import Path
import numpy as np
from inspect_contract import NPZ, SOURCE, REFERENCE, MAPPER, PRIVATE, EVIDENCE, REPO, pack_all, sha

def main():
    spec = importlib.util.spec_from_file_location('mapper170', MAPPER)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    source = mod.GLB(SOURCE); ref = mod.GLB(REFERENCE)
    g = copy.deepcopy(source); original = copy.deepcopy(g.j); original_bin = g.bin
    z = np.load(NPZ, allow_pickle=False)
    assert sha(NPZ) == 'ece32f56441f144925d83344e544331463f20c6e9f39221111b003702df35406'
    # Only changed garment materials use UV0. Protected gloves use UV1.
    texture_bindings = []
    def inspect(value, path=''):
        if isinstance(value, dict):
            if path.endswith('Texture'):
                assert value.get('texCoord', 0) == 0
                transform = value.get('extensions', {}).get('KHR_texture_transform', {})
                assert transform.get('texCoord', 0) == 0
                texture_bindings.append({'path': path, 'texCoord': value.get('texCoord', 0)})
            for key, child in value.items(): inspect(child, path + '/' + key)
        elif isinstance(value, list):
            for i, child in enumerate(value): inspect(child, path + '/' + str(i))
    for ordinal in [0, 2]:
        primitive = mod.inventory(g.j)[ordinal][2]
        inspect(g.j['materials'][primitive['material']], 'garment' + str(ordinal))
    consumer = subprocess.run(['rg', '-n', 'color_2|COLOR_2', str(REPO / 'src')], capture_output=True, text=True)
    assert consumer.returncode == 1 and not consumer.stdout
    loader = REPO / 'node_modules/three/examples/jsm/loaders/GLTFLoader.js'
    text = loader.read_text(); assert "COLOR_0: 'color'" in text and "COLOR_2:" not in text
    color_chunk = REPO / 'node_modules/three/src/renderers/shaders/ShaderChunk/color_vertex.glsl.js'
    assert 'color_2' not in color_chunk.read_text()
    rows = []
    def add(a, typ, component, signature=None):
        dtype = {5126:'<f4',5123:'<u2',5121:'u1',5125:'<u4'}[component]
        a = np.ascontiguousarray(a, dtype=dtype)
        g.bin += b'\0' * (-len(g.bin) % 4)
        vi = len(g.j['bufferViews']); offset = len(g.bin); g.bin += a.tobytes()
        g.j['bufferViews'].append({'buffer':0,'byteOffset':offset,'byteLength':a.nbytes})
        accessor = {'bufferView':vi,'componentType':component,'count':len(a),'type':typ}
        if signature is not None and 'normalized' in signature: accessor['normalized'] = signature['normalized']
        if component == 5126: accessor.update(min=a.min(0).tolist(),max=a.max(0).tolist())
        ai=len(g.j['accessors']);g.j['accessors'].append(accessor);return ai
    for ordinal, (_, _, primitive) in enumerate(mod.inventory(g.j)):
        if ordinal not in [0, 2]: continue  # All protected source bytes/references untouched.
        source_primitive = mod.inventory(source.j)[ordinal][2]
        old_count = len(source.array(primitive['attributes']['POSITION']))
        count = len(z[f'p{ordinal}']); old = z[f'oldVertex{ordinal}']
        assert np.array_equal(old[:old_count], np.arange(old_count))
        assert (old[old_count:] == -1).all()
        joints, weights = pack_all(z[f'W{ordinal}'])
        changes = []
        for semantic, accessor_id in list(primitive['attributes'].items()):
            accessor = source.j['accessors'][accessor_id]; old_values = source.array(accessor_id)
            if semantic in ['POSITION','NORMAL','TEXCOORD_0','JOINTS_0','WEIGHTS_0']:
                a = {'POSITION':z[f'p{ordinal}'],'NORMAL':z[f'n{ordinal}'],'TEXCOORD_0':z[f'uv{ordinal}'],
                     'JOINTS_0':joints,'WEIGHTS_0':weights}[semantic]
                changes.append({'semantic':semantic,'policy':'Authoritative NPZ; explicit float32 rounding for floats; all influences retained.'})
            elif count == old_count: continue
            else:
                a = np.zeros((count,old_values.shape[1]),dtype=old_values.dtype);a[:old_count]=old_values
                if semantic == 'TEXCOORD_1':
                    assert np.array_equal(old_values,source.array(source_primitive['attributes']['TEXCOORD_0']))
                    a[old_count:] = z[f'uv{ordinal}'][old_count:]
                    policy='Original rows exact; new rows duplicate authored UV0.'
                elif semantic == 'COLOR_2': policy='Original rows exact; new rows explicitly unused zero (not source-exact).'
                else:
                    assert len(np.unique(old_values,axis=0))==1, semantic
                    a[old_count:] = old_values[0];policy='Original rows exact; extend proven constant.'
                assert np.array_equal(a[:old_count],old_values)
                changes.append({'semantic':semantic,'policy':policy})
            primitive['attributes'][semantic] = add(a,accessor['type'],accessor['componentType'],accessor)
        primitive['indices'] = add(z[f'tr{ordinal}'].reshape(-1,1),'SCALAR',5125)
        for target in primitive.get('targets',[]):
            assert not np.any(source.array(target['POSITION']))
            if count == old_count: continue
            for semantic, accessor_id in list(target.items()):
                accessor=source.j['accessors'][accessor_id];old_values=source.array(accessor_id)
                a=np.zeros((count,old_values.shape[1]),dtype=old_values.dtype);a[:old_count]=old_values
                target[semantic]=add(a,accessor['type'],accessor['componentType'],accessor)
        rows.append({'primitive':ordinal,'originalRows':old_count,'newRows':count-old_count,'attributes':changes,
                     'morphPolicy':'Original POSITION/NORMAL deltas exact; new fabric POSITION/NORMAL deliberately zero: grip closure leaves authored garment surface unchanged.'})
    assert g.bin[:len(original_bin)] == original_bin
    for key in ['nodes','skins','materials','images','textures','samplers','animations']:
        assert g.j.get(key) == original.get(key), key
    for ordinal in [1,3,4]: assert mod.inventory(g.j)[ordinal][2] == mod.inventory(source.j)[ordinal][2]
    g.j['buffers'][0]['byteLength']=len(g.bin)
    output=PRIVATE/'source06';assert not output.exists();output.mkdir(parents=True)
    result=g.encode();path=output/'rider.glb';path.write_bytes(result)
    decoded=mod.GLB(path)
    for ordinal,(_,_,primitive) in enumerate(mod.inventory(decoded.j)):
        assert decoded.array(primitive['attributes']['POSITION']).shape[0]==len(z[f'p{ordinal}'])
        assert np.array_equal(decoded.array(primitive['indices']).reshape(-1,3),z[f'tr{ordinal}'])
        if ordinal in [0,2]:
            w=decoded.array(primitive['attributes']['WEIGHTS_0']);j=decoded.array(primitive['attributes']['JOINTS_0'])
            rebuilt=np.zeros((len(w),19),dtype=np.float32);np.add.at(rebuilt,(np.arange(len(w))[:,None],j),w)
            assert np.array_equal(rebuilt,z[f'W{ordinal}'].astype(np.float32))
    report={'status':'UNACCEPTED_EXPLICIT_EXTENSION_SKINNED_SOURCE_NO_MOTION_PASS',
            'source':str(SOURCE),'sourceSHA256':sha(SOURCE),'npz':str(NPZ),'npzSHA256':sha(NPZ),
            'output':str(path),'outputSHA256':sha(path),'recipeSHA256':sha(__file__),
            'sourceBINPrefixExact':True,'sourceNodes19BindProtectedPrimitivesPBRImagesAnimationsExact':True,
            'allLiteralDenseInfluencesRetainedFloat32CastOnly':True,'rows':rows,
            'consumerAudit':{'sourceRgPattern':'color_2|COLOR_2','sourceRgNoMatches':True,
                'changedGarmentMaterialTextureBindings':texture_bindings,
                'protectedGloveMaterialUsesUV1AndIsUntouched':True,
                'GLTFLoaderSHA256':sha(loader),'colorShaderChunkSHA256':sha(color_chunk)},
            'setupFailures':['Initial all-material UV0-only assertion rejected before output: protected glove material consumes UV1. Final proof is scoped to changed garment materials0/2; glove primitive/material remains exact.',
                             'Second setup run rejected before output because duplicate-UV check looked up a newly appended accessor on the immutable source. Final check explicitly reads the untouched source primitive.'],
            'limits':['Auxiliary/morph extensions deliberately newly authored, not lossless original information.',
                      'Float64 NPZ casts to standard float32; exact original protected source references remain untouched.',
                      'No V7 topology-specific49 correctives or responding-surface adapter copied.',
                      'Source still fresh.* names; needs strict candidate-handoff170 mapping before continuous runtime gate.',
                      'No stock Three.js motion, appearance, intersection, contact, gameplay or mobile acceptance.']}
    EVIDENCE.mkdir(parents=True,exist_ok=True);(EVIDENCE/'export-report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'status':report['status'],'output':str(path),'sha256':report['outputSHA256']}))

if __name__=='__main__': main()
