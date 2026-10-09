# Committed release harness lint correction

Finding: strict CI-sparse lint previously failed 216 committed harness
errors; preserve serialized browser behavior and Node test registration
while qualifying those sources for the unchanged release lint gate.
Validation: corrected strict clean-export lint passes,27 syntax checks
pass, six compatible pure Node files yield35 pass/8 expected external-
assembly skips. Parent reviewed globals, exact lexical sorting, Promise
cleanup, independent flattened fixtures and narrow transform exceptions.
Limits: historical private source-transform/plain-Node failures retained;
no assertions removed or production source/asset/gate changed. Broader
production remains paused; local software-renderer timing failure open.
Evidence: docs/evidence/rider-rebuild/sixth-outfit-release01/lint-cleanup01/
