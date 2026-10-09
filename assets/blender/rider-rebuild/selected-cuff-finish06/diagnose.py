"""Read exact glove witnesses against the actual selected hoodie, rest and played.

Offline geometric/weight attribution only. Counterfactual field substitution is
reported as displacement, never saved as authored geometry or an accepted fix.
Run inside the original queue + bounded96 guard with Blender Python.
"""
import bpy, hashlib, json, sys
from pathlib import Path
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

DTYPES={5120:'i1',5121:'u1',5122:'<i2',5123:'<u2',5125:'<u4',5126:'<f4'}
WIDTH={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}

def digest(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(root,c,name):
    meta=c['attributes'][name]; raw=(root/c['name']/(name+'.bin')).read_bytes()
    assert hashlib.sha256(raw).hexdigest()==meta['decodedSHA256']
    a=np.frombuffer(raw,DTYPES[meta['componentType']]).reshape(meta['count'],WIDTH[meta['type']])
    if meta.get('normalized'): a=np.maximum(-1,a.astype(float)/np.iinfo(a.dtype).max)
    return a

def skin(p,j,w,mat):
    hom=np.column_stack([p,np.ones(len(p))]); result=np.zeros((len(p),3))
    for k in range(4): result+=np.einsum('nij,nj->ni',mat[j[:,k],:3,:],hom)*w[:,k,None]
    return result

def bary(p,t):
    a,b=t[1]-t[0],t[2]-t[0]; v=p-t[0]
    q=np.linalg.lstsq(np.column_stack([a,b]),v,rcond=None)[0]
    return np.r_[1-q.sum(),q]

def main(intake_path,played_path,witness_path,output_path):
    root=Path(intake_path); output=Path(output_path); assert not output.exists()
    receipt=json.loads((root/'intake.json').read_text()); played=json.loads(Path(played_path).read_text())
    witnesses=json.loads(Path(witness_path).read_text()); components={}
    for c in receipt['components']:
        a={key:read(root,c,key) for key in ['POSITION','JOINTS_0','WEIGHTS_0','indices','inverseBindMatrices']}
        a['indices']=a['indices'].reshape(-1,3); a['ib']=a.pop('inverseBindMatrices').reshape(-1,4,4).transpose(0,2,1).astype(float)
        a['names']=c['nativeJointNames']; components[c['name']]=a
    h=components['RiderHoodie']; output_rows=[]
    repo=Path(__file__).resolve().parents[4]
    config=json.loads((repo/'assets/blender/rider-rebuild/selected-ankle-field42/input.json').read_text())
    body_sources={k:config['sources'][k] for k in ['reference','canonicalFields','originalBody']}
    for pin in body_sources.values(): assert digest(repo/pin['path'])==pin['sha256']
    ref=np.load(repo/body_sources['reference']['path']); key='RiderBody__FullAnatomyReference'
    body_rest=ref[key+'_basis']; body_faces=ref[key+'_triangles']; body_ids=ref[key+'__SOURCE_VERTEX_ID']
    original=np.load(repo/body_sources['originalBody']['path'])
    body_names=original['jointNames'].tolist(); named=json.loads((repo/body_sources['canonicalFields']['path']).read_text())
    assert len(named)==len(body_rest)
    body_fields=np.array([[row.get(name,0.) for name in h['names']] for row in named])
    relevant=[i for i,name in enumerate(h['names']) if any(part in name for part in ['forearm','hand','palm','thumb','f_index','f_middle','f_ring','f_pinky'])]
    wrist_rows=np.flatnonzero(body_fields[:,relevant].sum(1)>.5)
    assert np.array_equal(body_rest[wrist_rows],original['vertices'][body_ids[wrist_rows]]), 'Actual wearer wrist basis must be identical'
    original_fields=original['nativeCoefficients'][body_ids[wrist_rows]]
    for bi,name in enumerate(h['names']):
        if name in body_names:
            assert np.array_equal(body_fields[wrist_rows,bi],original_fields[:,body_names.index(name)]), name
    body=body_rest[:,[0,2,1]].copy(); body[:,2]*=-1
    body_tree=BVHTree.FromPolygons(body.tolist(),body_faces.tolist(),all_triangles=True)
    for tick in sorted(set(w['tick'] for w in witnesses)):
        sample=next(p for p in played['played']['motionSamples'] if p['tick']==tick)
        byname={j['id']:j['worldMatrix'] for j in sample['joints']}
        world=np.array([byname[n] for n in h['names']]).reshape(-1,4,4).transpose(0,2,1)
        mat=world@h['ib']; hp=skin(h['POSITION'],h['JOINTS_0'],h['WEIGHTS_0'],mat)
        trees={state:BVHTree.FromPolygons(points.tolist(),h['indices'].tolist(),all_triangles=True) for state,points in [('rest',h['POSITION']),('played',hp)]}
        for witness in [w for w in witnesses if w['tick']==tick]:
            c=components[witness['component']]; rows=c['indices'][witness['triangle']]
            p=c['POSITION'][rows]; jj=c['JOINTS_0'][rows]; ww=c['WEIGHTS_0'][rows]
            cp=skin(p,jj,ww,mat); corners=[]
            side=witness['component'][-1]; wrist=c['names'].index('DEF-hand.'+side)
            forearm=c['names'].index('DEF-forearm.'+side+'.001')
            rest_world=np.linalg.inv(c['ib']); head=rest_world[wrist,:3,3]
            axis=head-rest_world[forearm,:3,3]; axis/=np.linalg.norm(axis)
            for k,row in enumerate(rows):
                item={'vertex':int(row),'restPosition':p[k].tolist(),'playedPosition':cp[k].tolist(),
                      'anatomicalWristStationMeters':float((p[k]-head)@axis),
                      'skin':[{ 'joint':c['names'][int(j)],'weight':float(w)} for j,w in zip(jj[k],ww[k]) if w>0]}
                for state,point,hoodie in [('rest',p[k],h['POSITION']),('played',cp[k],hp)]:
                    hit,normal,face,distance=trees[state].find_nearest(Vector(point))
                    hi=h['indices'][face]; bc=bary(np.array(hit),hoodie[hi]); field=np.zeros(len(c['names']))
                    for idx,fraction in zip(hi,bc):
                        for joint,weight in zip(h['JOINTS_0'][idx],h['WEIGHTS_0'][idx]): field[joint]+=fraction*weight
                    alternative=np.zeros(3); hom=np.r_[p[k],1.]
                    for joint in np.flatnonzero(field): alternative+=field[joint]*(mat[joint]@hom)[:3]
                    item[state]={'hoodieTriangle':int(face),'hoodieRows':hi.tolist(),'distanceMeters':float(distance),
                        'nearestPoint':list(hit),'geometricNormal':list(normal),'normalSignedDistanceMeters':float((point-np.array(hit))@normal),
                        'barycentric':bc.tolist(),'hoodieField':[{ 'joint':c['names'][int(j)],'weight':float(field[j])} for j in np.flatnonzero(field)],
                        'commonFieldCounterfactualPlayedDisplacementMeters':float(np.linalg.norm(alternative-cp[k]))}
                hit,normal,face,distance=body_tree.find_nearest(Vector(p[k]))
                bi=body_faces[face]; bc=bary(np.array(hit),body[bi]); field=bc@body_fields[bi]
                item['canonicalWearerRest']={'triangle':int(face),'rows':bi.tolist(),
                    'distanceMeters':float(distance),'normalSignedDistanceMeters':float((p[k]-np.array(hit))@normal),
                    'nearestPoint':list(hit),'barycentric':bc.tolist(),
                    'field':[{ 'joint':h['names'][int(j)],'weight':float(field[j])} for j in np.flatnonzero(field)]}
                corners.append(item)
            output_rows.append({**witness,'corners':corners})
    report={'accepted':False,'source':receipt['source'],'playedSHA256':digest(played_path),'witnessSHA256':digest(witness_path),'canonicalWearerSources':body_sources,'canonicalWristRowsVerified':len(wrist_rows),'results':output_rows,
        'limits':['Nearest hoodie sheet normal is local, not a global containment proof.','Rest and played nearest faces may differ.','Common-field displacement isolates weight disagreement without modifying source, and is not an authored correction.']}
    output.parent.mkdir(parents=True,exist_ok=True); output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'accepted':False,'witnesses':len(output_rows),'report':str(output)}))

if __name__=='__main__': main(*sys.argv[sys.argv.index('--')+1:])
