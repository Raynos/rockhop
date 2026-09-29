# Third-round gate after A3 loader

The accepted CSS comment cut, C1 ramp support and A3 loader share this edited source. The [A3 matched moving report](../../a3/loader-cab/README.md) has exact clean, obstacle and fault hashes and camera checks.

The [quick partial ship gate](ship-gate.partial.json) ran cold boot, exact flat clear, crash and instant restart on host SwiftShader. **8/11 checks passed.** The flat clear remains 8.591667 s with hash `622bb2554e0f9a26`; crash occurs at 0.86 s; fault-to-control is 25 ms; restart logic takes one tick. The three misses were menu ready p50 **364.52/300 ms**, first synced frame **8,405/4,000 ms**, and restarted synced-frame p95 **482.59/150 ms**. Host load average was about 10/18 cores at boot. A [boot-only recheck](boot-recheck.json) under higher host load missed the same two boot rows (564.81/300 and 13,913/4,000 ms). This is **NO-SHIP on this software-renderer host**, not a physical-phone frame result.

A3's scenic geometry is created only in its course scene, behind the ridden contact lane; it does not change the boot pipeline, physics or retry logic. The input result and fault recovery are unchanged. The real landscape iPhone and Android sustained frame, audio, battery and human-play gates remain open.
