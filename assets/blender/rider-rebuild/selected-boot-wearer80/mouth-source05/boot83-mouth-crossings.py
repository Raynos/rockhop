exec(open('/tmp/boot83-mouth-fit.py').read().split('for side in')[0])
def edge_hit(a,b,tri):
 e1,e2=tri[1]-tri[0],tri[2]-tri[0];d=b-a;h=np.cross(d,e2);det=e1@h
 if abs(det)<1e-20:return None
 q=a-tri[0];u=q@h/det;r=np.cross(q,e1);v=d@r/det;t=e2@r/det
 if 0<=u<=1 and 0<=v and u+v<=1 and 0<=t<=1:return (a+t*d).tolist()
 return None
for side in 'LR':
 def arr(k):
  d=s['arrays']['layout'][side+k];return np.frombuffer(raw,dtype=d['dtype'],offset=d['byteOffset'],count=np.prod(d['shape'])).reshape(d['shape'])
 orig=arr('Positions').astype(float);f=arr('Triangles');recipe=np.load('/tmp/boot83-mouth-'+side+'.npz');loop=recipe['loopOriginalVertexIds'];retired=recipe['retiredOriginalFaceIds'];mask=np.ones(len(f),bool);mask[retired]=False;band=np.zeros(len(f),bool);verts=loop
 for i in range(3):band |= mask & np.any(np.isin(f,verts),axis=1);verts=np.unique(f[band])
 ids=np.flatnonzero(band);bt=body['vertices'][body['faces']].astype(float);valid=(bt[:,:,0].min(1)>0 if side=='L' else bt[:,:,0].max(1)<0)&(bt[:,:,2].max(1)>.09)&(bt[:,:,2].min(1)<.14);bids=np.flatnonzero(valid);bt=bt[bids];lo=bt.min(1);hi=bt.max(1);rows=[]
 for fid in ids:
  tri=orig[f[fid]];which=np.flatnonzero(np.all((lo<=tri.max(0))&(hi>=tri.min(0)),axis=1))
  for j in which:
   hits=[]
   for k in range(3):
    q=edge_hit(tri[k],tri[(k+1)%3],bt[j]);r=edge_hit(bt[j,k],bt[j,(k+1)%3],tri)
    if q is not None:hits.append(q)
    if r is not None:hits.append(r)
   if hits:rows.append({'bootSourceTriangle':int(fid),'bodySourceTriangle':int(bids[j]),'intersectionWorldM':hits})
 result={'sourceReturnBandTriangles':len(ids),'bodyTrianglesTested':len(bids),'intersectingTrianglePairs':len(rows),'bootTriangleCount':len(set(r['bootSourceTriangle'] for r in rows)),'rows':rows};Path('/tmp/boot83-mouth-crossings-'+side+'.json').write_text(json.dumps(result,indent=2));print(side,{k:v for k,v in result.items() if k!='rows'},'examples',rows[:2],flush=True)
