"""Fit the actual selected jeans through coherent cavity/pelvis section charts.

This is source deformation, not an offset-body garment. The original closed
material's inner and outer surfaces move together. No source vertex, fold,
face or master is replaced. Native fitting, collision and moving review follow.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
from scipy.interpolate import PchipInterpolator

ROOT = Path(__file__).resolve().parents[4]
SOURCE = ROOT / 'assets/blender/hero-remaster/rider/finish-2026-10-05/wardrobe/data/prep02/jeans/retopology-prototype.npz'
BODY = ROOT / 'docs/evidence/rider-rebuild/glove-charts01/target01/native-body.npz'
SECTION = ROOT / 'assets/blender/rider-rebuild/glove-charts01/audit-hand-anatomy.py'
PINS = {SOURCE:'6907492293a23765f49b41a64a65cbdf18a6e10b15cfd183416113352f759a49',
        BODY:'b34897b3c1fe810d7bd77806a1635f8132b3a43e66986986c218ab23cfad2f45',
        SECTION:'1bf0cd59073c83381980801a40a31b5b7f0837750034e2c8db8a616d6711f303'}
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
ROOM = .010
SOURCE_Y = np.array([-1.,-.85,-.12,.38,.54,.82,.974])
TARGET_Z = np.array([.160,.210,.543,.764,.800,.998,1.060])


def inside(points, polygon):
    a, b = polygon, np.roll(polygon,-1,axis=0)
    result=[]
    for p in points:
        crossing=(a[:,1]>p[1]) != (b[:,1]>p[1])
        denominator=b[:,1]-a[:,1]
        x=a[:,0]+(p[1]-a[:,1])*(b[:,0]-a[:,0])/np.where(denominator != 0,denominator,1)
        result.append(bool(np.count_nonzero(crossing & (x>p[0]))%2))
    return np.asarray(result)


def radii(polygon, center, angles):
    """First exit from an actual air/skin centre; multiple exits are recorded."""
    a=polygon-center; e=np.roll(polygon,-1,axis=0)-polygon
    directions=np.column_stack((np.cos(angles),np.sin(angles)))
    output=[]; counts=[]
    cross=lambda p,q:p[...,0]*q[...,1]-p[...,1]*q[...,0]
    for d in directions:
        denominator=cross(d,e)
        valid=np.abs(denominator)>1e-13
        t=np.divide(cross(a,e),denominator,out=np.zeros(len(a)),where=valid)
        u=np.divide(cross(a,d),denominator,out=np.zeros(len(a)),where=valid)
        hits=t[valid & (t>1e-10) & (u>=0) & (u<1)]
        assert len(hits), 'Actual section has no positive exit'
        counts.append(len(hits));output.append(float(hits.min()))
    return np.asarray(output),counts


def cavity(contours, side=None):
    eligible=[c for c in contours if (side is None and abs(c['centroid'][0])<.06)
        or (side is not None and c['centroid'][0]*side>.06)]
    eligible.sort(key=lambda c:-c['areaM2'])
    assert len(eligible)>=2,'No measured nested source cavity'
    outer=eligible[0]; plane=outer['polygon'][:,[0,2]]
    inners=[c for c in eligible[1:] if c['areaM2']>.35*outer['areaM2']
            and inside(c['polygon'][:,[0,2]],plane).all()]
    assert inners,'Source inner surface is not contained by its outer contour'
    selected=max(inners,key=lambda c:c['areaM2'])
    assert inside([selected['centroid'][[0,2]]],selected['polygon'][:,[0,2]])[0]
    return outer,selected


def curve(values, rows, key, query):
    data=np.asarray([row[key] for row in rows])
    # Endpoint continuation is explicitly constant. No extrapolated donor joint
    # or sliding vertex-local median establishes any chart centre.
    return PchipInterpolator(values,data,axis=0)(np.clip(query,values[0],values[-1]))


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--out',required=True)
    args=parser.parse_args();out=Path(args.out).resolve()
    assert out.is_relative_to(ROOT/'harness/out/rider-rebuild') and not out.exists()
    assert all(sha(p)==h for p,h in PINS.items()),'Pinned source changed'
    spec=importlib.util.spec_from_file_location('actual_sections',SECTION)
    section=importlib.util.module_from_spec(spec);spec.loader.exec_module(section)
    source=dict(np.load(SOURCE));body=dict(np.load(BODY))
    sv,sf=source['vertices'],source['faces'];bv,bf=body['vertices'],body['faces']
    longitudinal=PchipInterpolator(SOURCE_Y,TARGET_Z)
    assert np.all(longitudinal.derivative()(np.linspace(SOURCE_Y[0],SOURCE_Y[-1],1000))>0)
    angles=np.linspace(0,2*np.pi,128,endpoint=False)
    report={'accepted':False,'status':'RUNNING_SECTION_CHART_REGISTRATION',
        'inputs':[{'path':str(p),'sha256':h} for p,h in PINS.items()],
        'recipeSHA256':sha(__file__),'roomM':ROOM,'charts':{},
        'longitudinalKnots':{'sourceY':SOURCE_Y.tolist(),'nativeZ':TARGET_Z.tolist()},
        'limits':['Section-based registration only; no native garment or full collision/motion/art acceptance.',
            'Original true cavity/outer contours, not per-vertex medians or a replacement body shell.',
            'Crotch, rim, thickness, all-triangle intersections and actual moving fit require separate validation.']}
    out.mkdir(parents=True)
    witness={}
    try:
        chart_data={}
        for name,side,levels in [('left',1,np.linspace(-.84,.365,17)),
                ('right',-1,np.linspace(-.84,.365,17)),('pelvis',None,np.linspace(.605,.825,7))]:
            records=[]
            for index,y in enumerate(levels):
                outer,inner=cavity(section.all_contours(sv,sf,np.array([0,y,0]),np.array([0,1.,0])),side)
                z=float(longitudinal(y))
                candidates=section.all_contours(bv,bf,np.array([0,0,z]),np.array([0,0,1.]))
                if side is None:
                    candidates=[c for c in candidates if abs(c['centroid'][0])<.05]
                else:
                    candidates=[c for c in candidates if .06<c['centroid'][0]*side<.28]
                assert candidates,'No actual wearer section for source chart'
                target=max(candidates,key=lambda c:c['areaM2'])
                p=inner['polygon'][:,[0,2]]; center=inner['centroid'][[0,2]]
                # Source front+Z maps to native forward -Y; account for this
                # proper basis in all shape/enclosure calculations.
                q=target['polygon'][:,:2]*[1,-1];target_center=target['centroid'][:2]*[1,-1]
                extent=np.ptp(p,axis=0);target_extent=np.ptp(q,axis=0)+2*ROOM
                scales=target_extent/extent
                source_radius,source_hits=radii((p-center)*scales,np.zeros(2),angles)
                body_radius,body_hits=radii(q-target_center,np.zeros(2),angles)
                correction=float(np.max((body_radius+ROOM)/source_radius))
                scales*=max(1.,correction)
                actual_radius,_=radii((p-center)*scales,np.zeros(2),angles)
                assert np.min(actual_radius-body_radius)>=ROOM-1e-10
                row={'sourceY':float(y),'nativeZ':z,'sourceCenter':center.tolist(),
                    'targetCenter':target_center.tolist(),'radialScale':scales.tolist(),
                    'sourceOuterArea':outer['areaM2'],'sourceCavityArea':inner['areaM2'],
                    'targetArea':target['areaM2'],'minimumMeasuredRadialRoomM':float(np.min(actual_radius-body_radius)),
                    'sourceExitCounts':source_hits,'targetExitCounts':body_hits,
                    'sourceInnerEdges':inner['sourceEdges'],'sourceInnerEdgeFractions':inner['sourceEdgeFractions'],
                    'sourceOuterEdges':outer['sourceEdges'],'sourceOuterEdgeFractions':outer['sourceEdgeFractions'],
                    'bodyEdges':target['sourceEdges'],'bodyEdgeFractions':target['sourceEdgeFractions']}
                records.append(row)
                for kind,points in [('inner',inner['polygon']),('outer',outer['polygon']),('body',target['polygon'])]:
                    witness[name+'-'+str(index)+'-'+kind]=points
            report['charts'][name]=records;chart_data[name]=(levels,records)
        y=sv[:,1];base=sv[:,[0,2]]
        mapped={}
        for name,(levels,records) in chart_data.items():
            mapped[name]=curve(levels,records,'targetCenter',y)+(base-curve(levels,records,'sourceCenter',y))*curve(levels,records,'radialScale',y)
        # One continuous whole-garment field, including shared crotch vertices.
        # X interpolation is smooth across the centre plane; pelvis takeover is
        # smooth in source Y. No individual vertex has a moving sampling window.
        t=np.clip((sv[:,0]+.06)/.12,0,1);t=t*t*(3-2*t)
        legs=mapped['right']*(1-t[:,None])+mapped['left']*t[:,None]
        blend=np.clip((y-.365)/(.605-.365),0,1);blend=blend*blend*(3-2*blend)
        transverse=legs*(1-blend[:,None])+mapped['pelvis']*blend[:,None]
        current=np.column_stack((transverse[:,0],-transverse[:,1],longitudinal(y)))
        affine=np.eye(4);affine[:3,:3]=np.array([[1,0,0],[0,0,-1],[0,1,0]])*.42
        affine[:3,3]=[0,.012,.580]
        reference=sv@affine[:3,:3].T+affine[:3,3]
        assert np.isfinite(current).all() and np.array_equal(sf,source['faces'])
        np.savez_compressed(out/'registered-jeans.npz',referenceVertices=reference,vertices=current,faces=sf,
            sourceToNativeAffine=affine,originalSourceVertices=sv,sourceVertexIds=np.arange(len(sv)))
        np.savez_compressed(out/'section-witnesses.npz',**witness)
        report['registeredVertices']=len(current);report['preservedSourceTriangles']=len(sf)
        report['maximumDisplacementFromReferenceM']=float(np.linalg.norm(current-reference,axis=1).max())
        report['status']='ACTUAL_SOURCE_SECTION_CHART_CANDIDATE_UNACCEPTED'
        report['candidateSHA256']=sha(out/'registered-jeans.npz')
        report['witnessSHA256']=sha(out/'section-witnesses.npz')
        assert all(sha(p)==h for p,h in PINS.items())
    except BaseException as error:
        report['status']='REJECTED_SECTION_CHART_REGISTRATION';report['error']=type(error).__name__+': '+str(error)
        raise
    finally:
        (out/'registration.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'status':report['status'],'sourceVertices':len(sv),'sourceTriangles':len(sf)}))


if __name__=='__main__':main()
