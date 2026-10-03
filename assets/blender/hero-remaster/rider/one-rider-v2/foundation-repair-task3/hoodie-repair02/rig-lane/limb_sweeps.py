from weights import *
def around(D,joints,pivot,rotation):
 for j in joints:
  D[j,:3,:3]=rotation@D[j,:3,:3]
  D[j,:3,3]=rotation@(D[j,:3,3]-pivot)+pivot
 return D
def limb_pose(kind,fraction,side='both'):
 D=np.repeat(np.eye(4)[None],N,axis=0)
 if kind=='raise':return raise_pose(fraction)
 for ss,sg in [('L',1),('R',-1)]:
  if side!='both'and ss!=side:continue
  a,b,c=[IND[s+'.'+ss]for s in ['upperArm','forearm','hand']]
  if kind=='elbow':rotation=R.from_rotvec(np.array([0,0,sg])*np.deg2rad(120)*fraction).as_matrix();around(D,[b,c],P[b],rotation)
  elif kind=='twist':axis=P[c]-P[b];axis/=np.linalg.norm(axis);rotation=R.from_rotvec(axis*np.deg2rad(90)*fraction).as_matrix();around(D,[b,c],P[b],rotation)
  elif kind=='wrist':rotation=R.from_rotvec(np.array([0,0,sg])*np.deg2rad(65)*fraction).as_matrix();around(D,[c],P[c],rotation)
 return D
if __name__=='__main__':
 rows=[];folder=HERE/'limb-poses';folder.mkdir(exist_ok=True)
 ct=np.concatenate([TRI[0],TRI[1]+len(POS[0])]);rest=np.concatenate([POS[0],POS[1]])
 mask=((rest[ct][:,:,1]>.85)&(rest[ct][:,:,1]<1.01)).all(1);roi=ct[mask]
 ed=np.unique(np.sort(np.concatenate([roi[:,[0,1]],roi[:,[1,2]],roi[:,[0,2]]]),axis=1),axis=0)
 l0=np.linalg.norm(rest[ed[:,0]]-rest[ed[:,1]],axis=1);a0=np.linalg.norm(np.cross(rest[roi[:,1]]-rest[roi[:,0]],rest[roi[:,2]]-rest[roi[:,0]]),axis=1)
 for name,ws in [('source',W),('anatomical',out)]:
  for kind in ['elbow','twist','wrist']:
   for f in [-1,-.5,0,.5,1]:
    D=limb_pose(kind,f);pts=deform(POS,ws,D,False);q=np.concatenate([pts[0],pts[1]])
    ratio=np.linalg.norm(q[ed[:,0]]-q[ed[:,1]],axis=1)/l0;area=np.linalg.norm(np.cross(q[roi[:,1]]-q[roi[:,0]],q[roi[:,2]]-q[roi[:,0]]),axis=1)/a0
    uq=np.zeros_like(U);np.add.at(uq,INV,np.concatenate(pts));uq/=cnt[:,None]
    gaps=np.linalg.norm(np.concatenate(pts)-uq[INV],axis=1)
    r={'model':name,'kind':kind,'fraction':f,'cuffP99EdgeRatio':float(np.quantile(ratio,.99)),'cuffMaxEdgeRatio':float(ratio.max()),'cuffCollapsedBelowQuarter':int((area<.25).sum()),'allAliasGapM':float(gaps.max())};rows.append(r)
    np.savez(folder/f'{name}-{kind}-{f}.npz',**{f'p{i}':p for i,p in enumerate(pts)},matrices=D)
 (HERE/'limb-gates.json').write_text(json.dumps({'rows':rows,'ROI':'Actual sourcebody+glove faces withall corners .85<y<1.01m. Exactsharedcuff surfaces included. No continuouscollisioncertificate.','gloveGeometryUnchanged':True,'sourceClipGripClosureRetained':True,'angles':'elbow +120deg/-120diagnostic; twist+/-90deg aboutrestforearm; wrist+/-65deg.'},indent=2));print(json.dumps(rows))
