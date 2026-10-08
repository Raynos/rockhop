# Native IK pole convention from the solver

Finding: Blender constructs its chain up vector as rootX*cos(angle)+rootZ*sin(angle); the earlier signed angle about rootY reverses this convention. Direct basis coefficients explain the actual approximately180-degree native03 operators and yield the corrected pole angle without trials.

Validation: Parent reviewed source/proof against retained actual native03 matrices; predicted old operators agree within4.3e-7 arms/2.02e-5 legs, corrected identity prediction within4.29e-6. Both changed files parse. Actual native04 full build remains pending and keeps every physical/rest/operator/action gate.

Limits: Analytic prediction is not a native pass. Full build now saves a separately labeled strict neutral-only checkpoint before action authoring; a later action failure cannot become a successful six-action delivery.
