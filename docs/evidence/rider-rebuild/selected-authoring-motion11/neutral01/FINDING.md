Neutral probe locates incorrect added rest orientations before IK

Actual read-only native probe exits0/7.053seconds. Added mechanism/control
heads match source positions, but rest matrices already differ: thigh1.994,
upperarm1.944, handtarget1.779, shouldercontrol1.031 maximum component errors.
The failure therefore precedes action authoring. The new edit bone receives its
matrix while its length is zero, before its positive length is established.

Validation: Parent inspected actual full per-bone rest/pose/basis/constraint
report. Animationlead24 corrects creation order and asserts added rest matrices
before constraints, retaining original neutral/target/operator gates.

Limits: Diagnostic only; no correction executed, native saved or art accepted.
