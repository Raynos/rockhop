"""Declarative read-only gates; no fitter, mesh instantiation or bpy import."""

PREFLIGHT = {
    'parent_go_required': True,
    'regular_ring_nodes': 64,
    'regular_ring_unique_float32_nodes': 64,
    'regular_ring_min_edge_m': 0.001,
    'new_neighbor_row_min_distance_m': 0.002,
    'minimum_triangle_area_m2': 1e-12,
    'exact_donor_edges': 'Report inherited range; never move/skip/collapse',
    'fitter': 'Positive smooth periodic radial B-spline; measured extrema',
    'orientation': 'Reverse donor face-edge direction; propagate half-edges',
    'collar_hem_controls': 'Positive-width offset into upper garment',
    'source_loops': {'hood': 307, 'cuff_left': 65, 'cuff_right': 62},
    'lower_boundary': 'Exact independently compiled paired design-cut loop',
    'quad_transitions': 'Declared triangles/poles; every diagonal preflighted',
    'render_after': 'Actual Float32 combined export topology/contact gate',
    'on_failure': 'Freeze evidence; no automatic geometry repair/retry',
}


def require_go(contract):
    if not contract.get('parentGeometryGo'):
        raise RuntimeError('No parent geometry go; read-only proposal only')
    return contract


def require_unique_controls(controls_as_float32_tuples):
    if len(set(controls_as_float32_tuples)) != len(controls_as_float32_tuples):
        raise ValueError('Repeated actual Float32 control positions')


def required_new_boundary_direction(donor_directed_edge):
    first, last = donor_directed_edge
    if first == last:
        raise ValueError('Collapsed donor edge')
    return last, first


# No functions create points, fit data, generate faces, export or render.
