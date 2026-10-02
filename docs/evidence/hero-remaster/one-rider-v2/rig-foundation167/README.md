# Frozen rig foundation diagnostic167 — unaccepted

The mapped static V5 uses the same 19-joint rest hierarchy and inverse binds as source34 and immutable C19. All five actual loaded primitives are attached SkinnedMeshes, use the declared canonical skin order, and retain identity mesh/bind transforms. The source rest × inverse-bind residual is **5.940526248693345e-8**; it was measured and retained, not replaced by identity. Raw GLB fields, source hashes, complete joint/mesh hierarchy, literal matrix values and pivot/surface witnesses are in `raw-foundation.json`.

The frozen conservative central torso diagnostic contains **1,423 original body vertices**, from Y0.968 to Y1.43160015818, within ±0.09363374614 of the upper-arm lateral midline, all X included. This intentionally excludes the shoulder joint height and outer lateral shoulder surfaces; it does not classify shoulder influences as forbidden. Literal source vertex IDs, wholly contained triangle IDs, incident triangle IDs and weights are recorded. This region has **zero arm-family influence** in both V5 and source34. All 16 unilateral arm/wrist/grip families give **zero central-core displacement** versus neutral on the actual Three surface. The other bilateral arm controls also give zero. Squat/sit/lean move this core with their torso controls, as expected from the fixture; displacement is not an art pass.

Outside this core, source34 and V5 have 5,773 and 8,971 body vertex rows respectively with positive arm influence. V5 also changes 527 core rest-position rows. These observations neither condemn outer chest/shoulder weights nor establish that the entire torso is sound. Inspect lateral chest/axilla and moving garment failures separately; this core result rules out arm weight leakage only in the explicitly listed frozen region.

Actual Three evaluated all **5,404** fixture samples and independently reconstructed each core surface vertex from raw rest/inverse-bind matrices. Maximum actual/raw affine position difference was **1.1443916996305594e-15 m**; world/local fixture parity was **1.4432899320127035e-15**. Independent NumPy evaluation agrees with every per-frame maximum motion within **3.608224830031759e-16 m**. This is a finite named-world CPU test, not production physics replay or moving appearance/contact approval.

Stock GLTFLoader changed **192 weight lanes** through its documented Float32 normalization, maximum component change **5.960464477539063e-8**. Every loaded position, normal, UV, index and joint-index field was checked against raw GLB; every loaded weight matched the explicit normalization prediction. `prepareHero` did not alter those loaded weight bytes. The source GLBs remain untouched. These statements do not imply arbitrary production constructor conditioning is harmless: stock `GltfRider` invokes `conditionSleeveSkin`; the private `patchNewRiderSource` bypass must remain active when loading this already-conditioned source. The exported metadata carries `rockhopRiderSkinConditioned:1` and the explicit-child-axis flag. This audit evaluates GLTFLoader + `prepareHero` + the controlled fixture, not an instantiated patched `GltfRider`.

The rest matrices are world-aligned; naive transformed +Y is opposite much of the limb chain (upper-arm dot ≈−0.969, thigh dot ≈−0.996). The 14 explicit child directions are independently reconstructed and agree with the actual loaded hierarchy. The private `patchFreshC19Source` is consequently required for production-driver tests, rather than relying on the source +Y basis. Preserve this contract and the original binding; do not reset transforms or rebuild a skeleton to mask an axis error.

Head/neck/spine and shoulder evidence is geometric, not anatomical acceptance. Neck-to-head origin length is 55.825 mm; shoulder-to-upper-arm lengths are 137.025 mm; chest-to-neck is 247.350 mm. Rest joint centers and nearest body/hood/head surface vertices with literal IDs and 15 mm height-band bounds are retained. No identified skin/internal anatomical landmarks or moving rotation/bending views were available to validate those pivots. A pivot's nearest clothing surface is not its anatomical target. Head/neck skin behavior, visible join, shoulder arc, hip/seat shape, source proportions, full-motion gameplay/contact and Garage/device appearance remain unmeasured by this audit.

The existing source has identity mesh scale, joint world rotation determinants +1, Y up, named L limbs at positive Z, and game contact/segment coordinates expressed in metres. The measured head/pelvis origins are Y1.568175/Y0.918 and body bounds are retained. No source unit/basis conversion or binding reset was performed. Canonical-to-native proper mapping metadata remains source provenance; it is not a new conversion applied here.

Reproduce from the repository root (CPU only):

```sh
OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 /Users/raynos/projects/localai/runtime/unimate/.venv/bin/python assets/blender/hero-remaster/rider/one-rider-v2/rig-foundation167/prepare.py
UV_THREADPOOL_SIZE=2 OMP_NUM_THREADS=2 pnpm exec tsx assets/blender/hero-remaster/rider/one-rider-v2/rig-foundation167/evaluate.mts
OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 /Users/raynos/projects/localai/runtime/unimate/.venv/bin/python assets/blender/hero-remaster/rider/one-rider-v2/rig-foundation167/independent.py
OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 /Users/raynos/projects/localai/runtime/unimate/.venv/bin/python assets/blender/hero-remaster/rider/one-rider-v2/rig-foundation167/freeze.py
```

Contact metadata retains ancestor `body-bind04` source-hand matrices and `declaredUniformScale:1.015`; these differ from current C19 hand rest matrices and identity mesh scale. The inspected private adapter uses current captured q0 plus mapped target quaternions, not those ancestral matrices or scale. `contact-metadata-provenance.json` records both; do not reinterpret provenance as live binding or apply the old scale again. Contact correctness remains a parent physics test.

Source/fixture assertions reject changed inputs. Recipe and external adapter/runtime dependency hashes are frozen in `freeze.json`. No art, topology, skeleton, weights, game code, sources, shared tracking documents or GPU state were changed. Parent owns integration and judgment; task-3 retains garment construction.

## Parent integration review — round167

Parent verifies24source/dependency/receipt hashes and independently evaluates
all5,404core samples. The3,088unilateral samples have exact unchanged contributing
joint matrices and actual Three0motion. Independent per-frame motion differs
by<=3.61e-16m. Initial scalar/batched BLAS exact-rounding assertion failed at
2.48e-16m; that computational residual remains recorded separately. Exact input
matrix equality and actual0core motion remain mandatory; no physical threshold
or geometry changed. This narrow core excludes lateral chest/axilla failure.

Do not apply ancestral bind04metadata as current binding. Keep explicit19bone
child-axis mapping and the already-conditioned sleeve bypass in private runtime
tests. Source marker alone does not prove the normal player constructor respects
these controls. Future promotion must preserve this exact adapter behavior in
the real game path and verify moving contacts/appearance, not copy the GLB alone.
No source/weights/bone change or anatomy acceptance. Construction first.
