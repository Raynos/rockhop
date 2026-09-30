# Third-round gate after rejected D1 trials

The D2 cart, C1 brake camera and rejected D1 readability trials are the three rounds since the previous gate. D1's camera and material candidates were removed before this check, so the game source is the accepted C1 commit `68d0a1e1`.

`pnpm harness:gate --build --quick --only=boot,clear,crash,restart --jobs=1` ran cold boot, exact flat clear, crash and instant restart on host SwiftShader. The [partial report](ship-gate.partial.json) passes **8/11**. The flat clear is still 8.591667 s with pinned hash `622bb2554e0f9a26`; the crash occurs in 0.86 s; fault-to-control is 25 ms and manual restart takes one simulation tick. Menu ready p50 is **357.54/300 ms**, first synced frame **6,306/4,000 ms**, and restart synced-frame p95 **241.18/150 ms**. These three host software-renderer timing rows fail, so this is **NO-SHIP on this host**, not a physical-phone result.

The rejected [D1 camera](../../d1/terrace-sightline/README.md) and [contact-material](../../d1/terrace-contrast/README.md) moving comparisons did not improve the true terrace silhouette enough to ship. The next D1 pass requires a larger terrain and lighting composition and fresh uncoached riders.
