"""Geometry-only selected skin derivative retaining exact original UV charts.

Wrap the frozen production25 geometry/field construction for SKIN ONLY. The
bilateral boots entry point and frozen production input remain unchanged.
"""
import hashlib
import importlib.util
import json
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


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def material_state(obj):
    materials = []; images = {}
    for material in obj.data.materials:
        assert material and material.use_nodes
        nodes = []; links = []
        for node in material.node_tree.nodes:
            assert node.type != 'GROUP', 'Unknown nested selected skin shader requires explicit review'
            inputs = []
            for socket in node.inputs:
                if not hasattr(socket, 'default_value'): continue
                value = socket.default_value
                if not isinstance(value, (str, bool, float, int)):
                    try: value = list(value)
                    except TypeError: value = str(value)
                inputs.append((socket.identifier, value))
            row = {'name': node.name, 'type': node.type, 'inputs': inputs}
            if node.type == 'TEX_IMAGE' and node.image:
                image = node.image; assert image.packed_file and not image.is_float
                digest = hashlib.sha256(image.packed_file.data).hexdigest()
                row.update(image=image.name, imageSHA256=digest, interpolation=node.interpolation, extension=node.extension)
                images[image.name] = {'sha256': digest, 'dimensions': list(image.size),
                                      'colorSpace': image.colorspace_settings.name,
                                      'residentRGBA8MipBytes': UV.rgba8_mip_bytes(*image.size)}
            nodes.append(row)
        for link in material.node_tree.links:
            links.append((link.from_node.name, link.from_socket.identifier, link.to_node.name, link.to_socket.identifier))
        materials.append({'name': material.name, 'diffuse': list(material.diffuse_color), 'nodes': nodes, 'links': sorted(links)})
    return {'materialGraphSHA256': hashlib.sha256(json.dumps(materials, sort_keys=True).encode()).hexdigest(),
            'materials': [m.name for m in obj.data.materials], 'images': images}


def charts(obj):
    obj.data.calc_loop_triangles(); loops = np.empty((len(obj.data.loop_triangles), 3), np.int32)
    obj.data.loop_triangles.foreach_get('loops', loops.ravel())
    materials = np.array([t.material_index for t in obj.data.loop_triangles], dtype=np.int32)
    result = {}
    for layer in obj.data.uv_layers:
        uv = np.empty((len(layer.data), 2), np.float32); layer.data.foreach_get('uv', uv.ravel())
        result[layer.name] = UV.chart(uv[loops], materials)
    assert result, 'Missing original selected skin UVs'
    return result


def main():
    global UV
    args = sys.argv[sys.argv.index('--')+1:]
    assert len(args) == 4 and args[3] == 'skin', 'This wrapper owns only the skin family'
    manifest = json.loads((HERE/'input.json').read_text())
    for row in manifest['pins'].values(): assert sha(ROOT/row['path']) == row['sha256'], row
    assert sha(Path(args[0])) == manifest['pins']['productionInput']['sha256']
    config = json.loads(Path(args[0]).read_text())
    engine = load(ROOT/manifest['pins']['productionAuthor']['path'], 'selected_skin29_frozen_production25')
    UV = load(ROOT/manifest['pins']['uvHelper']['path'], 'selected_skin29_uv')
    original = engine.simplify; state = {}

    def simplify(source, rig, spec, level, cfg):
        assert source.name == 'RiderBody' and spec['family'] == 'skin'
        state.update(source=source, originalMaterials=material_state(source), originalCharts=charts(source))
        target, report = original(source, rig, spec, level, cfg)
        state['target'] = target
        return target, report

    def preserve(objects):
        assert len(objects) == 1 and objects[0] is state['target']
        target = objects[0]; source = state['source']
        assert state['originalMaterials'] == material_state(source) == material_state(target), 'Selected shader/map identity changed'
        assert state['originalCharts'] == charts(source), 'Source UVs changed'
        target_charts = charts(target)
        assert target_charts.keys() == state['originalCharts'].keys()
        checks = {name: UV.compare(original_chart, target_charts[name]) for name, original_chart in state['originalCharts'].items()}
        assert [m.as_pointer() for m in target.data.materials] == [m.as_pointer() for m in source.data.materials]
        target['selectedProductionMaterialMode'] = 'ORIGINAL_SELECTED_SKIN_UV_MATERIALS_MAPS'
        skin_bytes = sum(row['residentRGBA8MipBytes'] for row in state['originalMaterials']['images'].values())
        other_families = {r['family'] for r in config['objects'].values()}-{'skin'}
        per_family = sum(UV.rgba8_mip_bytes(config['textures'][name], config['textures'][name]) for name in ['albedo', 'normal', 'orm'])
        total = skin_bytes+len(other_families)*per_family
        assert total <= config['textures']['maximumResidentMiB']*1048576
        state['receipt'] = {'mode': target['selectedProductionMaterialMode'], 'selectedMaterialState': state['originalMaterials'],
            'chartChecks': checks, 'sourceCharts': state['originalCharts'], 'targetCharts': target_charts,
            'atlasRepacked': False, 'sourceTexturesResampled': False,
            'skinOriginalMaterialSlots': len(target.data.materials),
            'skinUniqueImageDatablocks': len(state['originalMaterials']['images']),
            'skinActualImageDimensionsRGBA8MipBytes': skin_bytes,
            'otherFamilyPlannedRGBA8MipBytes': len(other_families)*per_family,
            'wholeRiderPlannedRGBA8MipMiB': total/1048576,
            'wholeRiderMaterialPrimitiveEstimate': len(target.data.materials)+sum(1 for r in config['objects'].values() if r['family'] != 'skin'),
            'runtimeAllocationMeasured': False, 'actualCompleteRiderTextureSetAssembled': False,
            'limits': 'Original chart boundaries/area and texture dimensions preserve selected texel allocation. Geometry, rendered sampling/shading, real GPU residency, whole-scene timing and device quality still need actual qualification.'}

    engine.simplify = simplify; engine.unwrap_family = preserve
    engine.main()
    out = Path(args[1]); report_path = out/'production.json'; report = json.loads(report_path.read_text())
    assert state.get('receipt') and report['authoredFamilies'] == ['skin']
    report.update(baseRecipeSHA256=report['recipeSHA256'], recipeSHA256=sha(__file__),
                  materialPreservation=state['receipt'], preserveSelectedMaterialFamilies=['skin'],
                  requiresFamilyBake=False, materialDelivery='ORIGINAL_SELECTED_SKIN_MAPS_ALREADY_PRESENT',
                  policySHA256=sha(HERE/'input.json'))
    report_path.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({'skinMaterialPreservation': state['receipt'], 'acceptedArt': False}), flush=True)


if __name__ == '__main__': main()
