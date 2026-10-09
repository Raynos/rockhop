# Canonical foot groups for the exact ankle42 native initializer

Native45 failed before its RAW save at the destination-group assertion. Its
first row (`nativeID: 0`) had already passed exact rest, source shin-only and
NPZ/replacement checks. The pinned75-bone contract contains `DEF-foot.L` and
`DEF-foot.R`, so the first failure identifies a missing Jeans `DEF-foot.L`
group. Right-side group absence is not inferred:52 measures the whole group
inventory during intake and appends only whichever canonical foot groups are
missing. Native45 and all original native files remain untouched.

Native52 keeps the same native10, qualified11, generation10, qualifier11 and
frozen42 field ancestry. It checks all3318 native IDs, exact rest coordinates,
incoming deform rows and NPZ/JSON replacements before any mutation. Only
missing `DEF-foot.L/R` groups may append, sorted by name after the last old
index. Existing names and indices remain exact. The pending record contains
actual `groupInventory.before`, `.appended` and `.after` arrays of name/index
pairs. The patch changes1652 left and1666 right declared rows without pruning
or normalization; selected nondeform memberships remain intact.

The original protected helper includes vertex groups. Native45's claim that
its fingerprint separated those groups was incorrect and would reject valid
field changes later. For Jeans only,52 removes exactly that pinned helper's
group block; positions, topology, attributes, UVs, normals, PBR and binds stay
in the fingerprint. Original key states/coordinates remain separately exact.
All other meshes retain the complete original fingerprint and exact full
field digest. Source and saved witnesses independently measure inventories.
The source predicts all saved Jeans memberships using the virtual appended
group inventory and exact42 replacements. Saved complete canonical fields
must equal that prediction, including every untouched and zero membership.
Group membership iteration order alone may differ after Blender reopens.

Parent serial CPU2 commands, each wrapped in the unchanged original guard:

```sh
/Applications/Blender.app/Contents/MacOS/Blender -b -t 2 --python-exit-code 1 --python assets/blender/rider-rebuild/selected-ankle-native52/apply.py -- save harness/out/rider-rebuild/selected-ankle-native52/native01
/Applications/Blender.app/Contents/MacOS/Blender -b -t 2 --python-exit-code 1 --python assets/blender/rider-rebuild/selected-ankle-native52/apply.py -- source harness/out/rider-rebuild/selected-ankle-native52/native01/pending.json
/Applications/Blender.app/Contents/MacOS/Blender -b -t 2 --python-exit-code 1 --python assets/blender/rider-rebuild/selected-ankle-native52/apply.py -- saved harness/out/rider-rebuild/selected-ankle-native52/native01/pending.json
python3 assets/blender/rider-rebuild/selected-ankle-native52/apply.py compare harness/out/rider-rebuild/selected-ankle-native52/native01/pending.json
```

The save stage writes `UNACCEPTED-ankle-field42-native52.blend` RAW before full
field/geometry/action scans. It creates `pending.json`, which is not a pass.
Separate source/saved jobs create witnesses; only their CPU comparison emits
`receipt.json` with status
`ANKLE52_EXACT_REOPENED_FIELDS_PROTECTED_PASS_ART_PENDING`.

Downstream51 imports `apply.py` without Blender and calls
`qualify_receipt(path)`. It returns the exact receipt dictionary only after
rechecking actual source/input/recipe/native/witness pins and every comparison
gate. It accepts no native10 or failed45 substitute. The pure helper
`validate_witness_pair(pending, before, after, qualified, pending_pin,
recipe_pin, source_native, rows)` is also available for fixture use.

Validation:39 CPU fixtures pass and both Python sources parse as Python3.9.
Mutation fixtures cover unselected/selected nondeform/zero fields, original
group names/indices, noncanonical/extra groups, protected geometry/PBR, keys,
actions/rest, source ancestry and downstream witness pins. No Blender, native
save, browser, export, heavy numeric job or commit ran in this source unit.
Changed skinning still requires actual native/engine deformation parity,
finite ankle/cloth contacts, complete moving review and device qualification.
Source42 remains an unaccepted initializer even if protected comparison passes.
