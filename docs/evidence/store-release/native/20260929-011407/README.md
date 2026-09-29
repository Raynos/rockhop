# Current-source iOS WKWebView gate

The debug native bundle was built from a clean export of committed `b5f4438c4ea999bac26f34bf25edf75d3418c663`, then run through the same in-app gate in headless Chromium/Metal and the landscape `rockhop-gate` iPhone 17 Pro Max Simulator. [Machine report](gate.json) · [silent played iOS clip](ios-clip.mp4) · [clip frames](ios-sheet.jpg).

Both platforms reach the menu and ride, construct **zero AudioContexts** under automation, clear the pinned flat-test recording at exactly **8.591666666666667 s** with matching float64 bytes `efeeeeeeee2e2140` and hash `622bb2554e0f9a26`, crash at **0.8583333333333333 s**, restore control in **25 ms**, and complete all 20 one-tick restarts. The paced rendered replay also has identical finish bytes and hash. iOS cold launch to menu measured **4,345 ms** in this Simulator run; web was **2,393 ms**. The iOS synced restart frame p95 was **5 ms**.

The clip shows a real landscape native boot and the pinned ride; the result image is the existing harness route, not a store screenshot. These are simulator and bot results. They do not establish warm cached start, physical-phone touch, sustained thermal performance, 12-course human difficulty or Android WebView. The normal-build four-section gate at `30028838` still has two SwiftShader frame misses, so this candidate remains **NO-SHIP**.
