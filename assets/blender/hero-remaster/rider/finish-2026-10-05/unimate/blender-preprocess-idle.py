"""Blender entry point: preserve a deliberately static seated clip and all joints.

Upstream preprocessing assumes training motion and prunes stationary bones /
static ends. A fixed-contact idle input needs those bones and static frames.
Only those preprocessing filters are adapted; canonical math is upstream.
"""
from pathlib import Path
import functools
import runpy
import sys
import bpy

root = Path("/Users/raynos/projects/localai")
runtime = root / "runtime/unimate"
sys.path.insert(0, str(runtime / "blender-deps"))
# Motion's public mathematical modules are pure Python; keep compiled venv
# extensions out of Blender's different Python ABI.
sys.path.insert(0, str(runtime / "motion-pure"))
sys.path.insert(0, str(runtime / "code"))
# Upstream develops against legacy Blender Actions; 5.2 stores curves in a
# slot's channelbag. The single-character importer creates exactly one slot.
def action_fcurves(action):
    for layer in action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                return bag.fcurves
    raise RuntimeError(f"Action has no channelbag: {action.name}")

if not hasattr(bpy.types.Action, "fcurves"):
    bpy.types.Action.fcurves = property(action_fcurves)
from data_process.mesh_animation import preprocess_char as pre
pre.export_asset = functools.partial(pre.export_asset, prune=False, remove_tpose=False, min_frames=1)
pre.process_object = functools.partial(pre.process_object, static_threshold=-1,
                                     activity_threshold=-1, min_frames=1)
args = pre.parse_args()
pre.preprocess_asset(args.char_path, args.output_dir, face_r=args.face_r,
               face_l=args.face_l, body_axis=args.body_axis,
               formats=tuple(args.formats.split(",")),
               keep_intermediate=args.keep_intermediate,
               target_diameter=args.target_diameter, save_vis=args.save_vis,
               apply_clip=args.apply_clip, max_clip_len=args.max_clip_len,
               clip_stride=args.max_clip_len - args.diffusion_max_len)
