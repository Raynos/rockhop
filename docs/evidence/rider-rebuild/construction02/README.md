# Independent frozen04 native/export inspection

Unaccepted static checkpoint. Parent owns actual played engine judgment.
Source: `harness/out/rider-rebuild/construction01/combined04/rider.glb`,
SHA256 `58677cc37aff6b22bb98144762eb5a93dfe689ac207ea0b74a214ba60538f6fc`.
Recipe: `assets/blender/rider-rebuild/construction02/audit-frozen04.py`.
[Decoded audit](frozen04-static-audit.json) records the exact findings.

All10,582 source body vertices form one connected component, including head and
neck. All75 exported joint parents match the native contract. Native-to-decoded
rest heads differ by at most0.772µm. Decoded rest LBS positions across all dressed
meshes differ from source positions by at most0.987µm. Both eyes have only the
head joint's weight and occupy the declared head region. These static checks
do not judge sculpture, moving normals, garments or contact.

The exporter drops tiny native FOUR influences on12 body source IDs and
renormalizes the remaining weights. Largest weight difference0.0000941177 is
source3220's removed `DEF-spine.001` contribution. Native FOUR and exported GPU
fields are therefore not exactly identical; moving native/export parity remains
open. Largest automatic FULL→FOUR removed mass0.25312 occurs near the wrist;
146 vertices lose more than0.1 mass, including neck/pelvis areas. Removed mass
does not measure deformation error. Retain FULL controls and evaluate motion.

Reported0.5346397m arm length is already the normalized1.78m rider's length:
upper0.2747018m, forearm0.2599380m. Raw source-coordinate proposal totals roughly
0.507595m before scale1.0532787. Runtime must use actual exported heads and must
not multiply the reported normalized length by source scale again.

Validation: read-only Python audit ran successfully against frozen04. No Blender,
browser, body render, pose injection, master alteration or export replacement.
R0–R5 remain open. Current engine review takes priority over clip expansion.
