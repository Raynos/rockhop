# Neutral anatomy separated from failed gripping pose

The freshly instantiated CC0 MPFB source retains its unposed native rig and
weights. Only connected hand, palm and proximal wrist surfaces were extracted;
no historical character or failed rider mesh was used. Each neutral hand has
1,668 vertices and 1,656 polygons, with one intentional open 22-edge wrist
loop and no nonmanifold edges beyond that loop. Native weights sum to one
within floating-point tolerance. This is an anatomical template, not a sewn
body or accepted riding pose.

The initial render inherited untransformed MPFB shape keys and displayed
blank crops. Its saved canonical mesh vertices and native weights are valid,
but those original images do not establish appearance. A display-only
correction rebuilt meshes from the frozen NPZs without those keys. Final
verification then found the tri/quad-only NPZ serialization had omitted two
wrist-cut n-gons per hand. Both partial NPZs and that display evidence are
preserved as diagnostic failures.

[Complete neutral evidence](display-complete/README.md) exports **all 1,656
polygons** from the unchanged saved canonical master, retains the identical
vertex positions and weights, and rebuilds a render mesh without inherited
shape keys. Only those complete views should be used to judge neutral anatomy.
No curl, anatomy sculpting, bake or source modification occurred in either
display correction. The neutral original full source and canonical master
remain available and hashed; the full source includes the authoring rig.

The separately sewn fixed-curl derivative has finger-bend intersections.
Neutral anatomy and that failed posing technique have separate verdicts.
Parent visual judgment is pending; zero neutral overlap candidates do not
establish riding contacts or final deformation quality.
