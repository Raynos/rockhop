# Physical iPhone C1 FPS receipt

After the parent verifies the checked candidate deployment, open its stable
URL with `?review=1` in iPhone Safari, in landscape. The target is 60 FPS on
this physical phone; a Mac or simulator result does not qualify it.

1. Select the intended candidate outfit in Garage, then play C1 normally.
   Keep the usual quality/frame-rate settings. Ride for at least 25 seconds
   without pausing, crashing, changing settings or hiding Safari.
2. While still riding, tap **✎ Note**. Its `ride fps` chip shows the measured
   FPS for the latest 20 seconds. If it says `sampling`, close the note,
   resume and ride for a fresh 25 seconds before opening it again.
3. Send a short note naming the phone model and whether loading/first Garage
   was stable. FPS/frame percentiles, actual DPR/canvas, WebGL renderer,
   loaded rider/native/grip hashes and the full running build SHA travel with it.
   The parent drains the existing inbox and files the actual phone receipt.

`ready: true` means a complete 20 second riding window, including a slow
result; it is not a 60 FPS pass. The earlier >30 FPS requirement is the floor,
with 60 FPS the requested target. A crash, pause, Garage, hidden page or
track/outfit/tier/cap change starts a new window. The note itself captures
before pausing, so typing does not contaminate the result. No clear is needed.

The report measures actual submitted riding frames and unclamped wall-clock
intervals. CPU percentiles are CPU time, not GPU completion. This short
receipt diagnoses the reported 12 FPS; longer physical play is still needed
to establish sustained behavior beyond the 20 second window.
