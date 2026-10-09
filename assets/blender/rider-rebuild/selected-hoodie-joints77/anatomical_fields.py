"""Explicit anatomical shoulder painting; no all-support field diffusion.

The exact09 domain is retained. Original08 fields remain outside it. Inside,
own-side clavicle/arm and actual thoracic supports are deliberately painted.
Full canonical71 control inventory remains; this is not a production-four map.
"""
import json
from pathlib import Path
import runpy
import sys
import numpy as np

HERE=Path(__file__).resolve().parent
A=runpy.run_path(str(HERE/'author.py'));ROOT=A['ROOT'];pin=A['pin'];checked=A['checked']
REPAIR={'path':'assets/blender/rider-rebuild/selected-hoodie-joints77/field_repair.py',
        'sha256':'ce027c64927dfb571bf8c1b1edb5502b619daf9749f78af8ae845a68b14f26e4'}
INPUT={'path':'harness/out/rider-rebuild/selected-hoodie-joints77/receiver09/receiver.json',
       'sha256':'0ba4e267c98620a95e0ce60ada4288d5fa768116d2daf6070a607d6b9cd494bd'}


def smooth(x):
    x=np.clip(x,0.,1.);return x*x*(3-2*x)


def target(point,side,rest,names):
    bones={r[0]:r for r in rest};frame,lengths=A['bone_frame'](rest,side)
    origin,axis,_,_=frame(0);station=float((point-origin)@axis)
    # Center shoulder rotation on its real bind joint. The paint transition
    # ends half a proximal native upper-arm segment below that joint, before
    # the measured89mm axilla rows and the145mm first ordinary sleeve loop.
    proximal=bones['DEF-upper_arm.'+side]
    width=.5*np.linalg.norm(np.asarray(proximal[3])-proximal[2])
    arm=float(smooth((station+width)/(2*width)))
    thoracic=['DEF-spine.001','DEF-spine.002','DEF-spine.003']
    heights=np.asarray([(bones[n][2][2]+bones[n][3][2])*.5 for n in thoracic])
    spine=np.zeros(len(names));z=float(point[2])
    if z<=heights[0]:spine[names.index(thoracic[0])]=1.
    elif z>=heights[-1]:spine[names.index(thoracic[-1])]=1.
    else:
        j=int(np.searchsorted(heights,z)-1);t=float(smooth((z-heights[j])/(heights[j+1]-heights[j])))
        spine[names.index(thoracic[j])]=1-t;spine[names.index(thoracic[j+1])]=t
    shoulder='DEF-shoulder.'+side;bone=bones[shoulder]
    head=np.asarray(bone[2]);line=np.asarray(bone[3])-head
    clavicle=float(smooth(np.dot(point-head,line)/np.dot(line,line)))
    torso=(1-clavicle)*spine;torso[names.index(shoulder)]+=clavicle
    fields=(1-arm)*torso+arm*A['limb_fields'](point,side,rest,names)
    return fields,arm,width


def verify(receipt_path):
    row=json.loads(Path(receipt_path).read_text());repair=row['anatomicalFieldRepair']
    assert repair['recipe']==pin(__file__)and repair['input']==INPUT
    assert repair['status']=='ANATOMICALLY_AUTHORED_SHOULDER_FIELDS_UNACCEPTED'
    R=runpy.run_path(str(checked(REPAIR)));source=R['verify'](checked(INPUT))
    before=np.load(checked(source['receiver']));after=np.load(checked(row['receiver']))
    for key in before.files:
        if key not in ('namedFields','priorNamedFields'):assert np.array_equal(before[key],after[key]),key
    assert np.array_equal(after['priorNamedFields'],before['namedFields'])
    assert np.array_equal(after['field09PriorNamedFields'],before['priorNamedFields'])
    active=before['fieldRepairActive']
    assert after['namedFields'].shape==before['namedFields'].shape and after['namedFields'].dtype==np.float32
    assert np.array_equal(after['namedFields'][~active],before['priorNamedFields'][~active])
    assert np.isfinite(after['namedFields']).all()and after['namedFields'].min()>=0
    assert np.max(abs(after['namedFields'].sum(1)-1))<3e-7
    checked(repair['diagnostic']);return row


def main(output):
    output=Path(output).resolve()
    assert output.is_relative_to(ROOT/'harness/out/rider-rebuild/selected-hoodie-joints77')and not output.exists()
    R=runpy.run_path(str(checked(REPAIR)));source=R['verify'](checked(INPUT))
    a=dict(np.load(checked(source['receiver'])));rest=json.loads(checked(source['source47Receipt']).read_text())['expectedRest']
    p=a['positions'];roles=a['vertexRoles'];names=a['groupNames'].tolist();active=a['fieldRepairActive']
    _,_,neighbors=R['graph'](a)
    source_rows=(roles=='selected_original')|(roles=='armhole_seam')
    source_graph=[[(j,d)for j,d in edges if source_rows[j]]if source_rows[i]else[]for i,edges in enumerate(neighbors)]
    seam=np.flatnonzero(roles=='armhole_seam');far=np.flatnonzero(source_rows&~active)
    ds=R['distances'](source_graph,seam);df=R['distances'](source_graph,far)
    paint=np.ones(len(p));collar=active&(roles=='selected_original')
    assert np.isfinite(ds[collar]).all()and np.isfinite(df[collar]).all()
    paint[collar]=smooth(df[collar]/(df[collar]+ds[collar]))
    paint[~active]=0.
    previous=a['namedFields'].copy();baseline=a['priorNamedFields'].copy();fields=baseline.copy()
    arm=np.zeros(len(p));widths={};anatomical=np.zeros_like(fields)
    for vi in np.flatnonzero(active):
        side='L'if p[vi,0]>0 else'R'
        row,arm[vi],widths[side]=target(p[vi],side,rest,names)
        anatomical[vi]=row;fields[vi]=(1-paint[vi])*baseline[vi]+paint[vi]*row
    assert np.isfinite(fields).all()and fields.min()>=0 and np.max(abs(fields.sum(1)-1))<3e-7
    a.update(namedFields=fields,priorNamedFields=previous,field09PriorNamedFields=baseline,
             anatomicalPaintAmount=paint,anatomicalUpperArmBlend=arm,anatomicalTargetFields=anatomical)
    output.mkdir(parents=True);np.savez(output/'receiver.npz',**a)
    counts,frequency=np.unique((fields>0).sum(1),return_counts=True)
    report={'acceptedArt':False,'input':INPUT,'recipe':pin(__file__),'activeVertices':int(active.sum()),
        'sourceCollarVertices':int(collar.sum()),'geometryUVAncestryUnchanged':True,
        'original08FieldsExactOutsideDomain':bool(np.array_equal(fields[~active],baseline[~active])),
        'shoulderHalfTransitionWidthM':widths,'supportCountHistogram':{str(k):int(v)for k,v in zip(counts,frequency)},
        'method':'Anatomically authored own-side clavicle/upper/forearm plus native thoracic001/002/003. Shoulder transition centered on real upper-arm bind head; complete half a proximal segment below it. Scalar distance taper into exact08 source collar; no field diffusion.',
        'controlInventory':len(names),'productionFourConditioned':False,
        'limits':'Intentional local field reassignment, not equivalent-bone coalescence. Full named controls retained. Actual482, generic/heldout, finite contact and native/GPU/played evidence remain required.'}
    (output/'anatomical-fields.json').write_text(json.dumps(report,indent=2)+'\n')
    row=dict(source);row['receiver']=pin(output/'receiver.npz');row['priorFieldRepair']=row.pop('fieldRepair')
    row['anatomicalFieldRepair']={'status':'ANATOMICALLY_AUTHORED_SHOULDER_FIELDS_UNACCEPTED',
        'input':INPUT,'recipe':pin(__file__),'diagnostic':pin(output/'anatomical-fields.json')}
    row['correspondenceAndSkin']=dict(source['correspondenceAndSkin'],skinStatus=report['method'],
        healthyFieldsExactBeforeFloat32=False,sourceFarFieldAnchorsExact=True)
    row['limitations']=[*source['limitations'],'Local anatomical control weights were deliberately reassigned; no production-four equivalence or art/contact pass follows.']
    (output/'receiver.json').write_text(json.dumps(row,indent=2)+'\n');verify(output/'receiver.json')
    print(json.dumps(report),flush=True)


if __name__=='__main__':main(sys.argv[1])
