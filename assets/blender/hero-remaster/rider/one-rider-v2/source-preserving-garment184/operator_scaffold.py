"""Read-only operator contract; no source import, solver, mesh or export code."""

OPERATOR = {
    'kind': 'physical-position-quotient-dirichlet-biharmonic-displacement',
    'source_sha256': '186d0f86ae62722689be3c194f7437f623799c837e7ba515358680db12a1382e',
    'candidate_handle_source_row': (0, 4567),
    'support_original_edge_geodesic_radius_m': 0.045,
    'support_nodes': 62,
    'free_nodes': 22,
    'zero_ring_nodes': 20,
    'protected_support_nodes': 20,
    'handle_cap_m': 0.001,
    'all_free_displacement_cap_m': 0.003,
    'max_unknowns': 2000,
    'max_iterations': 200,
    'max_seconds': 60,
    'max_cpu_threads': 2,
    'residual_tolerance': 1e-10,
    'minimum_area_m2': 1e-12,
    'protected': 'Entire hood/glove/head/lowerY<.98 and exact seam aliases',
    'topology': 'Original faces, source halfedges, UV/PBR and row order exact',
    'current_feasible_clean_rest_target': False,
    'invariant_witness': (0, 7449, (4551, 4630), 2, 4106),
}


def preflight_request(parent_contract):
    if not parent_contract.get('parentGeometryGo'):
        raise RuntimeError('Planning only; parent geometry go absent')
    if parent_contract.get('objective') == 'clear_all_original_rest_pairs':
        if parent_contract.get('entireHoodLocked', True):
            raise RuntimeError('Locked seam-edge/hood witnesses are invariant')
    if not parent_contract.get('auditedMovableWitness'):
        raise RuntimeError('No justified free handle target')
    return parent_contract


# Deliberately no displacement/target generation or solve implementation.
