# Actual-engine03 source-specific private pose

Unaccepted private actual-game build: `harness/out/rider-rebuild/actual-engine03`.
Source GLB SHA256: `58677cc37aff6b22bb98144762eb5a93dfe689ac207ea0b74a214ba60538f6fc`.
Full source contract SHA256: `32d67e9031bd6865a561ba29dc6d2765ace49ad13bfb08bd61df07df85440ee4`.

The exact normalized 1.78 m arm chain measures 0.53464 m. The earlier
0.56312 m estimate double-scaled those already normalized lengths and is wrong.
The adapter always measured loaded joint centers and never used that estimate.

The selected anatomical palm-forward direction is -45 degrees in bike XY.
An explicit 41-knot input-lean table selects upper-spine flex in [-10,0] degrees
from the new measured source workspace. Linear interpolation stays within the
10 degree anatomical bound. The physical pelvis carrier and supplied COM stay
fixed; every inverse sample resets all 75 source joints. No limb scaling or
source FOUR weights change. This is a practical private review candidate.

Validation: eleven CPU tests pass on exact04 plus selected pose calibration,
including 41 inputs with socket-center gaps below 5 mm, world bike rotation,
fixed segment lengths, unchanged physics frame, exact repeated full joint
reset/crash/restart, authored Garage clip, and metadata request retry/sharing.
The input table has maximum socket-center gap 4.4032 mm. The remaining gap is
reported without moving the physical COM or hiding reach failures.

The private build passes the unchanged 701 KiB gzipped JS gate (717176 B,
limit 717824 B) and inline loader gate (8176 B, limit 8192 B). Calibration lives
in the existing private model catalog and its actual fetch is awaited before
GLTF construction. The load-manifest catalog byte/gzip receipt is updated.
The complete 75-joint specification remains; five consumed native endpoint
head/tail rows are compiled, without unused author matrices. Constructor debug
includes material factors and loaded texture dimensions for moving review.

Evidence: [pose calibration](combined04-pose-calibration.json),
[default04 measurements](combined04-com.json), [build receipt](actual-engine03-build.json).
Limits: socket-center proximity does not certify glove surface/bar-radius or
phalange clearance. The input table cannot guarantee contacts for every
force-displaced physical COM. No moving art, physical-device or release pass.
