from pathlib import Path
import sys,json,hashlib,ast,numpy as np
from scipy.spatial import cKDTree
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE));from boundary_weights import world_skin
sys.path.insert(0,str(HERE.parent/'mechanical-suite'));from motion import legacy,neutral_elbow
INPUT=HERE.parents[1]/'shape-lane/volume-lane/armhole-construction/armhole-chart-outward.npz';f=np.load(INPUT);assert hashlib.sha256(INPUT.read_bytes()).hexdigest()=='10a1c2094726e7ab929b453e07e5f9c072dd06b0673a8557f4f41c6c5e33c2d7'
pp=[f[f'p{i}']for i in range(5)];base=np.concatenate([pp[0],pp[2]]);tri=np.concatenate([f['tr0'],f['tr2']+len(pp[0])]);weld=np.r_[f['physicalWeld0'],f['physicalWeld2']]
mask=((base[tri][:,:,1]>.99)&(base[tri][:,:,1]<1.62)).all(1);ids=np.flatnonzero(mask);tr=tri[mask];ta=weld[tr];ed=np.unique(np.sort(np.concatenate([tr[:,[0,1]],tr[:,[1,2]],tr[:,[0,2]]]),axis=1),axis=0);l0=np.linalg.norm(base[ed[:,0]]-base[ed[:,1]],axis=1);a0=np.linalg.norm(np.cross(base[tr[:,1]]-base[tr[:,0]],base[tr[:,2]]-base[tr[:,0]]),axis=1);large=l0>=.002
newmask=ids>=len(f['tr0']) # primitive2 separately excluded below
newmask=(ids>=33968)&(ids<len(f['tr0']))
code=(HERE.parents[2]/'audit/self_intersections.py').read_text();tree=ast.parse(code);node=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='crossing');exec(compile(ast.Module(body=[node],type_ignores=[]),'<strict six-edge triangle predicate>','exec'));EPS=1e-9
fullweld=np.concatenate([f[f'physicalWeld{i}']for i in range(5)]);fullOff=np.r_[0,np.cumsum([len(x)for x in pp])];active=np.concatenate([np.unique(f[f'tr{i}'])+fullOff[i]for i in range(5)]);counts=np.bincount(fullweld[active],minlength=int(fullweld.max())+1)
def gate(pts):
 q=np.concatenate([pts[0],pts[2]]);T=q[tr];ratio=np.linalg.norm(q[ed[:,0]]-q[ed[:,1]],axis=1)/np.maximum(l0,1e-15);area=np.linalg.norm(np.cross(T[:,1]-T[:,0],T[:,2]-T[:,0]),axis=1)/np.maximum(a0,1e-15)
 joined=np.concatenate(pts);avg=np.zeros((len(counts),3));np.add.at(avg,fullweld[active],joined[active]);avg/=np.maximum(counts[:,None],1);gap=np.linalg.norm(joined[active]-avg[fullweld[active]],axis=1)
 out={'maxEdgeMinRest2mm':float(ratio[large].max()),'p99EdgeMinRest2mm':float(np.quantile(ratio[large],.99)),'collapsedFaces25Pct':int((area<.25).sum()),'collapsedNewFabricFaces25Pct':int((area[newmask]<.25).sum()),'minAreaRatio':float(area.min()),'physicalSeamAliasMaxGapM':float(gap.max())}
 centre=T.mean(1);radius=np.linalg.norm(T-centre[:,None],axis=2).max(1);pairs=np.array([(a,b)for a,near in enumerate(cKDTree(centre).query_ball_point(centre,radius+radius.max()))for b in near if a<b],int).reshape(-1,2);lo=T.min(1);hi=T.max(1);pairs=pairs[((lo[pairs[:,0]]<=hi[pairs[:,1]])&(lo[pairs[:,1]]<=hi[pairs[:,0]])).all(1)];shared=(ta[pairs[:,0],:,None]==ta[pairs[:,1],None,:]).any(2).sum(1);keep=shared<2;pairs=pairs[keep];shared=shared[keep];hit=crossing(T[pairs[:,0]],T[pairs[:,1]]);out.update(strictNonadjacentCrossings=int((hit&(shared==0)).sum()),strictOneCornerCrossings=int((hit&(shared==1)).sum()),witnessCombinedFacePairs=ids[pairs[hit]].tolist()[:30]);return out
actual=np.load(HERE.parent/'chart-weights/source34-480-matrices.npz')['D'];poses=[('neutral',0,np.tile(np.eye(4),(19,1,1)),False)]
for t in [.375,.625,1]:poses.append(('forward',t,legacy('forward',t),t!=1))
for a in [45,75,90,105,120]:poses.append(('neutral_elbow',a,neutral_elbow(a),a in [45,75,105]))
for s in [304,250,350]:poses.append(('actual_source34',s,actual[s],s!=304))
variants={'shape_control':[f[f'W{i}']for i in range(5)]}
for name in ['fabric-ownership','fabric-anatomical']:
 w=np.load(HERE/(name+'.npz'));variants[name]=[w[f'W{i}']for i in range(5)]
rows=[];(HERE/'poses').mkdir(exist_ok=True)
for kind,value,D,held in poses:
 for name,w in variants.items():
  pts=[world_skin(p,x,D)for p,x in zip(pp,w)];label=f'{name}-{kind}-{value:g}';path=HERE/'poses'/(label+'.npz');np.savez_compressed(path,matrices=D,**{f'p{i}':q for i,q in enumerate(pts)});row={'variant':name,'probe':kind,'fraction':value,'holdout':held,'path':str(path),'worldMatricesSHA256':hashlib.sha256(D.tobytes()).hexdigest()};row.update(gate(pts));rows.append(row);print(json.dumps({k:v for k,v in row.items()if k not in ['path','witnessCombinedFacePairs']}),flush=True)
  (HERE/'finite-gates.json').write_text(json.dumps({'status':'UNACCEPTED_FINITE_TRIANGLE_GATES','geometrySHA256':hashlib.sha256(INPUT.read_bytes()).hexdigest(),'geometryPath':str(INPUT),'method':'Same reconstructed rest, same worldD pervariant, morph0; upper cloth0+2 triangle ROI all corners .99<y<1.62. Author physicalWeld sewn edges excluded; one-corner crossings explicit. Sphere/AABB broadphase plus strict transverse six-edge predicate. Seam gap includes only actually referenced vertices; unused removed-seam rows excluded.','limits':['Finite12poses, not continuous collision detection or visual/contact acceptance','Wider ROI includes inherited source C19 crossings outside shape rest-clear crop','Coplanar and tangent contacts not classified','No source weights or source geometry changes between these comparisons'],'rows':rows},indent=2)+'\n')
