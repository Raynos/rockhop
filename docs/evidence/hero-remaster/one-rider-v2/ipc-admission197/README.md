# IPC capability admitted; geometry remains unaccepted

The isolated ARM64 CPython 3.11 wheel `ipctk==1.6.0` passes CPU admission.
Its SHA256 is
`e2734de7e94fa40ffe8da6aaac1d6d5c5aa9456c64dd777777f40e10f1cf5a7c`.
The wheel contains the MIT license and original copyright notice; the
private wheel and complete provenance are retained. NumPy 2.4.6 and SciPy
1.17.1 are pinned. The original unimate environment was not modified.

[IPC Toolkit](https://github.com/ipc-sim/ipc-toolkit) supplies contact
potentials, derivatives and CCD, and explicitly omits a physics solver.
[Python installation](https://ipctk.xyz/build/python.html) distinguishes
release wheels from source builds. No source compilation was attempted.
The current [Python API](https://ipctk.xyz/python-api/index.html) and
[CCD contract](https://ipctk.xyz/python-api/ccd.html) require an
intersection-free start for a meaningful collision-free step. This is
collision infrastructure, not a guarantee of acceptable anatomy or motion.

The two-triangle demo has clear endpoints and a crossing in the middle.
Actual vertex–triangle/edge–edge CCD returns 0.39990234375; the static step
is 1.0. Barrier energy and gradient are nonzero, the Hessian is finite,
and the directional gradient matches finite differences with relative
error 9.76e-9. The API return documentation for `is_step_collision_free`
contains a contradictory sentence; fixtures establish True for clear
static motion and False for crossing motion.

Actual source185 is pinned at `ffb9ec5a…4281c5`, failed196 at
`5b54029e…336f27`; full hashes and input reader hashes are in JSON.
Independent node-world reconstruction agrees exactly. Joint all-five
XYZ deduplication yields 72,527 vertices, 217,443 edges and 144,883 faces.
The default source preflight finds no intersections, no zero-distance
contacts among 78,748 FV/EE candidates, and no degenerate faces. The
minimum area is 4.36754e-11 m². This agrees with source185's zero strict
crossings after its hood index repair; earlier source184 defects are not
silently inherited as a source185 assumption.

Exactly 46 released physical vertices touch exactly the frozen 168 faces.
The native static filter preserves every active stencil from the complete
79,139-candidate swept set: 439 queries, 81 FV and 358 EE. There are 61 CCD
events. The filtered and default full-surface safe prefix both equal
0.04752707481384277. A separate full-surface query verifies that prefix
clear and the full196 transit unsafe. All 44 frozen strict endpoint pairs
have native collision-event witnesses; all 44 are strict-clear at source.
The static full-surface step is 1.0. Conservative rescaling is 0.8,
tolerance 1e-8, maximum iterations 1,000,000, minimum distance zero.
This is a conservative safe step, not an exact mathematical first impact.

The actual-source local barrier at dhat=1e-4 m is finite and inactive
(energy and gradient zero); minimum source distance among local swept
stencils is 1.56480 mm. The nonzero derivative admission comes from the
triangle demo. Native shared-ID adjacency remains sewn; separate tests
for adjacent folded faces, inversion, boundary conservation, rest normals,
and moving art remain necessary. The final CPU recipe took 55.37 seconds,
two threads, with anonymous memory 41.13–41.59 GB. No geometry was created.

One possible next experiment is a source-only local 3D shell energy solve:
46 physical vertices / 138 free XYZ DOFs, exact source168 incidence, and
the original 78-vertex perimeter fixed byte-exactly. All other source
geometry, hood/head identity, cuffs, right side, lower garment, attributes
and rig remain fixed. Use source-relative membrane strain and dihedral
bending, IPC barrier derivatives, and native CCD to cap every line-search
step. A new explicit anatomical objective and barrier activation distance
must be registered by the parent before that single experiment starts.
No retired cage, tube, ARAP, harmonic field, contact projection or Y-only
hard lift is part of this proposal. Start feasibility is admitted; reaching
the attachment goal inside this small domain is unproved. Frozen196's
38.397× stretch and nine reversed normals, plus the fixed-boundary path
lower bounds, may require a separately authorized larger source domain or
retopology. This admission does not authorize that expansion or any solver.
