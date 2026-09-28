# Portrait rotate prompt during play — 2026-09-28

The game is landscape only. Before this fix, its in-game rotate overlay required `(pointer: coarse)` as well as portrait and a width cap, so a portrait viewport with a fine pointer continued showing gameplay. The loader had a separate width cap. A silent, automated browser reproduction at 393×852 showed gameplay without the rotate prompt during a ride.

Both loader and in-game CSS now show their rotate prompt on **any** portrait viewport. In the [played 17-second video](rotate-prompt-short.mp4), the same ride shows landscape gameplay, the full rotate prompt after turning portrait, and uninterrupted gameplay on returning to landscape. The original uncut capture is [here](rotate-prompt.mp4). A fresh portrait page load also showed the loader prompt; a landscape reload hid it. The browser reported zero page errors.

The capture uses `navigator.webdriver === true` and silent headless Chromium. It verifies the responsive UI, not the installed iPhone orientation transition. A physical phone recording remains in the device release gate.
