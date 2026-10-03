from pathlib import Path
ROOT=Path('/Users/raynos/projects/games/rockhop/assets/blender/hero-remaster/rider/one-rider-v2/foundation-repair-task3')
src=(ROOT/'hoodie-repair03/scripts/render_game304.py').read_text()
src=src.replace("for variant in ['source','v7-plain','v7-cage','volume-slide']:","for variant in ['uv-only','uv-geometric-normal']:")
src=src.replace("source=ROOT/'deliverables/C19.glb'if variant=='source'else ROOT/'hoodie-repair02/deliverables/rider-compression-v7.glb'","source=ROOT/'hoodie-repair03/uv-normal-foundation01/rider-uv-ablation.glb'")
src=src.replace("data=np.load(ROOT/'hoodie-repair03/poses'/f'game304-{variant}.npz');DD=data['matrices'];posed=np.concatenate([data[f'p{i}']for i in range(5)]);CC=", "data=np.load(ROOT/'hoodie-repair03/poses/game304-v7-plain.npz');DD=data['matrices'];uvrows=json.loads((ROOT/'hoodie-repair03/uv-normal-foundation01/uv-ablation-provenance.json').read_text())['rows'];oldtris=np.load(ROOT/'hoodie-repair02/v7-bind.npz')['tr0'];clones=np.concatenate([oldtris[row['face']]for row in uvrows]);points=[data[f'p{i}']for i in range(5)];points[0]=np.concatenate([points[0],points[0][clones]]);posed=np.concatenate(points);CC=")
src=src.replace("skin=skin@CC.T", """skin=skin@CC.T
 if variant=='uv-geometric-normal':
  # Diagnostic physically consistent geometric normals after deformation.
  # Preserve exact source rest aliases; do not weld merely coincident posed sheets.
  _,alias=np.unique(r,axis=0,return_inverse=True);faces=np.concatenate([g.array(prims[i]['indices']).reshape(-1,3)+offset[i]for i in [0,2]]).astype(int);ft=posed[faces];cross=np.cross(ft[:,1]-ft[:,0],ft[:,2]-ft[:,0]);sums=np.zeros((alias.max()+1,3))
  for corner in range(3):np.add.at(sums,alias[faces[:,corner]],cross)
  target=sums[alias];target/=np.maximum(np.linalg.norm(target,axis=1,keepdims=True),1e-15);target=target@CC.T;cloth=np.r_[np.arange(offset[1]),np.arange(offset[2],offset[3])];skin[cloth]=target[cloth]
""")
src=src.replace("['pbr','gray']","['pbr']")
src=src.replace("'normalMode':'standard LBS source normal emulation; cage candidate normals not yet rederived'","'normalMode':'UV-only LBS versus world geometric-normal diagnostic; positions andimagebytes fixed; no geometric acceptance'")
exec(compile(src,str(ROOT/'hoodie-repair03/scripts/render_game304.py'),'exec'))
