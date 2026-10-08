# Complete candidate saved; actual geometry checks reject it

Actual author03 exited 1 after 39.648 s. The complete editable candidate was saved **before all ten dense checks**, so this failed construction remains inspectable: native SHA256 `13d0017e0ccb160f2cc550f3104c8206ea3954136807525a4c489cac41f8f2f1`. The 775,852,259-byte blend stays ignored; [packet.json](packet.json) retains its reported hash and exact diagnostic lineage.

Both full control scans report zero strict crossings touching new cuff/wrist construction. Retained unchanged finger crossings remain open: 904 left and 875 right. Both dense **local cuff/wrist/join and immediate-neighbour** self-cross checks pass. These results do not clear distant fingers or the complete garment.

| Dense check | Left | Right |
| --- | --- | --- |
| Local cuff self-cross | Pass | Pass |
| Sleeve self-cross | Fail | Fail |
| Glove/sleeve intersection | Fail | Fail |
| Cuff/wearer intersection | Fail | Fail |
| Sleeve/wearer intersection | Fail | Fail |

All ten checks are retained: two pass and eight fail. Exact first crossing triangles and vertex IDs are in the unmodified construction report. Each sleeve also has **four degenerate faces already degenerate in the baseline, zero newly degenerate faces**. Their current coordinates have moved; inherited degeneracy does not mean unchanged geometry or an exempted failure. That baseline classification applies only to these degenerates, not to the other strict intersections.

The packet retains exact construction JSON and guard bytes as deterministic gzip, both actual guide arrays, actual hoodie wrist arrays and the original combined stdout/stderr worker capture. Every retained hash and gzip roundtrip was verified. The report records unchanged 75-bone rest, protected geometry, edited topology/UV/PBR/skin fields and zero new bindings, correspondences, weight computations or bakes.

**Rejected combined model; geometric correction required.** Saving it and passing local cuff checks grants no complete-model, art or motion approval. No export or normal-player promotion; R0–R5 remain open.
