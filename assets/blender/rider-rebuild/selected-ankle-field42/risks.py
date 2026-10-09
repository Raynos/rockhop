"""Localize frozen field42 edge stretch and support-boundary jumps for film review.

CPU diagnostics only; these witnesses do not establish folds/intersections or art.
"""
import importlib.util
import json
import sys
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('field42',HERE/'derive.py');d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)

def main():
    receipt_path=Path(sys.argv[1]).resolve();out=Path(sys.argv[2]).resolve()
    assert out.is_relative_to(d.ROOT/'docs/evidence/rider-rebuild/selected-ankle-field42')and not out.exists()
    r=json.loads(receipt_path.read_text());sources={k:d.pin(v)for k,v in r['sources'].items()}
    patch=np.load(d.pin(r['patch']));jp,jf,jw,loaded=d.GLB(sources['runtime']).mesh('RiderJeans')
    game=json.loads(sources['gameplayMatrices'].read_text());names=game['boneNames'];jw=jw[:,[loaded.index(n)for n in names]]
    bones={b['name']:b for b in game['nativeRest']['bones']};inverse=np.linalg.inv(np.array([bones[n]['matrix']for n in names]))
    generic=np.load(sources['genericMatrices']);assert generic['boneNames'].tolist()==names
    envelopes=[(a['name'],np.asarray(a['nativeWorldMatrices']))for a in game['actions']]
    envelopes += [(a['name'],generic['pose'+str(i)])for i,a in enumerate(json.loads(sources['genericReceipt'].read_text())['actions'])]
    result={'acceptedArt':False,'status':'FROZEN_FIELD42_MOVING_INSPECTION_WITNESSES','patchReceipt':{'path':str(receipt_path.relative_to(d.ROOT)),'sha256':d.sha(receipt_path)},'recipeSHA256':d.sha(__file__),'sides':{},'limits':['Edge stretch and field-displacement jumps identify film inspection targets; no fold/inversion/crossing/coverage pass.','Boundary means an edge crossing changed/unmodified support; it includes natural zero field arcs, not just upper height.','Upper-boundary witnesses are additionally separated at the frozen 200 mm selection height.']}
    new_names=patch['boneNames'].tolist();assert new_names==names
    for side,sign in [('L',1),('R',-1)]:
        chosen=jp[patch['nativeIds'],0]*sign>0;ids=patch['nativeIds'][chosen];weights=patch['weights'][chosen]
        local=jf[np.any(np.isin(jf,ids),axis=1)];edges=np.unique(np.sort(np.concatenate([local[:,[0,1]],local[:,[1,2]],local[:,[2,0]]]),axis=1),axis=0)
        needed=np.unique(edges);index={int(i):k for k,i in enumerate(needed)};ei=np.array([[index[int(i)]for i in e]for e in edges]);old=jw[needed];new=old.copy()
        for i,row in zip(ids,weights):new[index[int(i)]]=row
        boundary=np.isin(edges,ids).sum(1)==1;upper=boundary&(jp[edges,2].min(1)>=.195)
        rest=np.linalg.norm(jp[edges[:,0]]-jp[edges[:,1]],axis=1);assert np.all(rest>0)
        summaries=[]
        def update(best,label,values,select,frame):
            candidates=np.flatnonzero(select)
            if not len(candidates):return
            k=candidates[np.argmax(values[candidates])];v=float(values[k])
            if label not in best or v>best[label]['value']:
                e=edges[k];best[label]={'value':v,'frame':frame+1,'nativeEdgeIDs':e.tolist(),'restCoordinates':jp[e].tolist(),'restLengthM':float(rest[k]),'beforeFields':[{n:float(v)for n,v in zip(names,old[index[int(i)]])if v>0}for i in e],'afterFields':[{n:float(v)for n,v in zip(names,new[index[int(i)]])if v>0}for i in e]}
        for name,worlds in envelopes:
            best={}
            for frame,world in enumerate(worlds):
                matrices=world@inverse;a=np.zeros((len(needed),3));b=np.zeros_like(a)
                for j in np.flatnonzero(np.any(old+new>0,axis=0)):
                    t=d.transform(jp[needed],matrices[j]);a+=t*old[:,j,None];b+=t*new[:,j,None]
                stretch=np.linalg.norm(b[ei[:,0]]-b[ei[:,1]],axis=1)/rest
                jumps=np.linalg.norm((b-a)[ei[:,0]]-(b-a)[ei[:,1]],axis=1)
                update(best,'maximumNewEdgeStretchRatio',stretch,np.ones(len(edges),bool),frame)
                update(best,'maximumBoundaryDisplacementJumpM',jumps,boundary,frame)
                update(best,'maximumUpperBoundaryDisplacementJumpM',jumps,upper,frame)
            summaries.append({'action':name,'frames':len(worlds),**best})
        result['sides'][side]={'upperBoundaryCrossingEdges':int(upper.sum()),'envelopes':summaries}
    out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'output':str(out),'sides':{s:[{'action':e['action'],**{k:{'value':v['value'],'frame':v['frame'],'nativeEdgeIDs':v['nativeEdgeIDs']}for k,v in e.items()if isinstance(v,dict)}}for e in v['envelopes']]for s,v in result['sides'].items()}},indent=2))
if __name__=='__main__':main()
