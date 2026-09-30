# Reuse the already-resident model decoder

The hero renderer and C1 tug statically import production GLTFLoader and
MeshoptDecoder. Coast and Alpine dynamic imports therefore create async
wrappers without producing a lazy chunk. Use the resident imports while
keeping demand-driven course GLB fetching/parsing and all ownership guards.
Menu/Garage does not gain a course decoding operation.

Nine Coast loader tests and eleven botanical integration tests pass,
including required-map failure, ownership of partial/late resources, abort,
original-scene fallback and borrowed-neutral texture lifetime. App typecheck,
scoped source lint and fresh normal build pass. The [required partial round
gate](round-gate.json) passes14/14: cold hook boot, exact Rookie/Pro clears,
crash and instant restart, player bundle697.30KiB under unchanged700KiB.
The prior normal round measured697.51KiB. These are code-size findings,
not isolated loading/frame-time improvements or a phone qualification.

An initial incorrect test-path filter found no tests; it supplies no pass.
The actual test commands use the two leaf-specific Vitest configs under
assets/blender/course-kits/{coast-harbor,alpine-trees}/.
