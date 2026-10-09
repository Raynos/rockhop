"""Bounded read-only rest witnesses. Never calls cap_edit/main or saves a model."""
import json
from pathlib import Path
import runpy

import numpy as np

HERE = Path(__file__).resolve().parent
R = runpy.run_path(str(HERE/'refit.py'))
_, a, body, b, construction, _ = R['inputs']()
A = runpy.run_path(str(R['checked']('author')))
f, _, polygon = A['triangulate'](a)
rows, charts = [], {}
for side in ('L', 'R'):
    chart, detail = R['shoulder_chart'](side, b, body, construction, A)
    charts[side] = chart
    rows.append({'kind': 'chart', 'side': side, 'faces': len(detail['bodyTriangleIds']), 'seeds': detail['seedBodyTriangles']})
for triangle, side in ((28012, 'L'), (29669, 'R'), (26669, 'L'), (30969, 'R')):
    for vi in f[triangle]:
        strip = next(s for s in construction['strips'] if any(int(vi) in row for row in s['capRows']))
        ri = next(i for i,row in enumerate(strip['capRows']) if int(vi) in row)
        ci = strip['capRows'][ri].index(int(vi)); wall = strip['wall'].split(':')[1]
        other = next(s for s in construction['strips'] if s['side'] == side and s['wall'] != strip['wall'])
        frame,_ = A['bone_frame'](body['rest'], side); origin,_,forward,outward = frame(0)
        angles = {}
        for label,sp in (('own',strip),('other',other)):
            points = a['referencePositions'][sp['seamLoop']]-origin
            angles[label] = np.arctan2(points@outward, points@forward) % (2*np.pi)
        partner, ids, t = R['periodic_partner'](float(angles['own'][ci]), angles['other'], other['capRows'][ri], a['positions'])
        midpoint = (a['positions'][vi]+partner)/2
        witness, q, normal, fields = charts[side].nearest(midpoint)
        center = midpoint+normal*max(0.,R['INNER_EASE']+R['WALL']/2-float((midpoint-q)@normal))
        rows.append(dict(witness, kind='literal_paired_cap_rest_sample', garmentTriangle=triangle, vertex=int(vi),
            garmentRestPosition=a['positions'][vi].tolist(), old16Full71Fields=a['namedFields'][vi].tolist(),
            wall=wall, partnerVertices=ids, partnerFraction=t, originalMidpoint=midpoint.tolist(),
            proposedInnerRest=(center-R['WALL']/2*normal).tolist(), proposedOuterRest=(center+R['WALL']/2*normal).tolist(),
            bodyFieldsByName={str(n):float(w) for n,w in zip(a['groupNames'],fields) if w > 0}))
selected = a['faceRoles'][polygon] == 'selected_retained'
garment = A['Surface'](a['positions'], f[selected]); selected_ids = np.flatnonzero(selected)
body_ids = np.flatnonzero(np.all(b['regionIds'][b['triangles']] == 1, axis=1))
body_surface = A['Surface'](b['positions'], b['triangles'][body_ids])
for vi in f[3959]:
    target, hit, inner, outer, wall, shift, origin = R['front_pair'](a['positions'][vi], body_surface, garment, body, A)
    rows.append({'kind':'literal_lower_front_pair', 'vertex':int(vi), 'restPosition':a['positions'][vi].tolist(),
        'bodyTriangle':int(body_ids[hit[2]]), 'bodyBarycentric':hit[3].tolist(),
        'bodyRestPoint':(origin+np.array([0.,-hit[0],0.])).tolist(),
        'innerGarmentTriangle':int(selected_ids[inner[2]]), 'innerBarycentric':inner[3].tolist(),
        'outerGarmentTriangle':int(selected_ids[outer[2]]), 'outerBarycentric':outer[3].tolist(),
        'wall':wall, 'sharedRequiredTranslationM':shift, 'existingWallThicknessM':outer[0]-inner[0]})
result = {'status':'SOURCE_ONLY_READ_ONLY_ACTUAL_REST_WITNESSES', 'acceptedArt':False,
    'recipe':R['pin'](HERE/'refit.py'), 'input':R['pin'](R['checked']('receipt')),
    'bodyGuide':R['pin'](R['checked']('body')), 'full71ColumnNames':a['groupNames'].tolist(), 'witnesses':rows,
    'candidateCreated':False, 'geometryOrFieldsEdited':False, 'nativeOpened':False,
    'limits':'Twelve paired cap REST witnesses and three lower-front paired-ray witnesses only. Full paired-cap evaluation and fixed healthy lower-ring verification remain unrun.'}
print(json.dumps(result,indent=2))
