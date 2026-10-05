"""Semantic hand-surface envelope via a single bounded ambient velocity field."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def kernel(points, centers, sigma):
    delta = points[:, None, :] - centers[None, :, :]
    return np.exp(-(delta * delta).sum(2) / (2 * sigma * sigma))


def closest_triangle(points, triangles):
    """Exact closest among supplied triangles, including edges; no centroid proxy."""
    a, b, c = triangles[:, :, 0], triangles[:, :, 1], triangles[:, :, 2]
    ab, ac = b-a, c-a
    ap = points[:, None, :] - a
    aa, bb, cc = (ab*ab).sum(2), (ab*ac).sum(2), (ac*ac).sum(2)
    da, dc = (ap*ab).sum(2), (ap*ac).sum(2)
    determinant = aa*cc-bb*bb
    determinant = np.maximum(determinant, 1e-30)
    u, v = (da*cc-dc*bb)/determinant, (dc*aa-da*bb)/determinant
    face = a+u[:,:,None]*ab+v[:,:,None]*ac
    eligible = (u >= 0) & (v >= 0) & (u+v <= 1)
    candidates = [face]
    distances = [np.where(eligible, ((face-points[:,None,:])**2).sum(2), np.inf)]
    for x, y in [(a,b),(b,c),(c,a)]:
        edge=y-x
        t=np.clip(((points[:,None,:]-x)*edge).sum(2)/np.maximum((edge*edge).sum(2),1e-30),0,1)
        q=x+t[:,:,None]*edge
        candidates.append(q)
        distances.append(((q-points[:,None,:])**2).sum(2))
    d=np.stack(distances,2)
    selected=np.argmin(d.reshape(len(points),-1),1)
    ti,kind=selected//4,selected%4
    q=np.stack(candidates,2)[np.arange(len(points)),ti,kind]
    normal=np.cross(ab,ac)
    normal/=np.maximum(np.linalg.norm(normal,axis=2),1e-30)[:,:,None]
    return q,normal[np.arange(len(points)),ti],ti,np.sqrt(d[np.arange(len(points)),ti,kind])


def main():
    parser=argparse.ArgumentParser()
    for key in ['input','input-sha256','foundation','out','evidence']:
        parser.add_argument('--'+key,required=True)
    args=parser.parse_args()
    assert sha(args.input)==args.input_sha256
    out=Path(args.out);assert not out.exists();out.mkdir(parents=True)
    evidence=Path(args.evidence);evidence.mkdir(parents=True,exist_ok=True)
    glove=np.load(args.input);body=np.load(args.foundation)
    vertices=glove['vertices'].copy();labels=glove['branchLabels'];names=body['boneNames'].tolist()
    body_v=body['canonicalXYZ'].astype(float);body_f=body['canonicalTriangles']
    regions={};digit_names=['pinky','ring','middle','index','thumb']
    hand_columns=[i for i,n in enumerate(names)if n in ['hand.R','forearm.R'] or (n.endswith('.R') and any(n.startswith(d+'_')for d in digit_names))]
    for label in range(6):
        columns=hand_columns if label==0 else [names.index(f'{digit_names[label-1]}_{j:02}.R')for j in [1,2,3]]
        active=body['canonicalWeights'][:,columns].sum(1)>.15
        faces=body_f[active[body_f].any(1)]
        triangles=body_v[faces]
        regions[label]=(triangles,cKDTree(triangles.mean(1)),np.flatnonzero(active[body_f].any(1)))
    def witnesses(v):
        nearest=np.zeros_like(v);normals=np.zeros_like(v);signed=np.zeros(len(v));triangle_ids=np.zeros(len(v),int)
        for label,(triangles,tree,ids) in regions.items():
            select=np.flatnonzero(labels==label)
            _,candidate=tree.query(v[select],k=min(32,len(triangles)))
            q,n,ti,d=closest_triangle(v[select],triangles[candidate])
            nearest[select]=q;normals[select]=n;signed[select]=((v[select]-q)*n).sum(1)
            triangle_ids[select]=ids[candidate[np.arange(len(select)),ti]]
        return nearest,normals,signed,triangle_ids
    initial=vertices.copy();sigma=.014;clearance=.0025;rows=[]
    for iteration in range(160):
        nearest,normals,signed,triangle_ids=witnesses(vertices)
        deficit=np.maximum(clearance-signed,0)
        active=np.flatnonzero(deficit>.0002)
        if not len(active):break
        # Dispersed worst witnesses per semantic region, all applied together.
        chosen=[]
        for label in range(6):
            candidates=active[labels[active]==label]
            for i in candidates[np.argsort(-deficit[candidates])]:
                if all(np.linalg.norm(vertices[i]-vertices[j])>.008 for j in chosen):chosen.append(int(i))
                if sum(labels[j]==label for j in chosen)>=12:break
        centers=vertices[chosen]
        desired=normals[chosen]*np.minimum(deficit[chosen],.003)[:,None]
        coefficients=np.linalg.solve(kernel(centers,centers,sigma)+np.eye(len(chosen))*.02,desired)
        bound=float(np.linalg.norm(coefficients,axis=1).sum()*np.exp(-.5)/sigma)
        step=min(.35,.15/max(bound,1e-12))
        velocity=np.einsum('ni,ij->nj',kernel(vertices,centers,sigma),coefficients,optimize=False)
        vertices+=step*velocity
        assert np.isfinite(vertices).all() and bound*step<=.150000001
        rows.append({'iteration':iteration,'activeVertices':len(active),'selectedControls':len(chosen),'minimumSignedNormalWitnessM':float(signed.min()),'worstDeficitM':float(deficit.max()),'globalStepLipschitzProduct':bound*step,'maximumStepMovementM':float(np.linalg.norm(step*velocity,axis=1).max())})
    nearest,normals,signed,triangle_ids=witnesses(vertices)
    for side in ['R','L']:
        result={key:glove[key]for key in glove.files}
        result['vertices']=vertices.copy()
        if side=='L':result['vertices'][:,1]*=-1;result['faces']=glove['faces'][:,::-1]
        np.savez_compressed(out/f'glove-{side}.npz',**result)
    np.savez_compressed(out/'surface-witnesses.npz',initialXYZ=initial,finalXYZ=vertices,nearestBodyXYZ=nearest,nearestBodyNormals=normals,signedNormalWitnessM=signed,bodyTriangleRows=triangle_ids,branchLabels=labels)
    report={'accepted':False,'status':'SEMANTIC_SURFACE_ENVELOPE_EXPERIMENT_UNACCEPTED','recipeSHA256':sha(__file__),'input':{'path':args.input,'sha256':sha(args.input)},'foundation':{'path':args.foundation,'sha256':sha(args.foundation)},'candidate':{side:{'path':str(out/f'glove-{side}.npz'),'sha256':sha(out/f'glove-{side}.npz')}for side in ['R','L']},'steps':rows,'clearanceTargetM':clearance,'gaussianSigmaM':sigma,'finalMinimumSignedNormalWitnessM':float(signed.min()),'finalBelowTargetWitnessVertices':int((signed<clearance-.0002).sum()),'regions':{str(label):{'triangles':len(x[0]),'bodySelection':'Original body triangles incident on vertices with corresponding semantic weight >0.15'}for label,x in regions.items()},'witnesses':{'path':str(out/'surface-witnesses.npz'),'sha256':sha(out/'surface-witnesses.npz')},'limits':['Nearest triangle is exact among 32 closest centroid candidates within semantic regions; this is a finite local signed-normal witness, not a global signed distance or occupancy proof.','Full unchanged-body SAT and self-contact checks required independently.','Surface thickness/cuff opening, source UV bake, skin, native/engine, grip, art and device acceptance remain open.']}
    (evidence/'fit.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'steps':len(rows),'finalMinSignedNormalWitnessM':float(signed.min()),'belowTarget':report['finalBelowTargetWitnessVertices']}))


if __name__=='__main__':main()
