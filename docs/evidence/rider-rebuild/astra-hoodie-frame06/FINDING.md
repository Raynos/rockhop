# Source bone initialization inverted the hoodie sleeves

Fresh independent Astra06 identified matrix-before-length on a new zero-length edit bone. Parent verified the exact Blender5.2.1 implementations: [matrix preserves existing length](https://raw.githubusercontent.com/blender/blender/v5.2.1/source/blender/editors/armature/armature_utils.cc) and [zero-length direction falls back to +Z](https://raw.githubusercontent.com/blender/blender/v5.2.1/source/blender/makesrna/intern/rna_armature.cc).

Actual saved-native probe exit0/6.133s confirms all six sleeve source bones point upward instead of toward source elbows/cuffs. L upper-arm tail error387.302mm, forearm378.475mm; chest correct. Original GLB centers independently match controls within12µm. This is a construction-code bug, not a reason to regenerate the selected garment or tune weights.

Initialize source head/tail before assigning matrix, then check actual rest endpoints/matrices before posing. One actual corrected native and original-PBR outfit review next. All rider gates remain open.
