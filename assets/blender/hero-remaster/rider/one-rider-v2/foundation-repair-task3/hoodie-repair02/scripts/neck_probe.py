from base import *
b=np.load(OUT/'v4-bind.npz');pos=[b[f'p{i}']for i in range(5)];ww=[b[f'W{i}']for i in range(5)];rows=[]
for nf,hf in [(0,0),(.10,.10),(.2,.2),(.3,.3),(.5,.5),(.7,.7),(.3,0),(.1,0),(.2,.05)]:
 for kind,t,off in [('start',0,0),('sit',1,0),('lean',1,.25)]:
  D=sit_pose(t,True,off,neckfraction=nf,headfraction=hf);pp=deform(pos,ww,D,True);file=OUT/'poses'/f'neck-{nf}-{hf}-{kind}.npz';np.savez(file,**{f'p{i}':q for i,q in enumerate(pp)},matrices=D);rows.append({'variant':'v4','probe':f'neck-{nf}-{hf}-{kind}','fraction':t,'path':str(file)})
(OUT/'neck-probe-manifest.json').write_text(json.dumps({'rows':rows,'topology_path':str(OUT/'v4-bind.npz')},indent=2))
