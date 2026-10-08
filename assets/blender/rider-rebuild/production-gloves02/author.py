"""One explicit surface-region glove construction under a parent CPU2 lease.

Save both editable shells first, then each hand with selected-shaped features,
then complete native meshes/fields/UV/action BEFORE loading dense appearance.
No panel rays, nearest fallback, tip labels or fitting solver is used.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

import bpy
import bmesh
import numpy as np

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from region_geometry import duplicate_inset_extrude, seam_edge_geometry
from appearance import align_dense, bake, donor_material, mesh_object, motion, save_checkpoint

DIGITS = ('pinky', 'ring', 'middle', 'index', 'thumb')
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
unit = lambda p: np.asarray(p) / np.linalg.norm(p)


def body_signature(body, rig):
    h = hashlib.sha256()
    for v in body.data.vertices:
        h.update(struct.pack('<3f', *v.co))
        for g in v.groups: h.update(struct.pack('<If', g.group, g.weight))
    for p in body.data.polygons:
        h.update(struct.pack('<' + 'I' * len(p.vertices), *p.vertices))
    for bone in rig.data.bones:
        h.update(bone.name.encode())
        h.update(struct.pack('<16f', *(x for row in bone.matrix_local for x in row)))
    return h.hexdigest()


class HandAuthor:
    def __init__(self, side, hand, body, rig):
        self.side, self.hand, self.body, self.rig = side, hand, body, rig
        self.names = body['jointNames'].tolist()
        self.lookup = {name: i for i, name in enumerate(self.names)}
        self.wrist = self.head('DEF-hand.' + side)
        self.forward = unit(self.head('DEF-f_middle.01.' + side) - self.wrist)
        self.radial = self.head('DEF-f_index.01.' + side) - self.head('DEF-f_pinky.01.' + side)
        self.radial = unit(self.radial - self.forward * np.dot(self.radial, self.forward))
        self.dorsal = unit(np.cross(self.radial, self.forward)) * (1 if side == 'R' else -1)
        vertices, faces = hand['vertices'], hand['faces']
        normals = np.zeros_like(vertices)
        area = np.cross(vertices[faces[:, 1]] - vertices[faces[:, 0]], vertices[faces[:, 2]] - vertices[faces[:, 0]])
        for corner in range(3): np.add.at(normals, faces[:, corner], area)
        normals /= np.linalg.norm(normals, axis=1)[:, None]
        self.normals = normals
        back = np.clip(normals @ self.dorsal, 0, 1)
        palm = np.clip(-normals @ self.dorsal, 0, 1)
        longitudinal = (vertices - self.wrist) @ self.forward
        distal_taper = 1 - .20 * np.clip((longitudinal - .15) / .05, 0, 1)
        ease = (.0016 + back * .0018 + palm * .0007) * distal_taper
        self.scaffold = vertices + normals * ease[:, None]
        self.vertices, self.faces, self.fields, self.full_fields, self.parts = [], [], [], [], []
        self.features = []
        self.append('tailored-shell', self.scaffold, faces, hand['fourCoefficients'], hand['fullCoefficients'])

    def head(self, name):
        return self.body['jointHeads'][self.lookup[name]]

    def tail(self, name):
        return self.body['jointTails'][self.lookup[name]]

    def chain(self, digit):
        stem = 'thumb' if digit == 'thumb' else 'f_' + digit
        return [f'DEF-{stem}.{i:02d}.{self.side}' for i in (1, 2, 3)]

    def append(self, name, vertices, faces, fields, full_fields):
        start = len(self.vertices)
        self.vertices.extend(np.asarray(vertices).tolist())
        self.faces.extend([[int(v) + start for v in face] for face in faces])
        self.fields.extend(np.asarray(fields).tolist())
        self.full_fields.extend(np.asarray(full_fields).tolist())
        self.parts.extend([name] * len(faces))
        self.features.append({'name': name, 'vertices': len(vertices), 'faces': len(faces)})

    def construct_regions(self, regions):
        for spec in regions:
            v, f, four, full, seams, receipt = duplicate_inset_extrude(
                self.scaffold, self.normals, self.hand['fourCoefficients'],
                self.hand['fullCoefficients'], self.hand['faces'], spec)
            self.append(spec['name'], v, f, four, full)
            self.features[-1].update(receipt)
            # Narrow textured stitch piping is modeled along actual mesh edges.
            # Ribs themselves are sculpted in the duplicated connected region.
            if not spec['ribCount']:
                self.append(spec['name'] + '-sewn-edge', *seam_edge_geometry(seams, .00023, self.dorsal))
        cuff = [(self.scaffold[a], self.scaffold[b], self.hand['fourCoefficients'][a],
                 self.hand['fourCoefficients'][b], self.hand['fullCoefficients'][a],
                 self.hand['fullCoefficients'][b]) for a, b in self.hand['cuffBoundaryEdges']]
        self.append('selected-cuff-lip', *seam_edge_geometry(cuff, .00115, self.dorsal))

    def build_object(self, out, unwrap=False):
        name = 'GloveProduction.' + self.side
        old = bpy.data.objects.get(name)
        if old: bpy.data.objects.remove(old, do_unlink=True)
        obj = mesh_object(name, self.vertices, self.faces)
        full = np.asarray(self.full_fields)
        inherited = np.asarray(self.fields)
        assert np.max(abs(full.sum(1) - 1)) < 1e-10
        assert np.max(abs(inherited.sum(1) - 1)) < 1e-10
        order = np.argsort(-inherited, axis=1, kind='stable')[:, :4]
        four = np.zeros_like(inherited)
        np.put_along_axis(four, order, np.take_along_axis(inherited, order, axis=1), axis=1)
        removed = 1 - four.sum(1)
        four /= four.sum(1)[:, None]
        for i, bone_name in enumerate(self.names):
            ids = np.flatnonzero(four[:, i] > 0)
            if len(ids):
                group = obj.vertex_groups.new(name=bone_name)
                for vertex in ids: group.add([int(vertex)], float(four[vertex, i]), 'REPLACE')
        mod = obj.modifiers.new('SharedActual75', 'ARMATURE'); mod.object = self.rig
        obj.parent = self.rig
        # Native master retains complete shared75 fields on the same mesh;
        # ordinary deform groups hold FOUR. Missing attributes mean exact zero.
        obj['full_field_joint_names'] = json.dumps(self.names)
        for i, bone_name in enumerate(self.names):
            if np.any(full[:, i]):
                field_attribute = obj.data.attributes.new(name='FULL::' + bone_name, type='FLOAT', domain='POINT')
                field_attribute.data.foreach_set('value', full[:, i].astype(np.float32))
        obj['selected_source'] = 'painted.glb:890f8693256347156c20f82a62dd79e2145cf511e7a85eb5239089644a20bfea'
        obj['production_status'] = 'UNACCEPTED_REGION_CONSTRUCTION'
        obj['hand_side_independently_constructed'] = self.side
        obj['appearance_chirality'] = 'REFLECTED_SELECTED_RIGHT_DONOR' if self.side == 'L' else 'SELECTED_RIGHT_DONOR'
        attr = obj.data.attributes.new(name='AuthoredRegion', type='INT', domain='FACE')
        unique = list(dict.fromkeys(self.parts))
        attr.data.foreach_set('value', [unique.index(part) for part in self.parts])
        obj['authored_region_names'] = json.dumps(unique)
        bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True); bpy.context.view_layer.objects.active = obj
        bm = bmesh.new(); bm.from_mesh(obj.data)
        bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces)); bm.to_mesh(obj.data); bm.free()
        if unwrap:
            bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.uv.smart_project(angle_limit=np.radians(58), island_margin=.018)
            bpy.ops.object.mode_set(mode='OBJECT')
            obj.data.uv_layers.active.name = 'SelectedBakeUV'
        uv = np.empty((len(obj.data.loops), 2), dtype=np.float32) if unwrap else np.empty((0, 2), dtype=np.float32)
        if unwrap: obj.data.uv_layers.active.data.foreach_get('uv', uv.ravel())
        fields_path = out / (name + '-fields.npz')
        np.savez_compressed(fields_path, vertices=np.asarray(self.vertices),
                            fullCoefficients=full, inheritedFourCoefficients=inherited,
                            fourCoefficients=four, removedFourMass=removed,
                            jointNames=np.asarray(self.names), partNames=np.asarray(unique),
                            polygonRegionIds=np.array([unique.index(part) for part in self.parts]),
                            faceVertexIds=np.array([v for face in self.faces for v in face], dtype=np.int32),
                            faceOffsets=np.r_[0, np.cumsum([len(face) for face in self.faces])],
                            triangleCornerUV=uv)
        return obj, {'vertices': len(obj.data.vertices), 'polygons': len(obj.data.polygons),
                     'authoredFeatures': self.features, 'textures': {},
                     'sharedArmature': self.rig.name, 'nativeFullFieldAttributes': [a.name for a in obj.data.attributes if a.name.startswith('FULL::')], 'maxFourReductionMass': float(removed.max()),
                     'fields': {'path': str(fields_path.relative_to(ROOT)), 'sha256': sha(fields_path)},
                     'newUV': obj.data.uv_layers.active.name if unwrap else None}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('out')
    parser.add_argument('--stage', choices=('geometry', 'bake', 'all'), default='geometry')
    parser.add_argument('--bake-resolution', type=int, choices=(1024, 4096), default=1024)
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
    out = Path(args.out).resolve()
    assert out.is_relative_to(ROOT / 'harness/out/rider-rebuild/production-gloves02')
    records = json.loads((HERE / 'inputs.json').read_text())
    paths = {key: ROOT / value['path'] for key, value in records.items()}
    for key, record in records.items(): assert sha(paths[key]) == record['sha256'], ('Changed input', key)
    regions = json.loads((HERE / 'face-regions.json').read_text())
    source_files = {p.name: sha(p) for p in HERE.glob('*.py')}
    source_files.update({'inputs.json': sha(HERE / 'inputs.json'), 'face-regions.json': sha(HERE / 'face-regions.json')})
    if args.stage == 'bake':
        report = json.loads((out / 'geometry-report.json').read_text())
        assert report['sourcePins'] == records and report['sourceFiles'] == source_files
        native = ROOT / report['native']['path']; assert sha(native) == report['native']['sha256']
        bpy.ops.wm.open_mainfile(filepath=str(native))
    else:
        assert not out.exists(); out.mkdir(parents=True)
        bpy.ops.wm.open_mainfile(filepath=str(paths['nativeMaster']))
    body_obj, rig = bpy.data.objects['RiderBody'], bpy.data.objects['RiderSkeleton']
    assert len(body_obj.data.vertices) == 10582 and len(rig.data.bones) == 75
    before = body_signature(body_obj, rig)
    arrays = np.load(paths['nativeArrays'])
    if args.stage != 'bake':
        rig.animation_data_clear()
        for bone in rig.pose.bones: bone.matrix_basis.identity()
        bpy.context.view_layer.update()
        authors = {side: HandAuthor(side, np.load(paths['hand' + side]), arrays, rig) for side in ('R', 'L')}
        report = {'acceptedArt': False, 'status': 'BILATERAL_SCAFFOLD_PRIVATE_UNFINISHED',
                  'sourcePins': records, 'sourceFiles': source_files, 'hands': {},
                  'textureResolution': {'selectedPaintSource': 4096, 'firstLookDerivative': 1024, 'final4KMasterBake': 'NOT_EXECUTED'},
                  'bodyAndRestBefore': before,
                  'limits': ['Scaffold is unfinished and not selected-glove delivery.',
                             'Underlying native hand moving anatomy remains unaccepted.']}
        for side, author in authors.items():
            _, report['hands'][side] = author.build_object(out)
        save_checkpoint(out, 'unfinished-shells.blend', report, 'unfinished-shells.json')
        for side, author in authors.items():
            assert regions['sides'][side]['inputPin'] == records['hand' + side]
            author.construct_regions(regions['sides'][side]['regions'])
            _, report['hands'][side] = author.build_object(out, unwrap=True)
            report['hands'][side].update({'actualTargetGeometry': records['hand' + side],
                                          'donorAppearanceReflected': side == 'L',
                                          'thumbRootIncludesFace279': regions['sides'][side]['thumbRootIncludesFace279']})
            report['status'] = 'AUTHORED_REGIONS_' + side + '_COMPLETE_PRIVATE_UNACCEPTED'
            assert body_signature(body_obj, rig) == before
            save_checkpoint(out, 'authored-regions-' + side + '.blend', report, 'authored-regions-' + side + '.json')
        report['bodyAndRestAfter'] = body_signature(body_obj, rig)
        assert report['bodyAndRestAfter'] == before
        report['reviewAction'] = motion(rig, json.loads(paths['actualDigitControls'].read_text()))
        bpy.context.scene.frame_start = 1; bpy.context.scene.frame_end = 80; bpy.context.scene.frame_set(1)
        report['status'] = 'BOTH_REGION_GLOVES_FIELDS_UV_ACTION_SAVED_BEFORE_DENSE_BAKE'
        report['limits'] = ['Selected dense material transfer and played appearance are pending.',
                            'No fully dressed art, finite handlebar grip or mobile acceptance.',
                            'Native hand articulation remains subject to parent moving review.']
        save_checkpoint(out, 'authored-geometry.blend', report, 'geometry-report.json')
    else:
        assert before == report['bodyAndRestAfter']
    if args.stage == 'geometry': return
    report['geometryNative'] = dict(report['native'])
    source = np.load(paths['sourceDetailCage']); dense = np.load(paths['denseSelected'])
    material, color, mr = donor_material(paths)
    texture_out = out / ('first-review-1024' if args.bake_resolution == 1024 else 'master-4096')
    assert not texture_out.exists(); texture_out.mkdir()
    for side in ('R', 'L'):
        author = HandAuthor(side, np.load(paths['hand' + side]), arrays, rig)
        target = bpy.data.objects['GloveProduction.' + side]
        donor = align_dense(author, source, dense, material)
        report['hands'][side]['textures'] = bake(bpy.context.scene, target, donor, texture_out, material, color, mr, args.bake_resolution)
        report['status'] = 'SELECTED_BAKE_' + str(args.bake_resolution) + '_' + side + '_SAVED'
        assert body_signature(body_obj, rig) == before
        save_checkpoint(texture_out, 'bake-progress.blend', report, 'bake-progress.json')
    report['status'] = 'SELECTED_TEXTURED_REGION_GLOVES_FOR_PARENT_PLAYED_REVIEW'
    report['textureResolution']['executedBake'] = args.bake_resolution
    if args.bake_resolution == 4096: report['textureResolution']['final4KMasterBake'] = 'EXECUTED_UNACCEPTED'
    report['limits'] = ['Unaccepted until parent judges complete selected textured outfit in motion.',
                        'Bake coverage, wrong-face contamination and seam continuity require actual inspection.',
                        '1024 first-review textures do not satisfy a final4K master.',
                        'No finite handlebar grip, mobile, release or art gate is granted.']
    save_checkpoint(texture_out, 'selected-articulated-gloves.blend', report, 'report.json')
    for key, record in records.items(): assert sha(paths[key]) == record['sha256'], ('Input changed', key)


if __name__ == '__main__': main()
