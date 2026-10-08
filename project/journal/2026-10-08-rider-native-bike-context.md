# Exact bike context for native construction

Finding: Both actual bike saddles and existing unaccepted palm/boot contact frames are expressed in the selected native rig coordinates. Boot contact frames are converted through the measured contact-in-foot and anatomical socket-in-foot transforms; rejected fitted pelvis/spine controls are excluded. A separate editable native pose helper accepts explicit pelvis, torso/head and all pole controls.

Validation: Parent read generator, input and helper. Retained actual output has116 saddle triangles per bike and exact source hashes; generator checks round-trip contact transform residual below1e-12. Python helper parses; native pose/control/contact success remains unmeasured.

Limits: The context is authoring/reference geometry, not a seated pose, contact support, animation or clothed art pass. It supplies finite saddle guides to the separate posed-volume construction.
