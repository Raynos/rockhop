# Resident decoder reuse

Finding: Coast/Alpine dynamically import model decoders already resident for hero models and C1 tug. Remove unnecessary async wrappers while retaining demand-driven GLB loading, exact models and owner/failure handling. Normal gate player size reduces697.51→697.30KiB without relaxing the700KiB cap.

Validation: nine Coast and eleven botanical isolated tests pass with app typecheck, scoped lint, fresh normal build and required14/14 boot/exact clear/crash/instant restart/bundle round gate. [Report](../../docs/evidence/course-remaster/resident-decoder/README.md).

Limits: no isolated startup/frame-time improvement, art or phone claim. Initial wrong test filter ran no tests; only the two actual leaf configs qualify the20 tests.
