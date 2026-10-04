"""Connect actual selected donor displacement vectors on the qualified seed.

Scalar smoothing leaves radial directions disconnected at the underarm.
This changes the connected quantity, not the source, topology or parameters.
"""
import argparse,hashlib,json,sys
from pathlib import Path
import bpy,numpy as np
ap=argparse.ArgumentParser(description=__doc__)
for k in ['source','field','out','evidence']:ap.add_argument('--'+k,required=True)
a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);source,field_path,out,evidence=[Path(getattr(a,k)).resolve() for k in ['source','field','out','evidence']]
out.mkdir(parents=True,exist_ok=True);evidence.mkdir(parents=True,exist_ok=True)
assert not (out/'connected-vector.blend').exists(),'Frozen candidate exists'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();pins={str(p):sha(p) for p in [source,field_path]}
assert pins[str(source)]=='3859ffbe0716d1a6d87705c8f84fc4838527128b509ebc9244042199dcf91d34'
bpy.ops.wm.open_mainfile(filepath=str(source));original=bpy.data.objects['Selected Hunyuan radial exterior wearable, unrigged']
data=np.load(field_path);seed=data['seedXYZ'];edges=data['edges'];direction=data['direction'];ease=data['boundaryEase']
target=direction*data['targetRelief'][:,None];field=np.zeros_like(seed);degree=np.zeros(len(seed))
np.add.at(degree,edges[:,0],1);np.add.at(degree,edges[:,1],1)
weight=8.;iterations=40
for step in range(iterations):
    accum=np.zeros_like(field);np.add.at(accum,edges[:,0],field[edges[:,1]]);np.add.at(accum,edges[:,1],field[edges[:,0]])
    field=(target+weight*accum)/(1+weight*degree[:,None])*ease[:,None]
assert np.linalg.norm(field,axis=1).max()<=.025+1e-12
garment=original.copy();garment.data=original.data.copy();garment.name='Selected Hunyuan connected vector wearable, unrigged';bpy.context.collection.objects.link(garment)
final=seed+field
for vertex,p in zip(garment.data.vertices,final):vertex.co=p
garment.data.update();original.hide_render=True;original.hide_set(True)
garment['accepted']=False;garment['constructionStage']='Selected high-poly connected vector exterior/actual PBR, unrigged; independent static/game/art qualification pending'
bpy.ops.wm.save_as_mainfile(filepath=str(out/'connected-vector.blend'),compress=True)
assert pins=={p:sha(p) for p in pins}
np.savez_compressed(out/'connected-vector.npz',seedXYZ=seed,finalXYZ=final,targetDisplacement=target,connectedDisplacement=field,
                    direction=direction,boundaryEase=ease,edges=edges,region=data['region'],sourceTriangle=data['sourceTriangle'],barycentric=data['barycentric'])
report={'status':'UNACCEPTED connected selected-source vector exterior/PBR',
        'pins':pins,'recipeSHA256':sha(__file__),'candidateSHA256':sha(out/'connected-vector.blend'),'fieldSHA256':sha(out/'connected-vector.npz'),
        'sourceTargets':'Exact source10selected high-poly outward radial target vectors; same qualified09seed/opening/collar constraints, connection40steps/weight8',
        'change':'Connect all3 displacement coordinates across sewn edges; do not multiply smoothed lengths by unsmoothed directions',
        'iterations':iterations,'connectionWeight':weight,'maximumDisplacementM':float(np.linalg.norm(field,axis=1).max()),
        'boundaryMaximumDisplacementM':float(np.linalg.norm(field[ease==0],axis=1).max()),
        'textures':'Exact selected-donor source10UV/base/roughness/metallic atlas retained; garment rest geometry morph only',
        'limits':['Connected vector sculpt is static construction, not skinning, cloth or consumed live collision.',
                  'No injectivity/body clearance/coverage is inferred from connectivity; independent audit required.',
                  'All original body/head/51bind/failed controls preserved. Root alone judges played art; all M0-M5 open, no player/Library handoff.']}
(evidence/'construction.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:report[k] for k in ['maximumDisplacementM','boundaryMaximumDisplacementM']}),flush=True)
