"""CPU construction inspection against all482 existing actual bike matrices.

These geometry diagrams are not actual PBR game footage and award no art pass.
"""
import json
from pathlib import Path
import runpy
import sys

import numpy as np

HERE=Path(__file__).resolve().parent
A=runpy.run_path(str(HERE/'author.py'))
ROOT=A['ROOT'];checked=A['checked'];pin=A['pin']
GAME={'path':'harness/out/rider-rebuild/selected-authoring-motion11/gameplay-converted02/measured-gameplay-native-world.json',
      'sha256':'f3e0444768655bf72500a9245745a559586a7717b3f6cb6b600b6e9d1d05c153'}


def diagram(path,positions,faces,roles,label,selection=None):
    from PIL import Image,ImageDraw
    image=Image.new('RGB',(1500,850),'#10151c');draw=ImageDraw.Draw(image)
    for col,eye in enumerate(([0.,-1.,.05],[1.,-.4,.1],[-1.,-.65,.08])):
        view=A['unit'](np.asarray(eye));right=A['unit'](np.cross(view,[0,0,1]));up=np.cross(right,view)
        projected=np.stack([positions@right,positions@up,positions@view],axis=1)
        selected=np.ones(len(faces),bool)if selection is None else selection
        ids=np.unique(np.concatenate([faces[i]for i in np.flatnonzero(selected)]))
        bounds=projected[ids,:2];low,high=bounds.min(0),bounds.max(0);center=(low+high)/2
        scale=min(450/(high[0]-low[0]),740/(high[1]-low[1]))
        screen=(projected[:,:2]-center)*[scale,-scale]+[col*500+250,430]
        order=sorted(np.flatnonzero(selected),key=lambda i:float(projected[faces[i],2].mean()))
        for i in order:
            face=faces[i];p=positions[face];normal=np.cross(p[1]-p[0],p[2]-p[0]);length=np.linalg.norm(normal)
            if length==0:continue
            normal/=length
            if normal@view<0:continue
            light=.35+.65*max(0.,normal@A['unit'](view+np.array([-.4,0,.8])))
            base=np.array([188,142,56])if roles[i]!='selected_retained'else np.array([98,112,117])
            color=tuple(np.clip(base*light,0,255).astype(int));xy=[tuple(v)for v in screen[face]]
            draw.polygon(xy,fill=color);draw.line(xy+[xy[0]],fill=tuple(np.clip(base*.55,0,255).astype(int)),width=1)
        draw.text((col*500+12,20),label+' | construction geometry',fill='white')
    image.save(path)


def main(receipt_path,out):
    receipt_path=Path(receipt_path).resolve();out=Path(out).resolve()
    assert out.is_relative_to(ROOT/'harness/out/rider-rebuild/selected-hoodie-joints77')and not out.exists()
    receipt=json.loads(receipt_path.read_text());a=np.load(checked(receipt['receiver']))
    faces=[a['cornerVertexIds'][s:s+n]for s,n in zip(a['polygonStarts'],a['polygonCounts'])]
    roles=a['faceRoles'];p=a['positions'];game=json.loads(checked(GAME).read_text())
    bones={b['name']:b for b in game['nativeRest']['bones']};names=game['boneNames']
    inv=np.linalg.inv(np.asarray([bones[n]['matrix']for n in names]))
    weights=np.zeros((len(p),len(names)))
    for gi,name in enumerate(a['groupNames']):weights[:,names.index(str(name))]=a['namedFields'][:,gi]
    active=np.flatnonzero(weights.max(0)>0)
    edges=np.unique(np.sort(np.asarray([[int(x),int(y)]for face,role in zip(faces,roles)if role!='selected_retained'
                               for x,y in zip(face,np.roll(face,-1))]),axis=1),axis=0)
    restlength=np.linalg.norm(p[edges[:,1]]-p[edges[:,0]],axis=1);assert restlength.min()>0
    rest=np.asarray(p);results=[];out.mkdir(parents=True)
    cap=np.asarray([role.startswith('authored_armhole')or(any(a['vertexRoles'][f]=='shoulder_cap_L')or any(a['vertexRoles'][f]=='axilla_L'))
                    for f,role in zip(faces,roles)])
    diagram(out/'isolated-cap-axilla.png',p,faces,roles,'Rest cap and axilla',cap)
    diagram(out/'rest-whole.png',p,faces,roles,'Rest whole receiver')
    for action in game['actions']:
        rows=[]
        for fi,world in enumerate(np.asarray(action['nativeWorldMatrices'])):
            matrices=world@inv;posed=np.zeros_like(p)
            for j in active:
                posed+=(p@matrices[j,:3,:3].T+matrices[j,:3,3])*weights[:,j,None]
            ratio=np.linalg.norm(posed[edges[:,1]]-posed[edges[:,0]],axis=1)/restlength
            maxid=int(np.argmax(ratio));minid=int(np.argmin(ratio))
            rows.append({'frame':fi+1,'maximumAuthoredEdgeStretch':float(ratio[maxid]),'maximumEdge':edges[maxid].tolist(),
                         'minimumAuthoredEdgeRatio':float(ratio[minid]),'minimumEdge':edges[minid].tolist()})
            if fi+1 in action['surfaceWitnessFrames']:
                diagram(out/(action['bike']+'-'+str(fi+1).zfill(3)+'.png'),posed,faces,roles,action['bike']+' actual key '+str(fi+1))
        results.append({'action':action['name'],'keys':len(rows),'maximum':max(rows,key=lambda r:r['maximumAuthoredEdgeStretch']),
                        'minimum':min(rows,key=lambda r:r['minimumAuthoredEdgeRatio']),'frames':rows})
    report={'status':'AUTHORED77_ACTUAL482_CPU_GEOMETRY_INSPECTION_UNACCEPTED','acceptedArt':False,
            'recipe':pin(__file__),'receiverReceipt':pin(receipt_path),'gameplayMatrices':GAME,
            'keys':sum(r['keys']for r in results),'actions':results,
            'limits':'Actual recorded bone matrices and full named fields, CPU linear blend geometry only. No native dual-quaternion, GPU, PBR, finite contact, self-intersection or played art acceptance.'}
    (out/'inspection.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k]for k in ('status','keys')}),flush=True)


if __name__=='__main__':main(*sys.argv[1:])
