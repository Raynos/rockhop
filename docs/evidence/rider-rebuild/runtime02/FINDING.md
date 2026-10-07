# Actual hierarchy COM inversion checkpoint

Unaccepted private runtime checkpoint; player assets and sources are untouched.
The adapter calibrates native/rest head, toe and finger tail correspondences,
then measures an approximate adult-male segment mass model on actual posed
joint centers. The requested physical COM stays distinct from the solved hips.
The old profile is only a deterministic starting guess and supplies physical
carrier/head angles, contact targets and bend poles. Each numerical sample
resets all 75 source joints; no segment scale or source FOUR weight changes.

Validation: nine CPU tests pass on actual combined02, including 41 input leans,
measured COM residual, unchanged physics frame, actual segment lengths,
world bike rotations, full finger perturbation/reset, exact crash/restart pose
restoration and Garage authored-clip motion. Maximum measured COM residual is
0.5378 micrometers. The old rig still fails real contacts: maximum hand socket
gap 64.985 mm and sole gap 20.601 mm. The contact flags reflect those errors.

On this desktop CPU the 41 solved updates have median 1.473 ms and maximum
7.140 ms, including cold samples. No browser/device speed or moving art pass
is implied. Native04 with source-fitted arm centers is the next comparison.

Evidence: [raw comparison](combined02-com.json), [reproducible probe](probe.mts).
Limits: endpoint/segment mass fractions approximate adult male mass distribution;
they do not integrate tissue density or claim unchanged multibody inertia.
Physical carrier orientation remains fixed. Spine flex is currently zero.
