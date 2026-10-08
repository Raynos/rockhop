"""Bounded read-only inspection of the frozen author01 boot setup.

Reads the saved native and immutable source. No fit, bake, native save or body edit.
The only output is the requested setup/source-cut evidence JSON.
"""
import hashlib
import json
from pathlib import Path
import sys

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[4]
SOURCE = ROOT/'assets/blender/hero-remaster/rider/finish-2026-10-05/wardrobe/data/prep02/boots/cleaned-donor.npz'
AUTHOR = ROOT/'harness/out/rider-rebuild/production-boots01/authored01'
NATIVE = AUTHOR/'author-checked-appearance-pending.blend'
CONTROL = ROOT/'assets/blender/rider-rebuild/production-boots01/controls.json'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
arguments = sys.argv[sys.argv.index('--')+1:]
assert len(arguments) == 1
out = Path(arguments[0]).resolve()
assert not out.exists() and out.is_relative_to(ROOT/'docs/evidence/rider-rebuild/production-boots01')
before_native, before_source = sha(NATIVE), sha(SOURCE)
assert before_native == '2fa8cb66e31ee8f43b2437ea889de6142f7d53efbb88422546a2835e9b63c958'
assert before_source == '9849de6444632c2dcd1e1d76fda42ac27a7cbe8c7d2c0263ab2082e24b94777f'
config = json.loads(CONTROL.read_text())
bpy.ops.wm.open_mainfile(filepath=str(NATIVE))
lattices = [o for o in bpy.data.objects if o.type == 'LATTICE']
assert len(lattices) == 1
cage = lattices[0]
co = np.array([tuple(p.co) for p in cage.data.points])
deformed = np.array([tuple(p.co_deform) for p in cage.data.points])
matrix = np.array([tuple(row) for row in cage.matrix_world])
world = np.einsum('ij,nj->ni', matrix, np.column_stack([co,np.ones(len(co))]), optimize=False)[:,:3]
low, high = np.array(config['authoring']['sourceLattice']['bounds'])
co_low, co_high = co.min(0), co.max(0)
correct_scale = (high-low)/(co_high-co_low)
correct_location = low-correct_scale*co_low
body = bpy.data.objects['RiderBody']
assert not body.hide_render and not body.hide_viewport
body_v = np.array([tuple(v.co) for v in body.data.vertices])
source = dict(np.load(SOURCE))
selection = np.load(AUTHOR/'source-selection.npz')
removed = selection['removedHiddenShaftFloorOriginalDenseFaceRows']
points = source['vertices'][source['faces'][removed]]
centers = points.mean(1)
upper = (centers[:,0] < .38) & (centers[:,1] > -.22)
candidate_rows = removed[upper]
tree = BVHTree.FromPolygons([Vector(p) for p in source['vertices']], source['faces'].tolist(), all_triangles=True)
# Two fixed original-source viewing directions diagnose source selection only.
# A removed triangle that is a first visible hit is an exterior deletion witness.
visible_removed = []
for label, camera in [('original-lateral', np.array([0.,.2,3.5])),
                      ('original-toe-threequarter', np.array([-3.,1.4,2.7]))]:
    sampled = candidate_rows[np.linspace(0,len(candidate_rows)-1,min(512,len(candidate_rows)),dtype=int)]
    witnesses = []
    for row in sampled:
        center = source['vertices'][source['faces'][row]].mean(0)
        direction = center-camera
        length = float(np.linalg.norm(direction))
        direction /= length
        hit, normal, first_row, distance = tree.ray_cast(Vector(camera),Vector(direction),length+.0001)
        if first_row == int(row):
            witnesses.append({'originalDenseFaceRow':int(row),'sourceCenter':center.tolist(),
                              'originalSourceVertices':source['vertices'][source['faces'][row]].tolist(),
                              'rawOriginalCornerUV':source['originalCornerUV'][row].tolist()})
    visible_removed.append({'view':label,'sampledRemovedUpperFaces':len(sampled),
                            'firstVisibleRemovedUpperFaces':len(witnesses),'examples':witnesses[:12]})
report = {'accepted':False,'status':'READ_ONLY_AUTHORED_SETUP_DIAGNOSIS',
          'inspectionRecipeSHA256':sha(__file__), 'native':{'path':str(NATIVE),'sha256':before_native},
          'source':{'path':str(SOURCE),'sha256':before_source},
          'lattice':{'name':cage.name,'resolution':[cage.data.points_u,cage.data.points_v,cage.data.points_w],
                     'actualUndeformedLocalBounds':[co_low.tolist(),co_high.tolist()],
                     'actualUndeformedWorldBounds':[world.min(0).tolist(),world.max(0).tolist()],
                     'declaredDesiredSourceBounds':[low.tolist(),high.tolist()],
                     'currentObjectScale':list(cage.scale),'currentObjectLocation':list(cage.location),
                     'correctObjectScaleForActualCoDomain':correct_scale.tolist(),
                     'correctObjectLocationForActualCoDomain':correct_location.tolist(),
                     'sourceUnitDisplacementToCoFactor':(1/correct_scale).tolist(),
                     'originalCo':co.tolist(),'authoredCoDeform':deformed.tolist()},
          'removedOriginalDenseFaces':len(removed),'removedUpperSectorCandidateFaces':len(candidate_rows),
          'finiteVisibleExteriorDeletionWitnesses':visible_removed,
          'completeBodyVisible':True,'bodyVertices':len(body_v),'bodyMinimumZ':float(body_v[:,2].min()),
          'bootMinimumZ':{side:min(v.co.z for v in bpy.data.objects['ProductionSelectedBoot.'+side].data.vertices)
                          for side in ['L','R']},
          'savedNativeAndOriginalSourceBytePreserved':sha(NATIVE)==before_native and sha(SOURCE)==before_source,
          'limits':['Read-only setup/source-cut diagnosis; no native save, fit, bake or acceptance.',
                    'Finite source view witnesses diagnose exterior deletion, not exhaustive source classification.']}
out.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:report[k] for k in ['status','removedUpperSectorCandidateFaces','bootMinimumZ','savedNativeAndOriginalSourceBytePreserved']}))
