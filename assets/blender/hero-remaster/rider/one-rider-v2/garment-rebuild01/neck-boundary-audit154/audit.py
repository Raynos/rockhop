"""Read-only exact-coordinate interface audit; no source edits or asset acceptance."""
from pathlib import Path
from collections import defaultdict, Counter
import hashlib, json, struct
import numpy as np
from scipy.spatial import cKDTree

REPO = Path('/Users/raynos/projects/games/rockhop')
ROOT = Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2')
OUT = REPO/'docs/evidence/hero-remaster/one-rider-v2/garment-rebuild01/neck-boundary-audit154'
OUT.mkdir(parents=True, exist_ok=True)
SOURCE = ROOT/'rig-adapter01/body-bind34/rider.glb'
CAGE = ROOT/'garment-rebuild01/cage04/fit04.npz'
raw=SOURCE.read_bytes(); length=struct.unpack_from('<I',raw,12)[0]
doc=json.loads(raw[20:20+length]); binary=raw[28+length:]
def acc(index):
    a=doc['accessors'][index]; v=doc['bufferViews'][a['bufferView']]
    widths={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}
    dtype={5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']]
    assert 'byteStride' not in v and 'sparse' not in a
    return np.frombuffer(binary,dtype=dtype,count=a['count']*widths[a['type']],
        offset=v.get('byteOffset',0)+a.get('byteOffset',0)).reshape(a['count'],widths[a['type']])
def primitive(index):
    p=doc['meshes'][0]['primitives'][index]
    return acc(p['attributes']['POSITION']),acc(p['indices']).reshape(-1,3),p
P0,T0,p0=primitive(0); P2,T2,p2=primitive(2)
P,inv=np.unique(np.concatenate([P0,P2]),axis=0,return_inverse=True)
i0=inv[:len(P0)];i2=inv[len(P0):]
G0=i0[T0];G2=i2[T2]
shared=set(i0.tolist()) & set(i2.tolist())
shared0=np.where(np.isin(i0,list(shared)))[0]
def dense_skin(p):
    joints=acc(p['attributes']['JOINTS_0']);weights=acc(p['attributes']['WEIGHTS_0'])
    result=np.zeros((len(joints),19))
    for k in range(4):result[np.arange(len(joints)),joints[:,k]]+=weights[:,k]
    return result
D0=dense_skin(p0);D2=dense_skin(p2)
N0=acc(p0['attributes']['NORMAL']);N2=acc(p2['attributes']['NORMAL'])
normalDots=[];skinDeltas=[];aliasSpread=[]
for v in sorted(shared):
    a=np.where(i0==v)[0];b=np.where(i2==v)[0]
    normalDots.extend((N0[a]@N2[b].T).reshape(-1).tolist())
    skinDeltas.extend(np.max(abs(D0[a,None,:]-D2[None,b,:]),axis=2).reshape(-1).tolist())
    values=np.concatenate([D0[a],D2[b]]);aliasSpread.append(float(np.ptp(values,axis=0).max()))
# This is exactly render_cage_gray.py's material0 face selection in game axes.
neckMask=np.isin(G0,list(shared)).any(1)
shoeMask=(P0[T0,1]<.2).all(1)
grayMask=neckMask|shoeMask
def edges(faces):
    uses=defaultdict(list)
    for faceid,f in enumerate(faces):
        for j in range(len(f)):
            a,b=int(f[j]),int(f[(j+1)%len(f)])
            uses[tuple(sorted([a,b]))].append((faceid,a,b))
    return uses
def graph_components(edgelist):
    adj=defaultdict(set)
    for a,b in edgelist:adj[a].add(b);adj[b].add(a)
    pending=set(adj);components=[]
    while pending:
        start=min(pending);stack=[start];seen=set()
        while stack:
            v=stack.pop()
            if v in seen:continue
            seen.add(v);stack.extend(adj[v]-seen)
        pending-=seen;ordered=[]
        if all(len(adj[v])==2 for v in seen):
            prev=None;cur=min(seen)
            for _ in range(len(seen)):
                ordered.append(cur);nxt=min(adj[cur]-({prev} if prev is not None else set()))
                prev,cur=cur,nxt
            assert cur==ordered[0]
        components.append({'vertices':len(seen),'edges':sum(len(adj[v]) for v in seen)//2,
            'degreeHistogram':dict(Counter(len(adj[v]) for v in seen)),
            'orderedRing':ordered,'vertexIDs':sorted(seen),
            'boundsGame':[P[list(seen)].min(0).tolist(),P[list(seen)].max(0).tolist()]})
    return sorted(components,key=lambda c:-c['vertices'])
def topology(label,faces):
    uses=edges(faces);boundary=[e for e,u in uses.items() if len(u)==1]
    bad=[e for e,u in uses.items() if len(u)>2]
    orientedBad=[e for e,u in uses.items() if len(u)==2 and u[0][1:]==u[1][1:]]
    return {'label':label,'faces':len(faces),'uniqueVertices':len(np.unique(faces)),
        'boundaryEdges':len(boundary),'nonmanifoldEdges':len(bad),
        'sameDirectionSharedEdges':len(orientedBad),
        'boundaries':graph_components(boundary),'nonmanifoldEdgeIDs':bad}
allUses=edges(np.concatenate([G0,G2])); e0=edges(G0);e2=edges(G2)
seam=[e for e in e0 if e in e2]
seamComponents=graph_components(seam)
topos=[topology('originalBody0ExactWeld',G0),topology('protectedHood2ExactWeld',G2),
       topology('body0AndHood2ExactWeld',np.concatenate([G0,G2])),
       topology('temporaryGrayNeckPatch0ExactWeld',G0[neckMask]),
       topology('temporaryGrayNeckPlusHoodExactWeld',np.concatenate([G0[neckMask],G2]))]
f=np.load(CAGE);CP=f['positions'];CQ=f['quads']
# Native cage vertices are already geometrically unique; use separate ID namespace.
cEdges=edges(CQ);cBound=[e for e,u in cEdges.items() if len(u)==1]
oldP=P;P=CP;cLoops=graph_components(cBound);P=oldP
shirtLoops=[r for r in cLoops if r['boundsGame'][1][1]>.8]
# Identify collar geometrically by boundary mean/max height, not by rig weights.
collar=max(shirtLoops,key=lambda r:float(CP[r['vertexIDs'],1].mean()))
roles=[]
for c in seamComponents:
    v=c['vertexIDs']; roles.append({**c,'edgeIncidenceHistogram':dict(Counter(len(allUses[e]) for e in seam if e[0] in set(v))),
        'bodyAliases':[int(i) for i in np.where(np.isin(i0,v))[0]],
        'hoodAliases':[int(i) for i in np.where(np.isin(i2,v))[0]]})
rings={'indexContract':'Source IDs exact-weld global lexicographic float32 POSITION; primitiveAliases give literal GLB accessor IDs. Cage IDs literal fit04.npz positions/quads.',
       'sourceMaterialInterfaces':roles,'sourceTopology':topos,'cageBoundaryComponents':cLoops,'cageCollar':collar}
(OUT/'literal-rings.json').write_text(json.dumps(rings,indent=2)+'\n')
report={'status':'Read-only seam feasibility evidence; no mesh edits, appearance or rig acceptance',
    'source':str(SOURCE),'sourceSHA256':hashlib.sha256(raw).hexdigest(),
    'cage':str(CAGE),'cageSHA256':hashlib.sha256(CAGE.read_bytes()).hexdigest(),
    'fixtureRecipeSHA256':hashlib.sha256((REPO/'assets/blender/hero-remaster/rider/one-rider-v2/garment-rebuild01/render_cage_gray.py').read_bytes()).hexdigest(),
    'exactWeldRule':'No epsilon/rounding; np.unique float32 POSITION, duplicate UV/normals remain source aliases',
    'sourceBodyVertices':len(P0),'sourceHoodVertices':len(P2),'sharedExactPositions':len(shared),
    'bodySharedAccessorVertices':len(shared0),'materialSeamEdges':len(seam),
    'protectedInterfaceAttributes':{'dense19WeightMaxDelta':max(skinDeltas),
        'weightAliasMaxSpread':max(aliasSpread),
        'normalDotQuantiles':np.quantile(normalDots,[0,.5,.95,1]).tolist(),
        'note':'Material/UV aliases preserved; skin equality permits watertight moving aliases. New transition must copy protected seam weights; smooth normals require respecting actual hood boundary normals.'},
    'materialSeamComponents':[{k:v for k,v in r.items() if k not in ['orderedRing','vertexIDs','bodyAliases','hoodAliases']} for r in roles],
    'topologySummary':[{k:v for k,v in t.items() if k not in ['boundaries','nonmanifoldEdgeIDs']} for t in topos],
    'temporaryGrayBodyPatch':{'neckTouchFaces':int(neckMask.sum()),'shoeFaces':int(shoeMask.sum()),'totalFaces':int(grayMask.sum()),
        'rule':'Keep every triangle touching ANY body vertex exactly shared with hood, plus all-shoe triangles. This is a one-face incident-star patch, not a designed neck ring.'},
    'cageCollar':{k:v for k,v in collar.items() if k not in ['orderedRing','vertexIDs']},
    'limits':['Exact weld topology audit only; no rest/moving visual or deformation approval.',
              'Material aliases are not holes when exact-weld incidence is two; gray incident-star cut boundaries are artificial.',
              'Preserve original POSITION/UV/NORMAL/JOINTS/WEIGHTS for protected vertices, plus all source bytes.']}
# Feasibility-only face shells: remove actual collar-adjacent whole native quads
# in memory, not planar clipping. Keep every tested ring and rejection condition.
faceAdj=defaultdict(set)
for u in cEdges.values():
    if len(u)==2:
        a,b=u[0][0],u[1][0];faceAdj[a].add(b);faceAdj[b].add(a)
removed={i for i,q in enumerate(CQ) if set(q)&set(collar['vertexIDs'])}
nativeOriginalBoundaryVertices={v for e in cBound for v in e}
target=P[roles[0]['vertexIDs']];tree=cKDTree(target);shellRecords=[]
for shell in range(1,9):
    keep=np.ones(len(CQ),bool);keep[list(removed)]=False
    # Edges remain original native edges; new boundaries had TWO original faces.
    changedEdges=[e for e,u in edges(CQ[keep]).items() if len(u)==1 and len(cEdges[e])==2]
    oldP=P;P=CP;components=graph_components(changedEdges);P=oldP
    records=[]
    for c in components:
        pts=CP[c['vertexIDs']];nearest=tree.query(pts)[0]
        reverse=cKDTree(pts).query(target)[0]
        records.append({**c,'nativeToSourceRingDistanceQuantilesM':np.quantile(nearest,[0,.5,.95,1]).tolist(),
            'sourceToNativeRingDistanceQuantilesM':np.quantile(reverse,[0,.5,.95,1]).tolist(),
            'touchesOtherOriginalOpenings':bool(set(c['vertexIDs'])&(nativeOriginalBoundaryVertices-set(collar['vertexIDs'])))})
    shellRecords.append({'faceShellsFromCollar':shell,'removedQuadIDs':sorted(removed),'newBoundaryComponents':records})
    removed |= set().union(*(faceAdj[i] for i in removed))
(OUT/'native-transition-shells.json').write_text(json.dumps(shellRecords,indent=2)+'\n')
report['nativeFaceShellTests']=[{'faceShellsFromCollar':s['faceShellsFromCollar'],'removedQuads':len(s['removedQuadIDs']),
    'components':[{k:v for k,v in c.items() if k not in ['orderedRing','vertexIDs']} for c in s['newBoundaryComponents']]} for s in shellRecords]
assert SOURCE.read_bytes()==raw
(OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
