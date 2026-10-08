"""IO-only exact selected hoodie handoff. No Blender, fitting, bake or contact."""
import ast
import hashlib
import json
import struct
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
EVIDENCE = ROOT/'docs/evidence/rider-rebuild/production-hoodie02/artist-handoff01'
PREFIX = 'rockhop-selected-hoodie-artist01/'


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as handle:
        while block := handle.read(1024*1024): h.update(block)
    return h.hexdigest()


def main():
    controls_path = HERE.parent/'local-outside01/controls.json'
    controls = json.loads(controls_path.read_text())
    spec = json.loads((ROOT/controls['pins']['frozenInputs']['path']).read_text())
    paths = {}

    def add(path, role, expected=None):
        path = Path(path)
        if not path.is_absolute(): path = ROOT/path
        assert path.is_file() and path.resolve().is_relative_to(ROOT)
        digest = sha(path)
        if expected is not None: assert digest == expected, ('Changed immutable input',str(path))
        key = str(path.relative_to(ROOT))
        paths[key] = {'role':role,'sha256':digest,'bytes':path.stat().st_size,
                      'archivePath':PREFIX+key}

    for key,pin in controls['pins'].items(): add(pin['path'],key,pin['sha256'])
    for key in ('selectedNative','originalDensePaint','nativeMaster','nativeArrays','geometricControlReceipt'):
        pin = spec[key];add(pin['path'],key,pin['sha256'])
    extras = {
        'harness/out/rider-rebuild/production-hoodie01/regional-repair01/hoodie-fields.npz':'Actual current garment full coefficient fields',
        'harness/out/rider-rebuild/production-hoodie01/regional-repair01/proportional-fit-before-patch.blend':'Actual fitted selected surface before local topology edits',
        'harness/out/rider-rebuild/production-hoodie01/regional-repair01/proportional-fit.json':'Pre-topology saved native lineage',
        'assets/blender/rider-rebuild/production-assembly01/render.py':'Exact same-camera diagnostic renderer',
        'assets/blender/rider-rebuild/production-hoodie02/local-outside01/finish.py':'Exact failed one-pass source; do not rerun',
        'assets/blender/rider-rebuild/production-hoodie02/local-outside01/controls.json':'Exact failed one-pass controls',
        'docs/evidence/rider-rebuild/production-hoodie02/local-outside01/source-checkpoint.json':'Failed one-pass source checkpoint',
        'harness/out/rider-rebuild/production-hoodie02/local-outside01/trial01/diagnosis.json':'Actual pre-edit scope/topology/clipping diagnosis',
        'docs/evidence/rider-rebuild/production-hoodie02/local-outside01/guard01/guard.json':'Exact one-pass controller result',
        'docs/evidence/rider-rebuild/production-hoodie02/local-outside01/guard01/worker.txt':'Exact failed operation output',
        'docs/evidence/rider-rebuild/production-hoodie02/source-checkpoint.json':'Original dense PBR/frame source intake',
        'assets/blender/rider-rebuild/production-hoodie02/controls.json':'Original dense immutable intake',
        'assets/blender/rider-rebuild/production-hoodie02/prepare_dense.py':'Unexecuted frozen dense pre-bake helper provenance',
        'docs/evidence/rider-rebuild/production-hoodie02/target-review01/FINDING.md':'Parent negative rest-fit finding',
        'docs/evidence/rider-rebuild/production-hoodie02/target-review01/render-spec.json':'Matched negative three-view specification',
        'docs/evidence/rider-rebuild/production-hoodie02/target-review01/render.json':'Matched negative three-view receipt',
        'docs/evidence/rider-rebuild/production-hoodie02/target-review01/front.png':'Parent-rejected actual front view',
        'docs/evidence/rider-rebuild/production-hoodie02/target-review01/back.png':'Parent-rejected actual back view',
        'docs/evidence/rider-rebuild/production-hoodie02/target-review01/profile.png':'Parent-rejected actual profile view',
        'assets/blender/hero-remaster/rider/anatomical-foundation-2026-10-03/user-agent1/selected-hoodie25/report.json':'Original selected native geometry/shading provenance',
        'docs/evidence/hero-remaster/anatomical-foundation-2026-10-03/user-agent1/selected-hoodie24/review85/review.json':'Historical original-donor orbit provenance; unaccepted fitted context',
        'docs/evidence/hero-remaster/anatomical-foundation-2026-10-03/user-agent1/selected-hoodie24/review85/matched-actual-donor24.mp4':'Historical actual original-donor played reference',
        'docs/evidence/rider-rebuild/production-hoodie02/artist-handoff01/ARTIST_BRIEF.md':'Artist scope, observations and required native handback',
        str((HERE/'.gitignore').relative_to(ROOT)):'Binary package exclusion',
        str(Path(__file__).resolve().relative_to(ROOT)):'IO-only reproducible packer',
    }
    for path,role in extras.items(): add(path,role)
    diagnosis = json.loads((ROOT/'harness/out/rider-rebuild/production-hoodie02/local-outside01/trial01/diagnosis.json').read_text())
    failed_vertex = 12473
    assert failed_vertex in diagnosis['scopedVertices'] and failed_vertex in diagnosis['patchVertices']
    assert diagnosis['unexpectedLocalBoundaryEdges'] == []
    guard = json.loads((ROOT/'docs/evidence/rider-rebuild/production-hoodie02/local-outside01/guard01/guard.json').read_text())
    assert guard['exitCode'] == 1 and guard['elapsedSeconds'] == 1.032
    assert not (ROOT/'harness/out/rider-rebuild/production-hoodie02/local-outside01/trial01/local-outside-hoodie.blend').exists()
    source_checkpoint = json.loads((ROOT/'docs/evidence/rider-rebuild/production-hoodie02/local-outside01/source-checkpoint.json').read_text())
    assert sha(HERE.parent/'local-outside01/finish.py') == source_checkpoint['sourceSHA256']
    assert sha(controls_path) == source_checkpoint['controlsSHA256']
    render = json.loads((ROOT/'docs/evidence/rider-rebuild/production-hoodie02/target-review01/render.json').read_text())
    assert render['sourceNative']['sha256'] == controls['pins']['authoredNative']['sha256']
    assert sha(ROOT/'assets/blender/rider-rebuild/production-assembly01/render.py') == render['recipeSHA256']
    for view in render['outputs']:
        assert sha(ROOT/'docs/evidence/rider-rebuild/production-hoodie02/target-review01'/Path(view['path']).name) == view['sha256']
    # Extract original embedded PNG bytes without decoding or altering pixels.
    original = ROOT/spec['originalDensePaint']['path']
    image_dir = HERE/'original-pbr';image_dir.mkdir(exist_ok=True)
    with original.open('rb') as handle:
        _,_,_,size,_ = struct.unpack('<5I',handle.read(20))
        gltf = json.loads(handle.read(size))
        _,kind = struct.unpack('<2I',handle.read(8));assert kind == 0x004E4942
        start = handle.tell()
        assert all('normalTexture' not in m for m in gltf['materials'])
        pbr = gltf['materials'][0]['pbrMetallicRoughness']
        original_images = []
        for channel,key in [('baseColor','baseColorTexture'),('metallicRoughness','metallicRoughnessTexture')]:
            image_index = gltf['textures'][pbr[key]['index']]['source']
            image = gltf['images'][image_index];assert image['mimeType']=='image/png'
            view = gltf['bufferViews'][image['bufferView']]
            handle.seek(start+view.get('byteOffset',0));data = handle.read(view['byteLength'])
            assert data[:8] == b'\x89PNG\r\n\x1a\n' and struct.unpack('>2I',data[16:24])==(4096,4096)
            path = image_dir/(channel+'.png')
            if path.exists(): assert path.read_bytes() == data
            else: path.write_bytes(data)
            add(path,'Byte-exact original embedded 4K '+channel)
            original_images.append({'channel':channel,'gltfImageIndex':image_index,'pixels':[4096,4096],
                                    'path':str(path.relative_to(ROOT)),'sha256':sha(path)})
    ast.parse(Path(__file__).read_text())
    manifest = {'accepted':False,'stage':'EXACT_SELECTED_HOODIE_ARTIST_HANDOFF_NO_REPAIR_RETRY',
                'entryNative':controls['pins']['authoredNative'],
                'bodyVertices':10582,'nativeRestBones':75,
                'bodyAnd75RigSignature':json.loads((ROOT/controls['pins']['authorReceipt']['path']).read_text())['bodyAnd75RigSignature'],
                'failure':{'exitCode':1,'elapsedSeconds':1.032,'vertex':failed_vertex,
                           'inScopedVertices':True,'inPatchVertices':True,
                           'predicate':'i in scoped and i not in already_loose',
                           'interpretation':'Recorded scope proves first term true; failure identifies loose-preservation exclusion.',
                           'undetermined':'Per-vertex distance, displacement, and cause of modifier movement were not recorded.',
                           'noSavedCorrectedNative':True},
                'localDiagnosis':{k:diagnosis[k] for k in ('classification','nearestBodyInsideVertices','nearestBodyBelowClothClearanceVertices','unexpectedLocalBoundaryEdges')},
                'originalImages':original_images,'originalGLTFMaterials':gltf['materials'],
                'files':paths,'limits':['Unaccepted actual selected sources only. No generated replacement or repaired successor.',
                                      'No heavy job, rerun, bake, model export, artist contact, player promotion or art acceptance.',
                                      'Parent alone judges. All R0–R5 open.']}
    manifest_path = EVIDENCE/'manifest.json'
    manifest_path.write_text(json.dumps(manifest,indent=2)+'\n')
    archive = HERE/'selected-hoodie-artist01.zip'
    assert not archive.exists(), 'Keep existing packaged artifact immutable'
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_STORED,allowZip64=True) as bundle:
        for path,record in sorted(paths.items()):
            assert sha(ROOT/path) == record['sha256']
            bundle.write(ROOT/path,record['archivePath'])
        bundle.write(manifest_path,PREFIX+str(manifest_path.relative_to(ROOT)))
    with zipfile.ZipFile(archive) as bundle:
        assert bundle.testzip() is None
        for path,record in paths.items():
            digest = hashlib.sha256()
            with bundle.open(record['archivePath']) as handle:
                while block := handle.read(1024*1024): digest.update(block)
            assert digest.hexdigest() == record['sha256'] == sha(ROOT/path)
        assert bundle.read(PREFIX+str(manifest_path.relative_to(ROOT))) == manifest_path.read_bytes()
    report = {'accepted':False,'stage':'IO_ONLY_PACKAGE_VERIFIED',
              'archive':{'path':str(archive.relative_to(ROOT)),'sha256':sha(archive),'bytes':archive.stat().st_size},
              'manifestSHA256':sha(manifest_path),'fileCount':len(paths)+1,
              'zipCRCPassed':True,'everyArchiveMemberSHA256Passed':True,'allOriginalSourcesUnchanged':True,
              'limits':manifest['limits']}
    (EVIDENCE/'package-verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__ == '__main__': main()
