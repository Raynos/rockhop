"""One raw-byte surface/normal/overlap control; no render or model inference."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
import numpy as np


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--native',required=True);parser.add_argument('--out',required=True)
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    assert os.environ.get('ROCKHOP_GENERATION_CONTROLLER_PID')
    expected='c9e0f72e6df3b2e2c8d2f8d81e989a644c8369b49e1bc845d9f1ebe41f5f8469'
    assert sha(args.native)==expected
    start=time.monotonic();out=Path(args.out);out.mkdir(exist_ok=False,parents=True)
    with np.load(args.native,allow_pickle=False) as raw:
        vertices=raw['vertices'].copy();faces=raw['faces'].copy()
    mesh=bpy.data.meshes.new('Frozen triangles; no render, cleanup or smoothing')
    mesh.vertices.add(len(vertices));mesh.loops.add(faces.size);mesh.polygons.add(len(faces))
    mesh.vertices.foreach_set('co',vertices.reshape(-1));mesh.loops.foreach_set('vertex_index',faces.reshape(-1))
    mesh.polygons.foreach_set('loop_start',np.arange(len(faces),dtype=np.int32)*3)
    mesh.polygons.foreach_set('loop_total',np.full(len(faces),3,np.int32))
    mesh.polygons.foreach_set('use_smooth',np.ones(len(faces),dtype=bool));mesh.update()
    co=np.empty(vertices.size,np.float32);indices=np.empty(faces.size,np.int32)
    mesh.vertices.foreach_get('co',co);mesh.loops.foreach_get('vertex_index',indices)
    assert np.array_equal(co,vertices.reshape(-1)) and np.array_equal(indices,faces.reshape(-1))
    del co,indices
    normals=np.empty(vertices.size,np.float32);mesh.vertices.foreach_get('normal',normals);normals=normals.reshape(-1,3)
    face_normals=np.empty(faces.size,np.float32);mesh.polygons.foreach_get('normal',face_normals);face_normals=face_normals.reshape(-1,3)
    obj=bpy.data.objects.new('Raw control',mesh);bpy.context.collection.objects.link(obj)
    graph=bpy.context.evaluated_depsgraph_get();tree=BVHTree.FromObject(obj,graph,epsilon=0)
    # Fixed central chest/back rectangle in native coordinates. No region sweep.
    # Fixed strips include waist through upper chest; sleeves/hood excluded.
    xs=np.linspace(-.13,.13,65);zs=np.linspace(-.18,.22,201)
    results={};arrays={'x':xs,'z':zs}
    for label,sign in [('front',1),('back',-1)]:
        depth=np.full((len(zs),len(xs)),np.nan,np.float32)
        smooth=np.full((*depth.shape,3),np.nan,np.float32);flat=smooth.copy()
        first_faces=np.full(depth.shape,-1,np.int32);gap=np.full(depth.shape,np.nan,np.float32)
        for iz,z in enumerate(zs):
            for ix,x in enumerate(xs):
                origin=Vector((x,-sign*.75,z));direction=Vector((0,sign,0))
                hit,normal,index,distance=tree.ray_cast(origin,direction,1.5)
                if hit is None:continue
                depth[iz,ix]=hit.y;flat[iz,ix]=face_normals[index];first_faces[iz,ix]=index
                tri=vertices[faces[index]].astype(np.float64);p=np.array(hit,dtype=np.float64)
                e0,e1=tri[1]-tri[0],tri[2]-tri[0];q=p-tri[0]
                a,b,c=np.dot(e0,e0),np.dot(e0,e1),np.dot(e1,e1)
                denominator=a*c-b*b
                if denominator>1e-24:
                    u=(c*np.dot(q,e0)-b*np.dot(q,e1))/denominator
                    v=(a*np.dot(q,e1)-b*np.dot(q,e0))/denominator
                    n=normals[faces[index]].astype(np.float64)
                    interpolated=(1-u-v)*n[0]+u*n[1]+v*n[2]
                    length=np.linalg.norm(interpolated)
                    if length>0:smooth[iz,ix]=interpolated/length
                # Second inward surface hit, epsilon explicit, no mesh edits.
                second,_,_,d=tree.ray_cast(hit+direction*1e-6,direction,.2)
                if second is not None:gap[iz,ix]=d+1e-6
        valid=np.isfinite(depth);matched=np.isfinite(smooth).all(axis=-1)
        dot=np.clip(np.sum(flat[matched]*smooth[matched],axis=-1),-1,1)
        angle=np.degrees(np.arccos(dot))
        # A physical relief control independent of normals/material/lighting:
        # central-strip Y depth minus fixed31-row moving mean (~.062native Z).
        centre=depth[:,32].astype(np.float64);assert np.isfinite(centre).all()
        trend=np.convolve(np.pad(centre,(15,15),mode='edge'),np.ones(31)/31,mode='valid')
        relief=centre-trend
        local_extrema=np.where(np.diff(np.sign(np.diff(relief)))!=0)[0]+1
        results[label]={'hitRays':int(valid.sum()),'totalRays':int(valid.size),
            'region':{'x':[-.13,.13],'z':[-.18,.22],'rows':201,'columns':65},
            'faceVsAveragedNormalDegrees':{'median':float(np.median(angle)),'p95':float(np.percentile(angle,95)),'max':float(angle.max())},
            'centreStripDepthPeakToPeak':float(np.ptp(centre)),
            'centreStripReliefPeakToPeak':float(np.ptp(relief)),
            'centreStripReliefRMS':float(np.sqrt(np.mean(relief**2))),
            'centreStripReliefExtrema':len(local_extrema),
            'secondHitWithinQuarterVoxel':int((gap<1/4096).sum()),
            'secondHitWithinTwoVoxels':int((gap<2/1024).sum()),
            'secondHitMeasuredRays':int(np.isfinite(gap).sum()),
            'rayAdvanceEpsilon':1e-6}
        arrays.update({label+'Depth':depth,label+'FaceNormals':flat,label+'AveragedNormals':smooth,
                       label+'FirstFace':first_faces,label+'SecondHitGap':gap,label+'CentreRelief':relief})
    # Preserve raw sampled diagnostic bytes; NaN denotes explicit ray no-hit,
    # never a numerical model acceptance criterion.
    archive=out/'surface-control.npz';np.savez_compressed(archive,**arrays)
    report={'accepted':False,'nativeSHA256':sha(args.native),'recipeSHA256':sha(__file__),
            'rawVertices':len(vertices),'rawFaces':len(faces),'loadedArraysByteIdentical':True,
            'controls':results,'archiveSHA256':sha(archive),'elapsedSeconds':time.monotonic()-start,
            'renderOrInferenceCalls':0,'geometryChanges':False,
            'limits':['Fixed central ray rectangle only, not whole-mesh watertightness or intersection certification.',
                      'Second-hit proximity can also represent legitimate thickness; not by itself proof of overlap.',
                      'Relief includes genuine folds and does not identify the exact bands root sees in the played film.',
                      'Normal discrepancy is measured, not a renderer-bug verdict. Root owns played interpretation.']}
    assert report['nativeSHA256']==expected
    (out/'receipt.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))


if __name__=='__main__':main()
