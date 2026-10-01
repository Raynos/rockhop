# NEW white rider: actual replay exposes missed grip frames

This is a real private game build using body-bind05, its explicit adapter
and untouched production bikes/physics. Both tier labels use the same full
candidate deliberately; real reduced-detail geometry remains untested.

Cold boot, full recorded clear, crash and instant restart pass on both tiers.
State hash368f1ca5bd9e830a and finish clock bytesabaaaaaaaa0a4440 match Node.
Crash103ticks, restart2ms LOW/3ms HIGH, no page errors. First4s/120actual
moving frames retain body/clothing and show no gross wrist gap.

The longer40s/480frame capture changes the verdict: five sampled frames
lose grip contact, maximum72.704mm. Actual worst frame at tick500 visibly
shows both gloves hovering. Sole sockets stay within1.840µm throughout;
physics-driven lean reaches both-1/+1 and recorded wheel landings occur.
These are sockets, not complete surface-penetration measurements. Reject
final-contact acceptance and investigate rare elbow-pole degeneracy before
any promotion. The CPU static profiles were insufficient, not a passed gate.

Body/hands/feet movies and all ordered decoded boards are retained. Original
2560x1440 movies and lossless captured PNGs remain private with exact hashes;
review movies are1280x720. No frames, rig or texture repainted. Parent has
reviewed all120short-prefix frames and actual worst full-body frame; broad
40s appearance/visible sole/palm verdict remains open. GPU canonical lock,
peak46.956GB anonymous, whole second batch271.681s; no competing job touched.
