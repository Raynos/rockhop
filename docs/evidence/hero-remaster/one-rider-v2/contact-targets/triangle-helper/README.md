# Exact retained-triangle contact helper — unaccepted preparation

The private post-render probe now supports `target.kind: "triangles"` alongside its existing capsule/cylinder targets. This prepares measurements against the actual rounded footpeg and faceted grip geometry retained in the adjacent source audit. It supplies no rider mapping, changes no player or physics path, and accepts no character/contact result. All four real rider contacts remain **UNMEASURED** until the parent reviews the new rig's palm/sole patches and source-to-live target bindings.

`harness/hero-remaster/surface-contacts.mts` reads each rider sample through `SkinnedMesh.getVertexPosition` and `matrixWorld`, after the live renderer has updated the pose, skeleton and attached bind inverse. It reads rigid bike target vertices through the live `Mesh.getVertexPosition` and `matrixWorld` exactly once. The owning bike `frame` is an identity/ancestry guard; its transform must not be applied a second time. Triangle targets support actual nonuniform world transforms; existing primitive targets continue to reject nonuniform scale and shear.

## Explicit source-to-live binding

Each triangle target requires all of these fields. There is no implicit correspondence or nearest-bone inference.

- `mesh` and `frame`: separate exact child-path/name locators relative to the live bike root; the mesh must be a descendant of the selected frame.
- `geometrySHA256`: `runtimeRigidSurfaceSHA256(actualLiveMesh)`, covering its actual positions and indexing after loader merge/conditioning. Skinned targets and position morph targets are unsupported and become unmeasured.
- `source`: exact consumed GLB `assetSHA256`, source `nodeIndex`, `meshIndex`, `primitiveIndex`, and retained `triangleOrdinals`. These ordinals refer to that source primitive's accessor ordering, in its source node frame.
- `runtimeTriangleOrdinals`: an explicit separate correspondence array of equal length. It refers to the selected live mesh's actual index buffer or nonindexed consecutive triplets. The retained source indices in `fits/` or `pegs/` are **not** automatically valid live indices.
- `bindingReviewed: true`, `bindingReviewAuthority: "parent"`, and a concrete `evidence` reference. The booleans record an external review; this helper cannot establish correspondence from hashes alone.
- `closure: "open" | "closed"`, `closedVolumeReviewed`, and `weldToleranceM` (for closed checks, 1e-9 through 1e-4 metres). A closed volume needs a separate review of its simple, non-self-intersecting shape.

The manifest still pins actual consumed rider and bike bytes. Preparation freezes the mapping. Sampling rejects moved/replaced mesh identities, changed frame ancestry, hidden meshes/ancestors, geometry replacement, altered rigid positions/index values (including writes that omit `needsUpdate`), or a newly added target morph. Rigid pose transforms may change normally. No runtime mapping is supplied by this checkpoint.

## Report semantics

For each posed rider sample, nearest target distance is the exact point-to-retained-triangle distance. The report records the nearest runtime triangle ordinal, barycentric coordinates, closest world point, geometric face normal, sampled unsigned gap and opposing-normal mismatch. At edges/corners or equidistant faces, orientation uses the first nearest face's normal; it is not a smoothed corner normal.

Closed patches must be a single connected edge-manifold shell, with opposite edge incidence, no boundary or degenerate triangles under the specified positional weld, and positive signed volume. World-frame mirroring reverses winding and makes the contact unmeasured. Solid-angle winding distinguishes inside from outside; ambiguous classification becomes unmeasured. Signed negative distance and sampled penetration are available only after these checks and the recorded volume review. These checks do not certify absence of self-intersections or overlapping shells.

Open patches retain `minimumAbsoluteSurfaceGapM` and nearest-face `minimumSidedDistanceM` / `maximumSidedDistanceM`. Their `minimumSignedDistanceM`, `maximumSignedDistanceM` and `maximumSampledPenetrationM` are **null**, `penetrationStatus` is **unmeasured**, and `penetrationLimit` explains that they enclose no volume. Being below an open tooth triangle does not imply volumetric penetration or a pass.

Closed multi-component collections are conservatively rejected. A footpeg platform plus separate teeth therefore needs deliberate component handling before any union-volume claim; an open collection can already measure unsigned surface gaps without claiming volume penetration. The current full/LOD source platforms each pass the closure test as individual components. The twenty single-triangle teeth on each LOD asset fail closure and correctly retain open semantics.

Rider triangle lattice sampling and maximum spacing are unchanged. This is sampled point-to-surface measurement, not continuous mesh collision, intersection-free animation proof, complete penetration depth or image-quality acceptance. There is no automatic pass flag.

## Integration and validation

The existing private `hero-capture.mts --surface-map FILE` integration already consumes the extended target union through `contact-browser.mts`. Call preparation only after the live tier and conditioned geometry settle; sample only at the existing post-render stage, using the rendered scene as rider patch root and the live bike root as target root. Maximum lean and front/rear landing runs must retain the complete input prefix and matched physics traces, as documented in the prior contact integration checkpoint. A rig/tier change invalidates the binding and requires a new reviewed manifest.

The CPU unit suite verifies nearest face/edge/corner and barycentrics, closed inside/outside/on-surface distances, missing/reversed/duplicated/disconnected shells, nonidentity bind/world transforms, real bone deformation, position morphs, moving and nonuniformly scaled rigid targets, stale hashes, source-to-live mapping separation, frozen definitions, in-place geometry writes, and mirrored closed winding. It also hashes the actual four public Rookie/Pro full/LOD GLBs against the retained source peg reports, validates their individual platform components, and checks every LOD tooth triangle's open-sided distance. Those are source-geometry tests, not live rider contact results.

Actual final commands and source digests are in `validation.json`. No new browser, GPU, render, rig, historical hand shell or player asset was created in this round. The earlier guarded capture remains baseline evidence with four unmeasured contacts; it does not prove a triangle mapping.
