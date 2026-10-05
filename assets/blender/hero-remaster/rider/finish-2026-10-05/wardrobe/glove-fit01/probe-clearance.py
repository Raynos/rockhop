"""Scoped radial hit-gap witnesses; explicitly no signed occupancy certificate."""
import argparse
import json
from pathlib import Path
import numpy as np


def ray_hits(origin,direction,vertices,faces):
    t=vertices[faces];e1=t[:,1]-t[:,0];e2=t[:,2]-t[:,0]
    h=np.cross(np.broadcast_to(direction,e2.shape),e2);det=(e1*h).sum(1)
    eligible=np.abs(det)>1e-14;inv=np.zeros(len(det));inv[eligible]=1/det[eligible]
    delta=origin-t[:,0];u=(delta*h).sum(1)*inv;s=np.cross(delta,e1);v=(s*direction).sum(1)*inv
    distance=(e2*s).sum(1)*inv
    mask=eligible&(u>=-1e-9)&(v>=-1e-9)&(u+v<=1+1e-9)&(distance>1e-8)&(distance<.06)
    return np.unique(np.round(distance[mask],10))


def main():
    p=argparse.ArgumentParser();p.add_argument('--data',required=True);p.add_argument('--foundation',required=True)
    p.add_argument('--fit',required=True);p.add_argument('--out',required=True);a=p.parse_args()
    body=np.load(a.foundation);fit=json.loads(Path(a.fit).read_text());rows=[]
    for item in fit['items']:
        g=np.load(Path(a.data)/('glove-'+item['side']+'.npz'))
        for digit,info in item['stations'].items():
            for index in [6,16,26]:
                station=info['stations'][index];center=np.array(station['center']);frame=np.array(station['basisColumns'])
                for axis in [0,2]:
                    for sign in [-1,1]:
                        direction=frame[:,axis]*sign
                        gh=ray_hits(center,direction,g['vertices'],g['faces'])
                        bh=ray_hits(center,direction,body['canonicalXYZ'].astype(float),body['canonicalTriangles'])
                        rows.append({'side':item['side'],'digit':digit,'t':station['t'],'axis':axis,'sign':sign,
                                     'gloveSurfaceHitsM':gh.tolist(),'bodySurfaceHitsM':bh.tolist(),
                                     'firstSurfaceGapM':float(gh[0]-bh[0]) if len(gh) and len(bh) else None,
                                     'cavityClassified':False})
    gaps=[r['firstSurfaceGapM']for r in rows if r['firstSurfaceGapM']is not None]
    report={'accepted':False,'status':'REST_RADIAL_HIT_GAP_WITNESSES_ONLY','probes':rows,
            'minimumFirstSurfaceGapM':min(gaps),'negativeFirstSurfaceGapWitnesses':sum(g<0 for g in gaps),
            'missingBodyOrGloveHits':sum(r['firstSurfaceGapM']is None for r in rows),
            'limits':['First-positive surface hit comparison at named chain centers; 60mm raylimit.',
                      'Cannot classify inner/outer wall, initialinside/outside, solid occupancy, globalcavity or continuousclearance.',
                      'These negative gap witnesses corroborate finitecontacts; no fittedglove approval.']}
    Path(a.out).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items()if k not in ['probes','limits']}))


if __name__=='__main__':main()
