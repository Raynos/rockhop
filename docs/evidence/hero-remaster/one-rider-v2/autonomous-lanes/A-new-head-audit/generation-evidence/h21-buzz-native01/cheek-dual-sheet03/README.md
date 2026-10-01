# Native tessellation setup failure, unaccepted

Blender5.2.1 returns integer triangle indices from tessellate_polygon. The
older vector lookup raises TypeError before generating any cheek cap. This
is an API setup failure, not evidence of a generator or reducer defect.

Four analytic thickness tests passed. All four native boundaries classify;
the source GLB hash remains exact. No derivative or texture was emitted.
The next run consumes native integer indices with identical selection and
depth constraints, within the existing04:01:29UTC CPU batch ceiling.
See checkpoint-api-failure01.json for immutable recipe and receipt hashes.
