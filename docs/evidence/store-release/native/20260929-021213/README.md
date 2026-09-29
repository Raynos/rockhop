# Current-source iOS WKWebView gate after map and D3 rounds

The debug native bundle was built from a clean export of committed `6a70d2a245612a7dd7b6af0b7c79cd973793a6c8`, then run through the in-app gate on headless Chromium/Metal and the landscape iPhone 17 Pro Max Simulator. [Machine report](gate.json) · [silent played iOS clip](ios-clip.mp4) · [clip frames](ios-sheet.jpg).

Both legs reached menu and riding with **zero AudioContexts** under automation. Web and iOS finished the pinned flat-test recording at byte-identical **8.591666666666667 s** (`efeeeeeeee2e2140`) and state hash `622bb2554e0f9a26`, including the paced rendered replay. Both crashed at 0.858333 s, restored control in 25 ms and completed 20 one-tick restarts. The iOS synced restart frame p95 was **5 ms**. The simulator cold launch reached menu in **4,335 ms**; the web leg took 2,312 ms. The native gate returned success.

This is exact debug-shell and simulator proof for the current branch. The gate starts `flat-test` rather than playing through the 3D map or the twelve-course campaign. It does not establish a physical iPhone warm cached start, real touch and orientation, sustained phone performance, Android WebView, signed iOS archive or store readiness. The user's instruction keeps the Android emulator off; its native runtime proof requires a physical Android phone.
