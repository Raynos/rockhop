"""Original-source nested section and UV/PBR correspondence tables, CPU only."""
import argparse,json
from pathlib import Path
import numpy as np
from audit_hunyuan_air import load_glb,save,digest,point_inside


def cross2(a,b):return a[...,0]*b[...,1]-a[...,1]*b[...,0]


def crossing_counts(a,b,self_pair=False):
    aa=a[:,None,:];ab=np.roll(a,-1,axis=0)[:,None,:]
    ba=b[None,:,:];bb=np.roll(b,-1,axis=0)[None,:,:]
    o1=cross2(ab-aa,ba-aa);o2=cross2(ab-aa,bb-aa)
    o3=cross2(bb-ba,aa-ba);o4=cross2(bb-ba,ab-ba)
    eps=1e-14
    overlap=(np.maximum(np.minimum(aa,ab),np.minimum(ba,bb))<=np.minimum(np.maximum(aa,ab),np.maximum(ba,bb))+eps).all(axis=2)
    strict=overlap&(((o1>eps)&(o2<-eps))|((o1<-eps)&(o2>eps)))&(((o3>eps)&(o4<-eps))|((o3<-eps)&(o4>eps)))
    possible=overlap&~strict&((np.abs(o1)<=eps)|(np.abs(o2)<=eps)|(np.abs(o3)<=eps)|(np.abs(o4)<=eps))
    if self_pair:
        n=len(a);i=np.arange(n)[:,None];k=np.arange(n)[None,:];allowed=(k>i)&((k-i)>1)&~((i==0)&(k==n-1))
        strict&=allowed;possible&=allowed
    return {'strictTransverseCrossings':int(strict.sum()),'possibleNonAdjacentTangencies':int(possible.sum()),'crossProductTolerance':eps}


def planar_gap(a,b):
    def distances(points,p,q):
        edge=q-p;ee=(edge*edge).sum(axis=1);d=points[:,None,:]-p[None,:,:]
        t=np.clip((d*edge).sum(axis=2)/np.where(ee>0,ee,1)[None,:],0,1)
        return float(np.sqrt(((d-t[:,:,None]*edge)**2).sum(axis=2).min()))
    return min(distances(a,b,np.roll(b,-1,axis=0)),distances(b,a,np.roll(a,-1,axis=0)))


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--source',required=True);parser.add_argument('--sections',required=True);parser.add_argument('--out',required=True);args=parser.parse_args();out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
    assert not (out/'nested.json').exists()
    v,f,uv,images,meta=load_glb(args.source);sections=json.loads(Path(args.sections).read_text());nested=[];tables=[]
    for sid,s in enumerate(sections):
        axis=s['axis'];axes=[k for k in range(3) if k!=axis];valid=[(i,l) for i,l in enumerate(s['loops']) if l['closed'] and l.get('area',0)>1e-10]
        entry={'section':s['name'],'axis':axis,'value':s['value'],'quantization':s['quantizationNativeUnits'],'nonDegreeTwoComponents':sum(not l['closed'] for l in s['loops']),'loops':[],'relationships':[]}
        for lid,l in valid:
            points=np.asarray(l['points']);points2=points[:,axes];self_check=crossing_counts(points2,points2,True)
            entry['loops'].append({'id':lid,'area':l['area'],'bounds':l['bounds'],'segments':l['segments'],**self_check})
            # Loop edge i links original row i. Midpoints remain exact correspondence within reported residual.
            midpoint=(points+np.roll(points,-1,axis=0))/2;rows=np.asarray(l['triangleRows']);tri=v[f[rows]]
            e1=tri[:,1]-tri[:,0];e2=tri[:,2]-tri[:,0];normal=np.cross(e1,e2);nn=(normal*normal).sum(axis=1)
            assert (nn>0).all();delta=midpoint-tri[:,0]
            b=(np.cross(delta,e2)*normal).sum(axis=1)/nn;c=(np.cross(e1,delta)*normal).sum(axis=1)/nn
            bary=np.column_stack((1-b-c,b,c));reconstructed=np.einsum('ij,ijk->ik',bary,tri);residual=np.linalg.norm(reconstructed-midpoint,axis=1)
            assert residual.max()<1e-7 and bary.min()>-1e-5 and bary.max()<1+1e-5,(s['name'],residual.max(),bary.min(),bary.max())
            texcoord=np.einsum('ij,ijk->ik',bary,uv[f[rows]]);samples=[]
            for name in ('baseColorTexture','metallicRoughnessTexture'):
                im=images[name];h,w=im.shape[:2];pixels=np.floor((texcoord%1)*[w,h]).astype(int);samples.append(im[pixels[:,1],pixels[:,0]])
            tables.append({'section':np.full(len(rows),sid),'loop':np.full(len(rows),lid),'originalTriangleRow':rows,'positionNative':midpoint,'barycentric':bary,'uv':texcoord,'positionResidual':residual,'baseColorRGB8':samples[0],'metallicRoughnessRGB8':samples[1]})
        for ai,(aid,a) in enumerate(valid):
            for bid,b in valid[ai+1:]:
                aa=np.asarray(a['points'])[:,axes];bb=np.asarray(b['points'])[:,axes];crossings=crossing_counts(aa,bb)
                ainb=sum(point_inside(p,b,axis) for p in a['points']);bina=sum(point_inside(p,a,axis) for p in b['points'])
                gap=planar_gap(aa,bb);entry['relationships'].append({'a':aid,'b':bid,'aVerticesInsideB':ainb,'aVertices':len(aa),'bVerticesInsideA':bina,'bVertices':len(bb),'planarMinimumSeparation':gap,**crossings,
                    'strictlyNested':not crossings['strictTransverseCrossings'] and not crossings['possibleNonAdjacentTangencies'] and gap>1e-9 and (ainb==len(aa) or bina==len(bb))})
        nested.append(entry)
    combined={k:np.concatenate([t[k] for t in tables]) for k in tables[0]};np.savez_compressed(out/'source-region-correspondence.npz',**combined)
    save(out/'nested.json',nested);save(out/'correspondence.json',{**meta,'sectionsSHA256':digest(Path(args.sections).read_bytes()),'recipeSHA256':digest(Path(__file__).read_bytes()),'table':str(out/'source-region-correspondence.npz'),'tableSHA256':digest((out/'source-region-correspondence.npz').read_bytes()),'rows':len(combined['originalTriangleRow']),'columns':{k:list(x.shape) for k,x in combined.items()},'maximumPositionResidual':float(combined['positionResidual'].max()),'maximumBarycentricViolation':float(max(0,-combined['barycentric'].min(),combined['barycentric'].max()-1)),'sectionIDs':{i:s['name'] for i,s in enumerate(sections)},'textureConvention':{'origin':'top-left, repeat wrapping; nearest RGB8 diagnostics','roughness':'green /255, factor1','metallic':'blue /255, factor1','baseColor':'sRGB-encoded RGB8, not shaded color','officialSource':'https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html#materials'},'accepted':False,'limits':['Closed loops with strict nesting and separation are geometric evidence, not a universal solid/material occupancy rule.','Native model units are uncalibrated despite glTF metric convention; no fit/body transform.','No source mesh/UV/material mutation; table is original-row evidence only, not reconstructed/fitted geometry.','Tangency check is conservative float64 with explicit tolerance; no global 3D self-intersection proof.']})
    print(json.dumps({'rows':len(combined['originalTriangleRow']),'out':str(out),'accepted':False}))


if __name__=='__main__':main()
