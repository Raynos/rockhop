"""Fit the measured underarm seam corridor while retaining donor exterior.

True source fitting constraint: the tight sewn corridor keeps qualified seed
geometry, blended geodesically into selected-source exterior displacements.
This is neither an immutable whole-shirt constraint nor collision projection.
"""
import argparse,hashlib,heapq,json,sys
from pathlib import Path
import bpy,numpy as np
ap=argparse.ArgumentParser(description=__doc__)
for k in ['source','field','contacts','out','evidence']:ap.add_argument('--'+k,required=True)
a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);source,field_path,contacts,out,evidence=[Path(getattr(a,k)).resolve() for k in ['source','field','contacts','out','evidence']]
out.mkdir(parents=True,exist_ok=True);evidence.mkdir(parents=True,exist_ok=True)
assert not (out/'fitted-seam.blend').exists(),'Frozen candidate exists'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();pins={str(p):sha(p) for p in [source,field_path,contacts]}
assert pins[str(source)]=='96c0d90b437662e11dfb9a2386d2c61126538c1beec02db251e28674caf2f0bd'
bpy.ops.wm.open_mainfile(filepath=str(source));original=bpy.data.objects['Selected Hunyuan connected vector wearable, unrigged']
data=np.load(field_path);seed=data['seedXYZ'];edges=data['edges'];vector=data['connectedDisplacement'];witness=json.loads(contacts.read_text())
assert witness['pins'][str(source)]==pins[str(source)] and witness['selfPairs']==32
anchors=witness['contactVertices'];assert len(anchors)==40
adjacency=[[] for _ in seed]
for i,j in edges:
    length=float(np.linalg.norm(seed[i]-seed[j]));adjacency[i].append((int(j),length));adjacency[j].append((int(i),length))
distance=np.full(len(seed),np.inf);heap=[]
for i in anchors:distance[i]=0;heapq.heappush(heap,(0,i))
while heap:
    value,i=heapq.heappop(heap)
    if value!=distance[i]:continue
    for j,length in adjacency[i]:
        if value+length<distance[j]:distance[j]=value+length;heapq.heappush(heap,(distance[j],j))
width=.060;t=np.clip(distance/width,0,1);fit=t*t*(3-2*t)
field=vector*fit[:,None];final=seed+field
assert np.max(np.linalg.norm(field[anchors],axis=1))==0.
garment=original.copy();garment.data=original.data.copy();garment.name='Selected Hunyuan underarm fitted wearable, unrigged';bpy.context.collection.objects.link(garment)
for vertex,p in zip(garment.data.vertices,final):vertex.co=p
garment.data.update();original.hide_render=True;original.hide_set(True)
garment['accepted']=False;garment['constructionStage']='Actual selected exterior/PBR with measured underarm structural fit corridor, unrigged; independent source/rest/game/art qualification pending'
bpy.ops.wm.save_as_mainfile(filepath=str(out/'fitted-seam.blend'),compress=True)
assert pins=={p:sha(p) for p in pins}
np.savez_compressed(out/'underarm-fit.npz',seedXYZ=seed,finalXYZ=final,sourceDisplacement=vector,connectedDisplacement=field,
                    fitAnchors=np.array(anchors),geodesicDistance=distance,fitEase=fit,edges=edges,region=data['region'],
                    sourceTriangle=data['sourceTriangle'],barycentric=data['barycentric'])
report={'status':'UNACCEPTED actual selected-source wearable with local underarm structural fitting',
        'pins':pins,'recipeSHA256':sha(__file__),'candidateSHA256':sha(out/'fitted-seam.blend'),'fieldSHA256':sha(out/'underarm-fit.npz'),
        'fitAnchors':anchors,'anchorSource':'Exact40vertices from32source12shirt/shirt triangle contacts; qualified09seed retained only at tight underarm corridor',
        'geodesicBlendWidthM':width,'verticesInFitCorridor':int(sum(fit<1)),'totalVertices':len(seed),
        'maximumDisplacementM':float(np.linalg.norm(field,axis=1).max()),'outsideFitCorridorDisplacementsExact':bool(np.array_equal(field[fit==1],vector[fit==1])),
        'textures':'Actual selected-source10UV/base/roughness/metallic atlas unchanged; no plain-shirt appearance substitution',
        'limits':['Static anatomical seam fitting, not skinning or consumed live collision; whole triangle/body/coverage audit still required.',
                  'Selected-source geometry differs in explicit fitting corridor; no immutable whole-pattern acceptance constraint.',
                  'All original body/head/51bind and failed controls retained. Root alone judges played appearance, all M0-M5 open; no player/Library promotion.']}
(evidence/'construction.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:report[k] for k in ['verticesInFitCorridor','totalVertices','maximumDisplacementM','outsideFitCorridorDisplacementsExact']}),flush=True)
