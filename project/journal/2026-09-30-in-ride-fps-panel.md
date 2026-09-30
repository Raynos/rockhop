# In-ride FPS panel · 2026-09-30

Finding: The game hid its compact frame meter behind a diagnostic URL and
the existing detailed performance panel was unreachable during normal play.
The ride now shows a tappable 44 px FPS/frame-time pill; tapping opens or
closes frame, physics and renderer detail without restarting the course.
Physics timing runs only while expanded.

Validation: Typecheck and 41 focused UI/economy tests passed. Targeted game
lint passed. The normal build passed the 661 KB player bundle budget at
675,230 B gzip. Silent headless 852×393 touch and 1280×720 desktop runs
clicked open and closed, found no restart overlap and reported zero phone
page errors. The tap-layer interception found in the first run was fixed.

Limits: Software-rendered headless FPS is not physical iPhone or Android
frame pacing. Sustained on-device measurement and the full course remaster
remain open. Repository-wide lint currently fails in separate uncommitted
Git-hook fixtures; these game files pass targeted lint.
