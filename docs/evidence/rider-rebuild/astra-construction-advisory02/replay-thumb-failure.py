"""Read-only author02 thumb-ray replay; Blender bundled Python, no bpy or job.
Run from repo root with /Applications/Blender.app/Contents/Resources/5.2/python/bin/python3.13.
This is a one-point diagnostic, not a garment fitting/acceptance algorithm.
"""
import json
from pathlib import Path
import numpy as np

root = Path(__file__).resolve().parents[4]
hand = np.load(root/'docs/evidence/rider-rebuild/glove-native02-fit/target01/native-hand-R.npz')
body = np.load(root/'docs/evidence/rider-rebuild/native-hand-repair01/native02/native-body.npz')
names = body['jointNames'].tolist()
head = lambda name: body['jointHeads'][names.index(name)]
tail = lambda name: body['jointTails'][names.index(name)]
unit = lambda vector: vector/np.linalg.norm(vector)
digits = ('pinky', 'ring', 'middle', 'index', 'thumb')
chains = [[f'DEF-{"thumb" if d == "thumb" else "f_"+d}.{i:02d}.R' for i in (1,2,3)] for d in digits]
vertices, faces = hand['vertices'].copy(), hand['faces']
normal = np.zeros_like(vertices)
area = np.cross(vertices[faces[:,1]]-vertices[faces[:,0]], vertices[faces[:,2]]-vertices[faces[:,0]])
for j in range(3):
    np.add.at(normal, faces[:,j], area)
normal /= np.linalg.norm(normal, axis=1)[:,None]
forward = unit(head('DEF-f_middle.01.R')-head('DEF-hand.R'))
radial = head('DEF-f_index.01.R')-head('DEF-f_pinky.01.R')
radial = unit(radial-forward*np.dot(radial,forward))
dorsal = unit(np.cross(radial,forward))
masses = np.stack([hand['fourCoefficients'][:,[names.index(x) for x in ch]].sum(1) for ch in chains],1)
labels = np.where(masses.max(1)>.28,masses.argmax(1),-1)
back = np.clip(normal@dorsal,0,1)
palm = np.clip(-normal@dorsal,0,1)
ease = .0016+back*.0014+palm*.0007
ease[labels<0] += back[labels<0]*.0012
for i, chain in enumerate(chains):
    mask = labels == i
    taper = np.clip(np.linalg.norm(vertices[mask]-tail(chain[-1]),axis=1)/.022,0,1)
    ease[mask] *= .72+.28*taper
vertices += normal*ease[:,None]
# Exact thumb first-panel row0/column4, as currently authored.
chain = chains[-1]
lengths = np.array([np.linalg.norm(tail(x)-head(x)) for x in chain])
starts = np.r_[0,np.cumsum(lengths)]
available = starts[-1]-.050
distance = .050+available*.17
segment = min(2,int(np.searchsorted(starts,distance,side='right')-1))
along = unit(tail(chain[segment])-head(chain[segment]))
center = head(chain[segment])+along*(distance-starts[segment])
outward = unit(dorsal-along*np.dot(dorsal,along))
point = center-along*available*.23/2
logged = np.array([-.38028483,-.15183215,.88416905])
origin, direction = point+outward*.024, -outward
edge1 = vertices[faces[:,1]]-vertices[faces[:,0]]
edge2 = vertices[faces[:,2]]-vertices[faces[:,0]]
pvec = np.cross(direction,edge2)
determinant = np.einsum('ij,ij->i',edge1,pvec)
inverse = np.divide(1.,determinant,out=np.zeros_like(determinant),where=abs(determinant)>1e-10)
tvec = origin-vertices[faces[:,0]]
u = np.einsum('ij,ij->i',tvec,pvec)*inverse
qvec = np.cross(tvec,edge1)
v = qvec@direction*inverse
t = np.einsum('ij,ij->i',edge2,qvec)*inverse
valid = (abs(determinant)>1e-10)&(u>=0)&(v>=0)&(u+v<=1)&(t>=0)&(t<=.048)
seeds = hand['sourceHandBranchSeeds']
support = np.any(seeds[faces]==4,axis=1)&~np.any((seeds[faces]>=0)&(seeds[faces]!=4),axis=1)
hits = []
for row in np.flatnonzero(valid)[np.argsort(t[valid])]:
    hits.append({'face':int(row),'vertices':faces[row].tolist(),'distanceM':float(t[row]),
                 'normalDotOutward':float(unit(np.cross(edge1[row],edge2[row]))@outward),
                 'thumbSupport':bool(support[row]),'seeds':seeds[faces[row]].tolist()})
assert [hit['face'] for hit in hits] == [279,283]
assert not hits[0]['thumbSupport'] and hits[0]['normalDotOutward']>.98
assert hits[1]['thumbSupport'] and hits[1]['normalDotOutward']<-.96
print(json.dumps({'acceptedArt':False,'sourceTrial':'glove author02, not guard01 pinky',
                  'point':point.tolist(),'differenceFromLoggedPointM':float(np.linalg.norm(point-logged)),
                  'digit':'thumb','panel':1,'row':0,'column':4,'hits':hits},indent=2))
