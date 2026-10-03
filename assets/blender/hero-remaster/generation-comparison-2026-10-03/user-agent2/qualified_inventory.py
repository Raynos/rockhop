"""Read-only installed-quality inventory; no imports, model loading or edits."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import urllib.request

BASE = Path('/Users/raynos/ml/img2mesh')
STORE = Path('/Users/raynos/projects/weights/manual')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def repo(path):
    def git(*args):
        return subprocess.check_output(['git', '-C', str(path), *args], text=True).strip()
    return {'path': str(path), 'head': git('rev-parse', 'HEAD'),
            'origin': git('remote', 'get-url', 'origin'),
            'existingChangesPreserved': git('status', '--short').splitlines()}


def file(path, content_hash=True):
    path = Path(path)
    result = {'path': str(path), 'exists': path.is_file()}
    if path.is_file():
        result.update(bytes=path.stat().st_size, resolvedPath=str(path.resolve()),
                      symlink=path.is_symlink())
        if content_hash:
            result['sha256'] = sha(path)
    return result


def view(path):
    args = json.loads(path.read_text())['args']
    checkpoints = []
    for name, stem in args['models'].items():
        config = Path(stem + '.json')
        record = {'role': name, 'config': file(config)}
        if config.is_file():
            spec = json.loads(config.read_text())
            record['modelClass'] = spec.get('name')
            record['projectionArgs'] = {k: v for k, v in spec.get('args', {}).items()
                                        if 'proj' in k or 'attn_mode' in k}
        record['weights'] = file(stem + '.safetensors', False)
        checkpoints.append(record)
    return {'config': file(path), 'defaultPipeline': args['default_pipeline_type'],
            'samplers': {k: args[k]['params'] for k in (
                'sparse_structure_sampler', 'shape_slat_sampler', 'tex_slat_sampler')},
            'imageConditioner': args['image_cond_model'], 'backgroundModel': args['rembg_model'],
            'checkpoints': checkpoints}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', required=True)
    parser.add_argument('--scratch', required=True)
    args = parser.parse_args()
    out, scratch = Path(args.out), Path(args.scratch)
    assert not out.exists() and not scratch.exists(), 'Fresh inventory paths required'
    scratch.mkdir(parents=True)
    upstream = []
    for model, url, phrases in [
        ('Hunyuan3D-2.1', 'https://raw.githubusercontent.com/Tencent-Hunyuan/Hunyuan3D-2.1/main/gradio_app.py',
         ['30', '384', '512', '5.0', 'guidance_scale']),
        ('TRELLIS.2', 'https://raw.githubusercontent.com/microsoft/TRELLIS.2/main/app.py',
         ['value="1024"', 'value=12', '1536_cascade']),
        ('Pixal3D', 'https://raw.githubusercontent.com/TencentARC/Pixal3D/master/inference.py',
         ['steps: int = 12', '1024 if low_vram else 1536', 'pipeline_type='])]:
        data = urllib.request.urlopen(url, timeout=30).read()
        target = scratch / (model + '-upstream.py')
        target.write_bytes(data)
        lines = data.decode().splitlines()
        upstream.append({'model': model, 'url': url, 'sha256': sha(target),
                         'witnesses': [{'line': i + 1, 'text': line.strip()}
                                       for i, line in enumerate(lines)
                                       if any(phrase in line for phrase in phrases)]})
    trellis = BASE / 'trellis-mac/TRELLIS.2'
    pixal = BASE / 'Pixal3D-mac'
    hunyuan = BASE / 'Hunyuan3D-2.1'
    report = {
        'accepted': False, 'lastVerified': '2026-10-03', 'modelRuns': 0,
        'recipe': file(__file__), 'publicUpstreamSnapshots': upstream,
        'repositories': [repo(BASE / 'trellis-mac'), repo(trellis), repo(pixal), repo(hunyuan), repo(BASE / 'NAF')],
        'trellis': view(BASE / 'trellis-view/pipeline.json'),
        'pixal': view(BASE / 'pixal-view/pipeline.json'),
        'hunyuanShapeWeights': [file(STORE / 'tencent/Hunyuan3D-2.1' / p, False) for p in (
            'hunyuan3d-dit-v2-1/model.fp16.ckpt', 'hunyuan3d-vae-v2-1/model.fp16.ckpt')],
        'pixalAdditionalConditioning': file(STORE / 'valeoai/NAF/naf_release.pth'),
        'backendSources': [file(p) for p in (
            trellis / 'trellis2/modules/sparse/attention/full_attn.py',
            BASE / 'trellis-mac/stubs/o_voxel_override_convert.py',
            pixal / 'pixal3d/modules/sparse/attention/full_attn.py',
            pixal / 'pixal3d/utils/mesh_extract.py',
            pixal / 'pixal3d/models/sc_vaes/fdg_vae.py',
            pixal / 'pixal3d/trainers/flow_matching/mixins/image_conditioned_proj.py', pixal / 'generate_mps.py',
            hunyuan / 'hy3dshape/hy3dshape/models/autoencoders/surface_extractors.py')],
        'qualifiedTargets': {
            'hunyuan': {'steps': 30, 'guidance': 5, 'octree': 384, 'finalistOctree': 512, 'extractor': 'mc'},
            'trellis': {'pipeline': '1024_cascade', 'stepsEach': 12, 'finalist': '1536_cascade'},
            'pixal': {'pipeline': '1536_cascade', 'stepsEach': 12, 'lowerMemory': '1024_cascade'}},
        'observations': [
            'Pixal projected ElasticSLatFlowModel checkpoints differ from TRELLIS SLatFlowModel; shared class name is not model identity.',
            'Local Pixal view defaults1024; official standard inference defaults1536, low_vram1024.',
            'TRELLIS local sparse naive aliases MPS SDPA; Pixal naive is explicit chunked float32 matmul/softmax.',
            'TRELLIS derived orientation controls are not CUDA equivalence or complete garment topology validation.',
            'Requested1536 cascade can reduce actual resolution under token limit; report returned resolution.'],
        'limits': ['Static identity/settings/presence audit only; backend fixtures and inference pending.',
                   'Large weight digests not rehashed by this inventory; published provenance does not replace fresh verification.',
                   'No runtime/shared source/checkpoint edits, downloads of weights, cleanup or model promotion.']}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + '\n')
    assert all(c['weights']['exists'] and c['config']['exists']
               for k in ('trellis', 'pixal') for c in report[k]['checkpoints'])
    assert all(p['exists'] for p in report['hunyuanShapeWeights'])
    assert all(p['exists'] for p in report['backendSources'])
    print(json.dumps({'report': str(out), 'sha256': sha(out), 'modelRuns': 0,
                      'trellisCheckpoints': len(report['trellis']['checkpoints']),
                      'pixalCheckpoints': len(report['pixal']['checkpoints'])}))


if __name__ == '__main__':
    main()
