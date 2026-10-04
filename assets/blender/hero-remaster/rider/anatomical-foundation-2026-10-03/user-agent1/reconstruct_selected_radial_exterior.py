"""Selected high-poly radial exterior relief and actual PBR on qualified seed.

No vertex snaps: preserve angle/station and sewn openings, solve a connected
bounded scalar relief, record exact source texture correspondence separately.
Static fit and played appearance still require independent qualification.
"""
import argparse, hashlib, heapq, json, math, sys
from pathlib import Path
import bpy, bmesh, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ap=argparse.ArgumentParser(description=__doc__)
for key in ['source','registration-recipe','bake-recipe','out','evidence']:ap.add_argument('--'+key,required=True)
a=ap.parse_args(sys.argv[sys.argv.index('--')+1:])
source, registration_recipe, bake_recipe, out, evidence=[Path(getattr(a,k.replace('-','_'))).resolve() for k in ['source','registration-recipe','bake-recipe','out','evidence']]
out.mkdir(parents=True,exist_ok=True); evidence.mkdir(parents=True,exist_ok=True)
assert not (out/'radial-exterior.blend').exists(),'Frozen candidate exists'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
pins={str(p):sha(p) for p in [source,registration_recipe,bake_recipe]}
assert pins[str(source)]=='304a446ce5acc3d41acef7e6b9ad30606aeee47bbf4204fc4f598c4817ab0a7f'
bpy.ops.wm.open_mainfile(filepath=str(source))
body=bpy.data.objects['Canonical anatomical body, baked adult hm08'];rig=bpy.data.objects['Independent anatomical foundation rig']
pattern=bpy.data.objects['Separate fitted sweatshirt control, hood not constructed']
seed=bpy.data.objects['Open-front hood structural seed, unrigged'];high=bpy.data.objects['Exact selected Hunyuan high-poly PBR donor, display frame only']
garment=seed.copy();garment.data=seed.data.copy();bpy.context.collection.objects.link(garment)
garment.name='Selected Hunyuan radial exterior wearable, unrigged';garment.data.materials.clear()
seed.hide_render=True;seed.hide_set(True)
definition=registration_recipe.read_text();definition=definition[definition.index('height=.472'):definition.index('lineage=[]')]
exec(compile(definition,str(registration_recipe),'exec'))
high.data.calc_loop_triangles();donortri=[tuple(t.vertices) for t in high.data.loop_triangles]
donorXYZ=np.array([list(v.co) for v in high.data.vertices],dtype=np.float64)
# Vectorize the frozen pure registration. Independent sampled scalar calls
# check axes, shoulder seam blend, nearest segment and unit conversion exactly.
registered=np.empty_like(donorXYZ)
for side, sign in [('R',1),('L',-1)]:
    ids=np.flatnonzero(donorXYZ[:,0]>=0 if sign==1 else donorXYZ[:,0]<0);p=donorXYZ[ids]
    torso=p@torso_matrix[:3,:3].T+torso_matrix[:3,3];s=source_anchors[side];target=target_anchors[side]
    fractions=[];centers=[];distances=[];arm_options=[]
    for seg in [0,1]:
        axis=s[seg+1]-s[seg];u=np.clip((p-s[seg])@axis/np.dot(axis,axis),0,1);center=s[seg]+u[:,None]*axis
        rotation=np.array(Vector(display_to_native@axis).rotation_difference(Vector(target[seg+1]-target[seg])).to_matrix())@display_to_native
        arm=target[seg]+u[:,None]*(target[seg+1]-target[seg])+(p-center)@rotation.T*.50
        fractions.append(u);centers.append(center);distances.append(np.linalg.norm(p-center,axis=1));arm_options.append(arm)
    arm=np.where((distances[0]<=distances[1])[:,None],arm_options[0],arm_options[1])
    distance=(np.abs(p[:,0])-.36)-np.maximum(.46-p[:,2],0)*.22;alpha=np.clip(distance/.15,0,1);alpha=alpha*alpha*(3-2*alpha)
    registered[ids]=(1-alpha[:,None])*torso+alpha[:,None]*arm
checks=np.linspace(0,len(donorXYZ)-1,257,dtype=int)
registration_error=max(np.linalg.norm(registered[i]-register(donorXYZ[i])[0]) for i in checks)
assert registration_error<1e-12,registration_error
print('REGISTERED_SELECTED_HIGH',len(registered),'error',registration_error,flush=True)
dt=BVHTree.FromPolygons([Vector(p) for p in registered],donortri,all_triangles=True)
body.data.calc_loop_triangles();bt=BVHTree.FromPolygons([v.co.copy() for v in body.data.vertices],[tuple(t.vertices) for t in body.data.loop_triangles],all_triangles=True)
pattern.data.calc_loop_triangles();patterntri=[tuple(t.vertices) for t in pattern.data.loop_triangles]
patternXYZ=np.array([list(v.co) for v in pattern.data.vertices]);pt=BVHTree.FromPolygons([Vector(p) for p in patternXYZ],patterntri,all_triangles=True)
pattern_arm=[]
for vertex in pattern.data.vertices:
    weights={pattern.vertex_groups[g.group].name:float(g.weight) for g in vertex.groups if pattern.vertex_groups[g.group].name in rig.data.bones}
    total=sum(weights.values());pattern_arm.append(sum(w for n,w in weights.items() if n.startswith(('upperArm.','forearm.')))/total if total else 0.)
seedXYZ=np.array([list(v.co) for v in garment.data.vertices]);edges=np.array([list(e.vertices) for e in garment.data.edges],dtype=int)
parents=np.array([item.value for item in garment.data.attributes['source_parent_polygon'].data]);region=np.zeros(len(seedXYZ),dtype=int)
for face in garment.data.polygons:
    group=0 if parents[face.index]<1204 else 1 if parents[face.index]<1224 else 2
    for i in face.vertices:region[i]=max(region[i],group)
direction=np.zeros_like(seedXYZ);target_relief=np.zeros(len(seedXYZ));donor_hits=[];no_positive_hit=[]
for i,p in enumerate(seedXYZ):
    torso_d=np.array([p[0]-.015,p[1],0.]);torso_d/=max(np.linalg.norm(torso_d),1e-12)
    if region[i]==0:
        nearest,normal,tri,distance=pt.find_nearest(Vector(p));pts=patternXYZ[list(patterntri[tri])]
        uv=np.linalg.lstsq(np.column_stack([pts[1]-pts[0],pts[2]-pts[0]]),np.array(nearest)-pts[0],rcond=None)[0]
        bary=np.clip([1-sum(uv),uv[0],uv[1]],0,1);bary/=sum(bary)
        alpha=float(bary@np.array([pattern_arm[j] for j in patterntri[tri]]))
        side='R' if p[1]>=0 else 'L';options=[]
        for name in ['upperArm.','forearm.']:
            bone=rig.data.bones[name+side];head=np.array(bone.head_local);axis=np.array(bone.tail_local)-head
            u=np.clip(np.dot(p-head,axis)/np.dot(axis,axis),0,1);center=head+u*axis;options.append((np.linalg.norm(p-center),center))
        radius,center=min(options,key=lambda q:q[0]);arm_d=(p-center)/max(radius,1e-12)
        d=(1-alpha)*torso_d+alpha*arm_d;d/=max(np.linalg.norm(d),1e-12)
    else:d=torso_d
    direction[i]=d
    # Outward source relief only. This is anatomical construction, not a
    # collision response and not an exact copy of the generated closed volume.
    origin=Vector(p-d*.045);travel=0.;hits=[]
    for step in range(12):
        q,n,tri,distance=dt.ray_cast(origin,Vector(d),.115-travel)
        if q is None:break
        travel+=float(distance);hits.append((q.copy(),int(tri)));origin=q+Vector(d)*1e-5;travel+=1e-5
        if travel>=.115:break
    if hits:
        q,tri=hits[-1];relief=float((np.array(q)-p)@d);target_relief[i]=np.clip(relief,0,.025)
        donor_hits.append({'vertex':i,'sourceTriangle':tri,'signedRadialReliefM':relief})
    else:no_positive_hit.append(i)
adjacency=[[] for _ in seedXYZ];degree=np.zeros(len(seedXYZ))
for j,k in edges:
    length=float(np.linalg.norm(seedXYZ[j]-seedXYZ[k]));adjacency[j].append((k,length));adjacency[k].append((j,length));degree[j]+=1;degree[k]+=1
count={}
for face in garment.data.polygons:
    ids=list(face.vertices)
    for j,k in zip(ids,ids[1:]+ids[:1]):e=tuple(sorted((j,k)));count[e]=count.get(e,0)+1
distance=np.full(len(seedXYZ),np.inf);heap=[]
for e,c in count.items():
    if c==1:
        for i in e:
            if distance[i]!=0:distance[i]=0;heapq.heappush(heap,(0,i))
while heap:
    value,i=heapq.heappop(heap)
    if value!=distance[i]:continue
    for j,length in adjacency[i]:
        if value+length<distance[j]:distance[j]=value+length;heapq.heappush(heap,(distance[j],j))
ease=np.clip(distance/.020,0,1);ease=ease*ease*(3-2*ease);ease[region==1]=0.
field=np.zeros(len(seedXYZ));weight=8.;iterations=40
for iteration in range(iterations):
    accum=np.zeros(len(field));np.add.at(accum,edges[:,0],field[edges[:,1]]);np.add.at(accum,edges[:,1],field[edges[:,0]])
    field=(target_relief+weight*accum)/(1+weight*degree);field*=ease
finalXYZ=seedXYZ+direction*field[:,None]
for vertex,p in zip(garment.data.vertices,finalXYZ):vertex.co=p
garment.data.update();finalcoords=[v.co.copy() for v in garment.data.vertices]
lineage=[]
for i,p in enumerate(finalXYZ):
    q,n,tri,distance=dt.find_nearest(Vector(p));ids=donortri[tri];pts=registered[list(ids)]
    uv=np.linalg.lstsq(np.column_stack([pts[1]-pts[0],pts[2]-pts[0]]),np.array(q)-pts[0],rcond=None)[0]
    bary=np.clip([1-sum(uv),uv[0],uv[1]],0,1);bary/=sum(bary)
    lineage.append({'vertex':i,'sourceTriangle':int(tri),'barycentric':bary.tolist(),
                    'donorDisplayXYZ':(bary@donorXYZ[list(ids)]).tolist()})
for o in bpy.data.objects:o.select_set(False)
garment.hide_set(False);garment.hide_render=False;garment.select_set(True);bpy.context.view_layer.objects.active=garment
# Reuse the exact protected selected-source bake only, not its failed geometry
# projection. Its SHA and our scalar/source correspondence are explicit inputs.
code=bake_recipe.read_text();code=code[code.index("bpy.ops.object.mode_set(mode='EDIT')"):code.index('gp=[v.co.copy()')]
print('BAKE_SELECTED_RADIAL_PBR',flush=True);exec(compile(code,str(bake_recipe),'exec'))
for face in garment.data.polygons:face.use_smooth=True
garment['accepted']=False;garment['constructionStage']='Selected donor connected radial relief/PBR, unrigged; independent static/game/art qualification pending'
bpy.ops.wm.save_as_mainfile(filepath=str(out/'radial-exterior.blend'),compress=True)
assert pins=={p:sha(p) for p in pins}
np.savez_compressed(out/'radial-correspondence.npz',seedXYZ=seedXYZ,finalXYZ=finalXYZ,direction=direction,
                    targetRelief=target_relief,connectedRelief=field,boundaryEase=ease,region=region,edges=edges,
                    sourceTriangle=np.array([r['sourceTriangle'] for r in lineage]),barycentric=np.array([r['barycentric'] for r in lineage]))
report={'status':'UNACCEPTED selected donor radial exterior and actual PBR candidate',
        'pins':pins,'recipeSHA256':sha(__file__),'candidateSHA256':sha(out/'radial-exterior.blend'),
        'fieldSHA256':sha(out/'radial-correspondence.npz'),'sourceDonorSHA256':'800d7a9717757b90b296a78c605cddb698c68d399a96e403aa381103e77d2eba',
        'registrationScalarSamples':len(checks),'registrationMaxErrorM':registration_error,
        'geometryMethod':'Connected nonnegative scalar relief along anatomical radial directions, angle/station and actual sewn openings retained; no independent XYZ snap',
        'reliefBoundM':.025,'iterations':iterations,'connectionWeight':weight,'boundaryGeodesicEaseM':.020,
        'maximumConnectedReliefM':float(field.max()),'p50ConnectedReliefM':float(np.percentile(field,50)),
        'positiveTargetVertices':int(sum(target_relief>0)),'noRayHitVertices':no_positive_hit,
        'donorRadialHits':donor_hits,'textures':textures,
        'limits':['Static source-derived construction is not skinning or consumed live collision; rest preflight still required.',
                  'Outward-only/bounded connected relief and fixed opening/collar constraints change selected source shape; PBR correspondence is exact selected-source lineage, not appearance acceptance.',
                  'All original body/head/51bind/control preserved; no normal-player/Library handoff. Root alone judges played art, all M0-M5 open.']}
(evidence/'construction.json').write_text(json.dumps(report,indent=2)+'\n');print('RADIAL_SELECTED_DONE',len(seedXYZ),float(field.max()),sum(target_relief>0),flush=True)
