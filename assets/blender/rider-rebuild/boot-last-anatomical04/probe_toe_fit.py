"""Pinned read-only actual sculpt02/cavity diagnostic; parent CPU2 lease only.
No geometry/modifier mutation, save, bake or render. Canonical sample identity
matches the actual47-row witness. Scalar rays locate real selected outer walls.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import bpy
import numpy as np
from mathutils import Vector

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
C=json.loads((HERE/'sculpt-inputs.json').read_text())
NATIVE={'path':'harness/out/rider-rebuild/boot-last-anatomical04/sculpt02/anatomical-selected-boots.blend',
        'sha256':'c6d121b3ffb0b64c330f12d161f30567d6da6c4de0457517097a0b2c99fcb4d9'}
REPORT=ROOT/'harness/out/rider-rebuild/boot-last-anatomical04/sculpt02/report.json'


def sha(path):
    digest=hashlib.sha256()
    with Path(path).open('rb') as handle:
        while block:=handle.read(1024*1024):digest.update(block)
    return digest.hexdigest()


def pin(row):
    p=ROOT/row['path']
    assert sha(p)==row['sha256'],('Changed input',row['path'])
    return p


def triangle(mesh,row,frame,origin):
    p=mesh.polygons[row]
    return dict(faceRow=int(row),materialIndex=int(p.material_index),
        localVerticesM=((np.array([tuple(mesh.vertices[i].co) for i in p.vertices])-origin)@frame).tolist(),
        localNormal=(np.array(p.normal)@frame).tolist())


def main():
    args=sys.argv[sys.argv.index('--')+1:]
    assert len(args)==1
    out=Path(args[0]).resolve()
    assert out.is_relative_to(ROOT/'docs/evidence/rider-rebuild/boot-last-anatomical04') and not out.exists()
    report=json.loads(REPORT.read_text())
    source_pin=C['legacyHelpers']
    spec=importlib.util.spec_from_file_location('boot04_frozen_actual_probe_helpers',pin(source_pin))
    old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
    body=dict(np.load(pin(C['canonicalArrays'])))
    sections=json.loads(pin(C['sections']['R']).read_text())
    frame,origin=np.array(sections['footFrame']),np.array(sections['footOrigin'])
    vertices,faces=body['vertices'],body['faces']
    local=(vertices-origin)@frame
    mask=((local[:,0]>-.25)&(local[:,0]<.10)&(local[:,1]<C['cavityTopM'])&(local[:,1]>-.01)&(np.abs(local[:,2])<.10))
    vertex_ids=np.where(mask)[0]
    face_ids=np.where(np.all(mask[faces],axis=1))[0]
    samples=np.vstack((vertices[mask],vertices[faces[face_ids]].mean(1)))
    sample_local=(samples-origin)@frame
    raw=np.cross(vertices[faces[:,1]]-vertices[faces[:,0]],vertices[faces[:,2]]-vertices[faces[:,0]])
    face_normals=raw/np.linalg.norm(raw,axis=1)[:,None]
    vertex_normals=np.zeros_like(vertices)
    for corner in range(3):np.add.at(vertex_normals,faces[:,corner],raw)
    vertex_normals/=np.maximum(np.linalg.norm(vertex_normals,axis=1)[:,None],1e-20)
    sample_normals=np.vstack((vertex_normals[mask],face_normals[face_ids]))
    prior=report['sides']['R']['actualFootSurfaceWitness']
    assert len(samples)==prior['verticesAndTriangleCentroids']==3821
    bad=set(prior['insideLeatherSampleRows'])
    assert len(bad)==47
    bpy.ops.wm.open_mainfile(filepath=str(pin(NATIVE)))
    sculpt=bpy.data.objects['Boot04SelectedSurfaceSculpt.R']
    target=bpy.data.objects['Boot04SelectedAnatomical.R']
    cavity=bpy.data.objects['Boot04ContinuousInnerCavity.R']
    assert all(obj.matrix_world.is_identity for obj in (sculpt,target,cavity))
    trees={name:old.bvh(obj.data) for name,obj in [('sculpt',sculpt),('target',target),('cavity',cavity)]}
    out.mkdir(parents=True)
    result=dict(accepted=False,status='READ_ONLY_ACTUAL_TOE_CAVITY_PROBE',native=NATIVE,
        sourceSHA256=sha(__file__),controlsSHA256=sha(HERE/'sculpt-inputs.json'),
        actualReportSHA256=sha(REPORT),footFrame=frame.tolist(),footOrigin=origin.tolist(),
        priorLeatherRows=sorted(bad),priorLeatherSamples=[],outsideActualCavity=[],
        noSelectedOuterExitWithin80mm=[],selectedOuterExitWithinDeclared4mmEase=[],
        rayPolicy='At actual canonical surface position, follow its actual area-weighted anatomical normal. Record selected-shell crossings and first positively-facing outer exit,80mm maximum. No fitted normals or geometry edit.')
    def save():
        (out/'report.json').write_text(json.dumps(result,indent=2)+'\n')
    for i,(point,normal) in enumerate(zip(samples,sample_normals)):
        if sample_local[i,1]>C['coverageThroughHeightM']:
            continue
        entry=dict(sampleRow=i,canonicalVertexRow=int(vertex_ids[i]) if i<len(vertex_ids) else None,
            canonicalTriangleRow=None if i<len(vertex_ids) else int(face_ids[i-len(vertex_ids)]),
            localLongHeightTM=sample_local[i].tolist(),localAnatomicalNormal=(normal@frame).tolist())
        try:
            in_cavity=old.inside(trees['cavity'],point)
        except AssertionError as error:
            in_cavity=None;entry['cavityParityAmbiguity']=str(error)
        entry['insideActualCavity']=in_cavity
        p,_,row,distance=trees['cavity'].find_nearest(Vector(point))
        entry['nearestCavityBoundaryDistanceM']=float(distance)
        entry['nearestCavityFace']=triangle(cavity.data,int(row),frame,origin)
        crossings=[];cursor=Vector(point);direction=Vector(normal).normalized();travel=0.
        for _ in range(8):
            position,hit_normal,row,distance=trees['sculpt'].ray_cast(cursor,direction,.08-travel)
            if position is None:break
            travel+=float(distance)
            crossings.append(dict(distanceM=travel,normalDotAnatomicalOutward=float(hit_normal.dot(direction)),
                                  face=triangle(sculpt.data,int(row),frame,origin)))
            cursor=position+direction*1e-6;travel+=1e-6
            if travel>=.08:break
        entry['selectedShellCrossings']=crossings
        exits=[hit for hit in crossings if hit['normalDotAnatomicalOutward']>0.]
        entry['firstSelectedOuterExitM']=exits[0]['distanceM'] if exits else None
        if i in bad:
            p,_,row,distance=trees['target'].find_nearest(Vector(point))
            entry['actualLeatherNearestDistanceM']=float(distance)
            entry['actualLeatherNearestFace']=triangle(target.data,int(row),frame,origin)
            result['priorLeatherSamples'].append(entry)
        if in_cavity is False or in_cavity is None:result['outsideActualCavity'].append(entry)
        if not exits:result['noSelectedOuterExitWithin80mm'].append(entry)
        elif exits[0]['distanceM']<C['innerEaseM']:result['selectedOuterExitWithinDeclared4mmEase'].append(entry)
        result['lastActualSampleRow']=i
        if i%250==0:save()
    result['summaryCounts']={k:len(result[k]) for k in ['priorLeatherSamples','outsideActualCavity','noSelectedOuterExitWithin80mm','selectedOuterExitWithinDeclared4mmEase']}
    result['status']='READ_ONLY_ACTUAL_TOE_CAVITY_PROBE_COMPLETE'
    pin(NATIVE)
    save()
    print(json.dumps(result['summaryCounts']),flush=True)


if __name__=='__main__':main()
