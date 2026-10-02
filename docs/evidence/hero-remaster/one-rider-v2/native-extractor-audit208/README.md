# Native marching-cubes audit — conditional finding

The installed Hunyuan3D 2.1 FlashVDM decoder deliberately changes unqueried
`-10000` voxels into `NaN`. Its marching-cubes extractor passes the resulting
grid directly to scikit-image Lewiner without a finite-grid check or mask.
This can produce nonfinite vertex coordinates. **Whether this caused the
actual native207 assertion remains unassessed here.** No native207 arrays or
diagnostics were supplied to this source-only audit.

The CPU reproduction uses no Torch import, model, GPU, weights or installed
source edits. Exact scalar grids and pre-processing mesh arrays are preserved
in the private NPZ files pinned in `report.json`.

| 12³ sphere fixture | Native vertices | Native faces | Nonfinite vertices | Default Trimesh faces |
| --- | ---: | ---: | ---: | ---: |
| Fully finite | 192 | 380 | 0 | 380 |
| NaN exterior beyond a one-cell scalar halo | 504 | 1,032 | 312 | 228 |
| One NaN voxel | 198 | 392 | 6 | 379 |
| Positive-infinity exterior | 192 | 380 | 0 | 380 |

Default Trimesh processing removes the nonfinite vertex positions in these
fixtures, but the NaN exterior loses 152 faces relative to the fully queried
sphere. A successful finite-mesh export therefore does not demonstrate that
the surface is complete. Positive infinity is different: this fixture kept
positions finite while producing 160 nonfinite normals and 192 nonfinite
values. Do not describe every nonfinite grid entry as a proven NaN-vertex cause.

## Exact source chain

All six installed official-source files are hashed in `report.json`.

- `volume_decoders.py`: both hierarchical and FlashVDM decoding initialize
  sparse next grids to `-10000`, then replace remaining sentinels with NaN.
  Vanilla decoding instead queries every dense-grid point in chunks.
- `surface_extractors.py`: `MCSurfaceExtractor.run` directly calls
  `measure.marching_cubes(grid_logit.cpu().numpy(), mc_level, method='lewiner')`.
  There is no finite check before extraction or after vertex conversion.
- `model.py`: `latents2mesh` sends the decoder result into the surface
  extractor; disabling FlashVDM selects `VanillaVolumeDecoder`.
- `pipelines.py`: `output_type='mesh'` avoids `export_to_trimesh`; the ordinary
  `output_type='trimesh'` path invokes default `trimesh.Trimesh(vertices, faces)`.
- `attention_blocks.py` / `attention_processors.py`: FlashVDM installs a
  specialized processor on `geo_decoder`. `enable_flashvdm(enabled=False)`
  changes the volume decoder but does not explicitly restore that processor.
  In this installed source, `set_default_cross_attention_processor` assigns
  the processor **class**, whereas normal initialization assigns an instance.
  An isolated fallback must explicitly call
  `geo_decoder.set_cross_attention_processor(CrossAttentionProcessor())`.

## Specific alternative if the parent confirms this mechanism

1. Preserve the original native vertex/face arrays, scalar grid, evaluated
   voxel mask and decoded latents before cleanup. Record NaN, positive-inf and
   negative-inf counts separately, including whether nonfinite entries belong
   to unqueried sentinels or evaluated network outputs.
2. In an isolated experiment worker, decode the **same decoded latents** with
   fully queried vanilla dense volume decoding and the ordinary attention
   processor, at a registered resolution and bounded chunk size. Do not
   regenerate a new sampled latent and call it the same repair. Dense decoding
   and native export must use the shared GPU lock and resource watchdog.
3. Require all grid values finite before marching cubes; retain all native
   outputs before any Trimesh processing. If queried logits remain nonfinite,
   stop and diagnose those rather than filling them with arbitrary constants.
4. Compare the native full surface and actual underarm/body anatomy before
   reduction. Finite arrays alone are insufficient. A complete dense surface
   may still reproduce the fused underarm anatomy found in the older body.

Do not blanket-fill unknown grid entries or rely on default mesh processing
as a character repair. Masked extraction can exclude valid surface-crossing
cells unless sufficient finite halos are established; it would need its own
explicit completeness check. This audit executes neither alternative and
makes no rider appearance, topology, rigging or production-readiness claim.

Reproduce with the existing H21 environment, CPU only:

```sh
OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 PYTHONDONTWRITEBYTECODE=1 \
  /Users/raynos/ml/img2mesh/Hunyuan3D-2.1/.venv/bin/python \
  assets/blender/hero-remaster/rider/one-rider-v2/native-extractor-audit208/reproduce.py
```

The rerun writes only this owned evidence directory and its private NPZ
directory. Freeze all existing receipts before any rerun.
