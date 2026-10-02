Status: PARKED / RETIRED FAMILY. No geometry authorization.
Parent round182 invokes last resort at15; this document is failure diagnosis only.

# Q183 read-only proposal — fitted contours and oriented shared seams

No mesh, model, Blender, GPU or render has run. This proposes one further
quad approach trial only if the parent subsequently authorizes it. Source
and Q182 geometry remain frozen. Creating the new directories initially
failed with `No space left on device`; the consequent receipt write also
failed. No existing jobs or files were evicted. The parent must classify that
setup failure against the family limit before any new geometry authorization.

Read-only Q182 measurements show the cause directly. Each torso row had64
controls; rows1–4 had only56,40,43,27unique Float32 positions, respectively,
with8,24,21,37zero adjacent edges. Their largest edges were66.3,87.0,157.4,
188.3mm. The nearest-source-point selection reused controls and skipped
large contour arcs. The64-node hem row was unique but lay on the same actual
156-node cut polyline as its exact boundary, creating a zero-width zipper.
Hood/hem order was reversed according to a geometric angle convention rather
than the neighboring donor's directed face edges. These are compiler/control
defects; the exact donor cycles are not their cause.

Use one smooth, positive, periodic radial B-spline contour per complete
measured torso section in a shared anatomical chart. Fit the source section's
macro outline with positive radius and smooth curvature constraints, and
constrain front/back/lateral extrema to their measured source values. Do not
choose source vertices as output controls. Sample the fitted function at
strictly increasing fixed angles with a consistent anatomical front anchor.
Positive radius makes distinct angles distinct in real arithmetic; verify
Float32 uniqueness separately. The clipped .36/.48m window widths are not
fitting targets. Above the source hood's posterior ownership boundary, use
the actual nonplanar hood curve rather than fitting missing back sections.

Maintain the exact307hood,65left/62right cuff and156design-cut nodes in their
actual connectivity order. Derive each required new boundary direction as
the reverse of the existing donor's one-face directed edge. Preserve every
source point; never reorder by angle, skip nodes, or classify interior points
by height. At collar and hem, create the neighboring new row a positive
distance into the upper garment, rather than resampling the same curve.
Start with a20mm upward hem offset and20mm downward collar offset, blended
into source-guided body contours; these are declared new controls, not an
accepted geometric setting. Verify local strip width and nonintersection
before using the controls. No unnecessary coincident boundary strips.

The torso and both sleeves belong to one indexed half-edge graph. Define
side-window corner/edge sequences once and let both incident patches reuse
the same node arrays with opposite edge directions. Propagate orientation
across all face adjacencies and reject conflicts before geometry/export.
Sleeve sections use measured anatomical arm directions and fitted source
section contours, with explicit axilla controls and gap tests; they are not
independent transported tubes or repaired old cap meshes. Local triangles
and valence poles may handle donor counts, but do not collapse nodes to
match parity. Triangulate transitions against the actual ordered boundaries
and inspect every triangle, including dense donor-adjacent transition cells.

Before mesh instantiation, require64/64unique Float32 controls on every new
regular ring, positive adjacent control distance, monotone anatomical phase,
no repeated consecutive source boundary node, and positive distance between
successive new rows. Target minimum new regular-ring edge length1mm and
neighbor-row distance2mm; exact dense donor edges have a separately reported
inherited range and are never silently moved to satisfy these targets.
Reject zero-width strips. Preflight every proposed diagonal in Float32;
minimum triangle area must exceed1e-12m², with per-region minimum area,
angle/aspect and edge-length distributions disclosed. Orientation must give
one face per side/opposite directions at every physical donor/shared seam.

After one successful control/graph preflight, instantiate one fresh cage and
export it once. Audit actual assembled Float32 topology: no degenerate faces,
nonmanifold edges or winding conflicts; complete hood/cuff/hem pairing;
preserved237hood opening; no ghost cuff components; injective final source
correspondence and source-edge cut ancestry. Run conservative AABB/radius
strict zero/one-shared crossings across new and retained cloth, explicitly
retaining inherited donor defects and predicate limits. Only a stable literal
export can proceed to the exact179gray/PBR CPU films. A failed preflight or
export is frozen and counted; no automatic control repair or cosmetic loop.

This is a construction proposal, not a proof of anatomy, deformation or
appearance. Head/hood/gloves/lower source identity remains protected; no
weights, rig, texture bake or game-ready score is proposed.
