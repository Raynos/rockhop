# First author trial stops at a stale Blender vertex-group handle

Parent checkpoint e1ff2208e admitted one CPU2 author stage. The canonical guard
ran through nonblocking`lockf -k -t0`, bounded180seconds, with Blender5.2.1 and
`--threads2 --python-exit-code1`. It returned exit1 after5.433seconds; the
controller/process handle exited and the shared heavy lease is released.

The run loaded the pinned native02 wearer and constructed the dense selected
reference and authored surface. After applying the Shrinkwrap, Blender invalidated
the retained Python RNA vertex-group handle. Removing that stale handle raised
`RuntimeError: DeformGroup '' not in object 'RiderJeans'` at author-jeans.py153.
This occurred before weight initialization, unchanged-body/rest signature assertion,
output directory creation or master save. There is no saved candidate, geometry
review or body/rest preservation receipt from this trial. No bake ran.

The log also records an ordinary Blender material-node deprecation warning;
there is no NumPy BLAS warning or warning filter. Original sources remain pinned
and untouched. The complete guard and worker log are retained in`author-guard01/`.

Proposed correction is only reacquiring the named`SelectedSculptProjection`
vertex-group RNA handle after modifier application before removal. No fitting
parameters or construction mechanism change is proposed. The minimal source repair now reacquires that named group after the modifier.
Review of other apply sites finds no other retained mesh/group RNA data handles.
The bake stage reacquires source data/material after its mesh replacement, and
reads bmesh layers before mesh write/free. Fitting controls remain unchanged.
The ignored worker.log is copied byte-for-byte to tracked worker.txt. No retry
has run; parent must checkpoint this correction before a fresh bounded trial.
All selected-appearance, motion, full-outfit, phone and release gates remain open.
