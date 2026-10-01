# Boundary subdivision setup failure

CPU construction stops before export: float32 displacement arithmetic leaves some target boundary positions one ULP from the exact body coordinates. Dictionary lookup fails. This is our script arithmetic failure, not a generator failure or visual repair result. Explicitly assign exact seam target positions after deformation. Source masters unchanged; no new character exported.
