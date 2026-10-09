"""Dense source-relative graph fitting with actual-contact ADMM constraints.

This constructs a garment mesh; it does not assert an injective spatial map.
All retained vertices and centroids constrain every linearization. Source-wall
correspondences penalize displacement differences across the actual cloth solid.
"""
import numpy as np


def graph(points, faces, retained, pair_ids, pair_faces, pair_bary, guide_faces, guide_bary,
          guide_delta, smooth_scale):
    from scipy import sparse
    original, inverse = np.unique(points, axis=0, return_inverse=True)
    f = inverse[faces]; count = len(original)
    triangle = original[f]; area = np.linalg.norm(np.cross(triangle[:, 1]-triangle[:, 0],
                                                         triangle[:, 2]-triangle[:, 0]), axis=1)/2
    edge = np.concatenate((f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]))
    squared = np.sum((original[edge[:, 0]]-original[edge[:, 1]])**2, axis=1)
    weight = np.divide(np.tile(area, 3), 3*squared, out=np.zeros(len(edge)), where=squared > 0)
    a, b = edge.T
    stiffness = sparse.coo_array((np.r_[weight, weight, -weight, -weight],
        (np.r_[a, b, a, b], np.r_[a, b, b, a])), shape=(count, count)).tocsr()
    mass = np.bincount(f.ravel(), weights=np.repeat(area/3, 3), minlength=count)
    # A tiny disconnected/degenerate source island retains its source location.
    # This numerical positive term is not a geometry/contact acceptance tolerance.
    fidelity = np.maximum(mass/smooth_scale**2, np.finfo(float).eps)
    pfaces = inverse[faces[pair_faces]]
    row = np.repeat(np.arange(len(pair_ids)), 4)
    col = np.column_stack((inverse[pair_ids], pfaces)).ravel()
    val = np.column_stack((np.ones(len(pair_ids)), -pair_bary)).ravel()
    wall = sparse.coo_array((val, (row, col)), shape=(len(pair_ids), count)).tocsr()
    grow = np.repeat(np.arange(len(guide_faces)), 3)
    guide = sparse.coo_array((guide_bary.ravel(), (grow, inverse[faces[guide_faces]].ravel())),
                            shape=(len(guide_faces), count)).tocsr()
    # The same unit material energy weights measured wall links and soft
    # anatomical guide points. None of these is a pass/fail art threshold.
    energy = stiffness+wall.T@wall+guide.T@guide+sparse.diags_array(fidelity)
    rhs = guide.T@guide_delta
    retained_faces = f[retained]; used = np.unique(retained_faces)
    row = np.r_[np.arange(len(used)), np.repeat(np.arange(len(retained_faces))+len(used), 3)]
    col = np.r_[used, retained_faces.ravel()]
    weights = np.r_[np.ones(len(used)), np.full(3*len(retained_faces), 1/3)]
    contact = sparse.coo_array((weights, (row, col)),
        shape=(len(used)+len(retained_faces), count)).tocsr()
    # Vector-valued splitting gives one SPD matrix for all three coordinates.
    # Row equilibration matches the augmented penalty to local material
    # stiffness. It changes ADMM convergence, not the constrained minimizer.
    penalty = contact@energy.diagonal()
    system = (energy+contact.T@sparse.diags_array(penalty)@contact).tocsr()
    preconditioner = sparse.diags_array(1/system.diagonal()).tocsr()
    return {'original': original.astype(float), 'inverse': inverse, 'faces': f, 'contact': contact,
            'system': system, 'preconditioner': preconditioner, 'rhs': rhs, 'wall': wall,
            'used': used, 'constraintVertices': len(used), 'constraintCentroids': len(retained_faces),
            'sourceSamples': contact@original, 'guide': guide, 'penalty': penalty, 'energy': energy.tocsr()}


def initialize(system, cg_atol):
    """Minimize the SAME source energy before imposing actual body contacts.

    This is an initial iterate only; it cannot establish garment fit. It avoids
    damping unconstrained tangential motion through inactive contact splits.
    """
    from scipy import sparse
    from scipy.sparse.linalg import cg
    matrix = system['energy']; preconditioner = sparse.diags_array(1/matrix.diagonal())
    displacement = np.zeros_like(system['original']); information = []
    for axis in range(3):
        displacement[:, axis], info = cg(matrix, system['rhs'][:, axis],
            rtol=0., atol=cg_atol, maxiter=256, M=preconditioner)
        assert info >= 0; information.append(int(info))
    return displacement, information


def halfspaces(value, normals, lower):
    deficit = np.maximum(lower-np.einsum('ij,ij->i', value, normals), 0)
    return value+normals*deficit[:, None]


def linearize(system, displacement, nearest, target):
    moved = system['contact']@displacement
    gap, normal = nearest(system['sourceSamples']+moved)
    lower = target-gap+np.einsum('ij,ij->i', moved, normal)
    return gap, normal, lower


def residuals(system, state):
    image = system['contact']@state['d']
    stationarity = system['energy']@state['d']-system['rhs']+system['contact'].T@(system['penalty'][:, None]*state['dual'])
    return {'primalResidualM': float(np.linalg.norm(image-state['z'], axis=1).max()),
        'linearizedMaximumDeficitM': float(np.maximum(state['lower']-np.einsum('ij,ij->i', image, state['normal']), 0).max()),
        'stationarityEquationResidual': float(np.linalg.norm(stationarity, axis=1).max()),
        'dualEquationResidual': float(state['dualEquationResidual']),
        'cgInfo': state['cgInfo'].tolist(), 'inner': int(state['inner'])}


def converged(row, numerical):
    return (row['primalResidualM'] <= numerical['primalToleranceM']
        and row['linearizedMaximumDeficitM'] <= numerical['primalToleranceM']
        and row['stationarityEquationResidual'] <= numerical['equationTolerance']
        and row['dualEquationResidual'] <= numerical['equationTolerance']
        and not any(row['cgInfo']))


def iterate(system, state, cg_atol):
    from scipy.sparse.linalg import cg
    contact = system['contact']; d, z, dual = (state[k] for k in ('d', 'z', 'dual'))
    rhs = system['rhs']+contact.T@(system['penalty'][:, None]*(z-dual))
    # Equation residual tolerances are numerical settings, never a guarantee
    # on coordinate error. CG exhaustion cannot certify convergence.
    cg_info = []
    for axis in range(3):
        d[:, axis], info = cg(system['system'], rhs[:, axis], x0=d[:, axis],
            rtol=0., atol=cg_atol, maxiter=256, M=system['preconditioner'])
        assert info >= 0, ('Dense SPD solve failed', info)
        cg_info.append(int(info))
    image = contact@d
    previous_z = z
    z = halfspaces(image+dual, state['normal'], state['lower'])
    dual += image-z
    dual_residual = system['contact'].T@(system['penalty'][:, None]*(z-previous_z))
    state.update(z=z, dual=dual, d=d, cgInfo=np.asarray(cg_info), inner=int(state['inner'])+1,
                 dualEquationResidual=float(np.linalg.norm(dual_residual, axis=1).max()))
    return residuals(system, state)


def tangent_normals(original, current, faces, loop_normals):
    """Inverse-transpose of each actual triangle tangent deformation.

    The material-normal extension maps old unit face normal to new unit face
    normal. Degenerate source/current triangles retain normals and are counted;
    zero new area remains a failing separate geometry check.
    """
    result = loop_normals.copy(); unsupported = []
    for start in range(0, len(faces), 16384):
        end = min(start+16384, len(faces)); a, b = original[faces[start:end]], current[faces[start:end]]
        e1, e2 = a[:, 1]-a[:, 0], a[:, 2]-a[:, 0]
        f1, f2 = b[:, 1]-b[:, 0], b[:, 2]-b[:, 0]
        ns, nt = np.cross(e1, e2), np.cross(f1, f2)
        ls, lt = np.linalg.norm(ns, axis=1), np.linalg.norm(nt, axis=1)
        good = (ls > 0) & (lt > 0); ids = np.flatnonzero(good)
        unsupported.extend((np.flatnonzero(~good)+start).tolist())
        if not len(ids): continue
        ns, nt = ns[good]/ls[good, None], nt[good]/lt[good, None]
        # Covectors dual to current f1/f2, using the actual triangle cross product.
        dual1 = np.cross(f2[good], nt)/lt[good, None]
        dual2 = np.cross(nt, f1[good])/lt[good, None]
        n = loop_normals[start:end][good]
        moved = (np.einsum('nkj,nj->nk', n, e1[good])[:, :, None]*dual1[:, None]
                 +np.einsum('nkj,nj->nk', n, e2[good])[:, :, None]*dual2[:, None]
                 +np.einsum('nkj,nj->nk', n, ns)[:, :, None]*nt[:, None])
        lengths = np.linalg.norm(moved, axis=2)
        result[start+ids] = np.divide(moved, lengths[:, :, None], out=np.zeros_like(moved),
                                    where=lengths[:, :, None] > 0)
    return result, unsupported
