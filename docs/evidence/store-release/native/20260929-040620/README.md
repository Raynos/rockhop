# Main-branch web/iOS simulator gate before WebGL2 recovery

The native debug shell bundled committed `1e1dc9ded3edb913350e5169f030d92fa1ac4343`, the same source served by the public site after [production run 36519890627](https://github.com/Raynos/rockhop/actions/runs/36519890627). [Machine report](gate.json) · [silent played iOS clip](ios-clip.mp4) · [clip frames](ios-sheet.jpg).

Headless Chromium/Metal and the iPhone 17 Pro Max Simulator both reached the menu, entered riding, and used zero AudioContexts. The pinned flat-test input finished at byte-identical **8.591666666666667 s** (`efeeeeeeee2e2140`) and state hash `622bb2554e0f9a26` on both. The paced replay matched too. Both crashed at 0.858333 s and regained control in 25 ms; the one-tick restart passed. The iOS cold menu took **8,431 ms**, so the warm-start target is not proved by this run.

The user's physical iPhone Safari screenshot from build `0de5d5a` still reports **WebGL2 context unavailable during renderer startup**. This simulator pass does not override that failure. A fresh-canvas WebGL2 startup retry is a follow-up source change; it needs its own automation and a physical-phone retest. Android emulator testing remains off by user instruction.
