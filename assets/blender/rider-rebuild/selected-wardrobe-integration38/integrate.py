"""Parent CPU2: transplant only qualified selected wardrobe mesh datablocks.

Original destination objects, material slots, rig, actions, shape keys on the
body/jeans, mask and complete reference remain. Full comparison runs only
after this raw checkpoint, in separate witness processes. No runtime export.
"""
import gc
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import lineage as h

PENDING = 'UNACCEPTED_WARDROBE_INTEGRATION_SAVED_COMPARISON_PENDING'


def rest(rig):
    return [{'name': bone.name, 'parent': bone.parent.name if bone.parent else None,
             'head': list(bone.head_local), 'tail': list(bone.tail_local),
             'matrix': [list(row) for row in bone.matrix_local],
             'useConnect': bone.use_connect, 'useDeform': bone.use_deform} for bone in rig.data.bones]


def groups(obj):
    return [(group.index, group.name, group.lock_weight) for group in obj.vertex_groups]


def integrate(input_path, out, bpy):
    config, target, sleeve, contract = h.read_input(input_path)
    assert config['pins']['integrationRecipe'] == h.pin(__file__)
    assert config['pins']['lineageHelper'] == h.pin(h.HERE/'lineage.py')
    out = Path(out).resolve()
    assert not out.exists() and out.is_relative_to(h.ROOT/'harness/out/rider-rebuild/selected-wardrobe-integration38')
    assert bpy.ops.wm.open_mainfile(filepath=str(h.checked(config['pins']['targetNative'])), use_scripts=False) == {'FINISHED'}
    rig = bpy.data.objects['RiderSkeleton']
    assert rig.matrix_world.is_identity and rest(rig) == contract['nativeRest']['bones']
    assert len(rig.data.bones) == 75
    originals = {obj.name: (obj.as_pointer(), obj.data.as_pointer() if obj.data else None) for obj in bpy.data.objects}
    original_actions = {action.name: action.as_pointer() for action in bpy.data.actions}
    protected = set(target['visibleMeshes'])|{h.REFERENCE}
    assert {obj.name for obj in bpy.context.scene.objects if obj.type == 'MESH' and not obj.hide_render} == set(target['visibleMeshes'])
    assert bpy.data.objects[h.REFERENCE].hide_render
    assert bpy.data.objects['RiderBody']['outfitFullBodyReference'] == h.REFERENCE
    collections = ('objects', 'meshes', 'armatures', 'actions', 'materials', 'images')
    before_ids = {kind: {item.as_pointer() for item in getattr(bpy.data, kind)} for kind in collections}
    destinations = {name: bpy.data.objects[name] for name in h.WARDROBE}
    for obj in destinations.values():
        assert obj.type == 'MESH' and obj.matrix_world.is_identity and not obj.data.shape_keys
        assert obj.animation_data is None and not obj.constraints
    # Appending only these objects loads their required mesh/rig/material IDs;
    # no complete source scene or second complete dressed rider is loaded.
    with bpy.data.libraries.load(str(h.checked(config['pins']['sleeveNative'])), link=False) as (available, loaded):
        assert set(h.WARDROBE) <= set(available.objects)
        loaded.objects = list(h.WARDROBE)
    imported = dict(zip(h.WARDROBE, loaded.objects))
    new_objects = [obj for obj in bpy.data.objects if obj.as_pointer() not in before_ids['objects']]
    assert {obj.as_pointer() for obj in imported.values()} <= {obj.as_pointer() for obj in new_objects}
    assert all(obj.type == 'ARMATURE' or obj in imported.values() for obj in new_objects), 'Unexpected source object dependency'
    for donor_rig in (obj for obj in new_objects if obj.type == 'ARMATURE'):
        assert donor_rig.matrix_world.is_identity and rest(donor_rig) == rest(rig)
    old_meshes, changed = [], {}
    for name, donor in imported.items():
        obj = destinations[name]
        assert donor.type == 'MESH' and not donor.data.shape_keys and donor.animation_data is None
        assert donor.matrix_world == obj.matrix_world and donor.matrix_parent_inverse == obj.matrix_parent_inverse
        assert groups(donor) == groups(obj), ('Selected named group schema changed', name)
        assert len(donor.data.materials) == len(obj.data.materials) > 0
        assert all(mod.type in {'ARMATURE', 'TRIANGULATE'} for mod in donor.modifiers)
        arms = [mod for mod in obj.modifiers if mod.type == 'ARMATURE']
        assert len(arms) == 1 and arms[0].object == rig
        schema = groups(donor)
        # Constructor28 explicitly preserves these original selected slots.
        # Reuse them now; source-vs-final full PBR equality is a later required
        # witness comparison, never inferred from slot count or material names.
        selected_materials = list(obj.data.materials)
        mesh = donor.data
        for index, material in enumerate(selected_materials): mesh.materials[index] = material
        old_meshes.append(obj.data)
        obj.data = mesh
        assert groups(obj) == schema, 'Mesh transplant lost native named group schema'
        changed[name] = {'vertices': len(mesh.vertices), 'polygons': len(mesh.polygons),
                         'sourceGroupNames': [group[1] for group in schema]}
    # Remove only IDs imported by this operation or replaced mesh datablocks
    # that have no remaining users. No global orphan purge touches the master.
    for obj in new_objects: bpy.data.objects.remove(obj, do_unlink=True)
    for mesh in old_meshes:
        if mesh.users == 0 and not mesh.use_fake_user: bpy.data.meshes.remove(mesh)
    for kind in ('armatures', 'actions', 'materials', 'images'):
        data = getattr(bpy.data, kind)
        for item in list(data):
            if item.as_pointer() in before_ids[kind]: continue
            if item.use_fake_user: item.use_fake_user = False
            if item.users == 0: data.remove(item)
    assert set(originals) == {obj.name for obj in bpy.data.objects}
    for name, (object_id, data_id) in originals.items():
        obj = bpy.data.objects[name]
        assert obj.as_pointer() == object_id
        if name not in h.WARDROBE: assert (obj.data.as_pointer() if obj.data else None) == data_id
    assert original_actions == {action.name: action.as_pointer() for action in bpy.data.actions}
    assert rest(rig) == contract['nativeRest']['bones']
    assert all(bpy.data.objects[name].data.as_pointer() == originals[name][1] for name in protected-set(h.WARDROBE))
    del imported, loaded, donor, mesh, old_meshes, new_objects
    gc.collect()
    out.mkdir(parents=True)
    native = out/'UNACCEPTED-selected-dressed-wardrobe38.blend'
    print('WARDROBE38_RAW_SAVE_BEFORE_FULL_COMPARISON', flush=True)
    assert bpy.ops.wm.save_as_mainfile(filepath=str(native), compress=False) == {'FINISHED'}
    with native.open('rb') as stream: assert stream.read(7) == b'BLENDER'
    result = {'acceptedArt': False, 'status': PENDING, 'native': h.pin(native), 'input': h.pin(input_path),
              'recipe': h.pin(__file__), 'sourcePins': config['pins'], 'changedMeshes': changed,
              'visibleMeshes': target['visibleMeshes'], 'protectedValidationPassed': False,
              'geometryGatesPassed': False, 'poseEnclosurePassed': False, 'movingReviewPassed': False,
              'nativeStorage': {'compressed': False, 'reopenVerified': False},
              'limits': ['Data-pointer checks are cheap pre-save guards, not protected geometry/PBR/action success.',
                         'Separate target, source and merged native witnesses must compare all preserved fields.',
                         'Source static clearance is not moving clearance; both-bike and generic envelope, wrist holes and ankle overlap remain parent played gates.',
                         'No jeans/boot geometry edit, runtime export, player promotion or art acceptance.']}
    h.io['write'](out/'pending.json', result)
    print(json.dumps({'status': PENDING, 'native': result['native']}), flush=True)


if __name__ == '__main__':
    import bpy
    args = sys.argv[sys.argv.index('--')+1:]
    assert len(args) == 2, 'integrate.py -- ACTUAL_INPUT FRESH_OUTPUT'
    integrate(Path(args[0]).resolve(), Path(args[1]).resolve(), bpy)
