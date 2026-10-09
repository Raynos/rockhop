# Preserve full saved-stage witness semantics

Finding: Native67 compares live Python group tuples to JSON arrays, which
necessarily fails despite equal values. Frozen37 captures and rechecks the
source witness before the raw63 save, so that saved-stage expectation is
correct. Adapter68 canonicalizes the complete witness as JSON and writes
actual, expected and diff evidence before asserting equality.

Validation: Four CPU fixture groups pass, including protected geometry,
fields, UV/PBR, binds, rig and metadata mutations and a substituted-stage
rejection. See
[handoff](../../docs/evidence/rider-rebuild/selected-boot-witness68/source-handoff.json).

Limits: Failed67 saved no live witness; further native differences remain
unknown. No native job ran and no source-unchanged or proof-pass claim is
made. Whole source guards and all frozen67 geometric checks remain.
