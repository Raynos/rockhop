"""Positions-fixed local source topology proposal, not an executable repair."""

SOURCE_HOOD_FACES = (
    4, 28, 29, 67, 68, 3813, 3828, 3830, 3846, 3847, 3848, 4105, 4106,
)

FIRST_CANDIDATE = {
    'source_primitive': 2,
    'source_face_slots': (4105, 4106),
    'old_diagonal': (49, 66),
    'new_diagonal': (59, 50),
    'old_indices': ((59, 49, 66), (49, 50, 66)),
    'proposed_indices': ((59, 49, 50), (59, 50, 66)),
    'positions_fixed': True,
    'triangle_count_change': 0,
    'target_witness_ids': (0, 1, 2),
    'candidate_geometry_evaluated': False,
    'parent_go_received': False,
}

BOUNDED_PASS = {
    'candidate_registry': 'operator-proposal/hood185-candidates.json',
    'seed_faces': 13,
    'allowed_source_face_slots': 28,
    'initial_edges': 23,
    'excluded_attribute_fan_edges': 4,
    'max_accepted_flips': 32,
    'max_candidate_tests': 128,
    'max_cpu_threads': 2,
    'max_minutes': 12,
    'positions_fixed': True,
    'region_growth': False,
    'per_candidate_export': False,
    'selection': 'Strict decrease; area quality; lexicographic edge/face IDs',
    'goal': '11rest pairs to0; no new hood/body or adjacent/coplanar failure',
    'on_exhaustion': 'One frozen rejection, no vertex moves or fairing',
}

REQUIRED_GATES = (
    'Two source hood incident faces, four distinct physical nodes',
    'Neither old diagonal nor perimeter changes protected boundary edges',
    'Alternative diagonal absent from existing physical patch graph',
    'No source attribute fan seam incorrectly crossed by index surgery',
    'Positive actual Float32 area, no topology/winding defect',
    'Original head/neck/seam/cuff/morph/UV/PBR/source fields exact',
    'All new hood/body/glove strict pairs tested, inherited pairs labelled',
    'Adjacent/coplanar fold test prevents shared-class exclusion gaming',
    'Parent source silhouette/film judgment after stable export only',
)


def require_go(contract):
    if not contract.get('parentGeometryGo185'):
        raise RuntimeError('Read-only planning; Go185 has not been received')
    return contract


# No source loading, face replacement, normal calculation, solve or export.
