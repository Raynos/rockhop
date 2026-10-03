from material_paths import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
report=json.loads((OUT3/'evidence/material-path-lower-bounds.json').read_text());fig,ax=plt.subplots(1,4,figsize=(14,5),sharey=True);keep=cloth&(U[:,1]>.85)&(U[:,1]<1.60);ids=np.flatnonzero(keep)[::3]
for aa,kind in zip(ax,['horizontal','overhead','forward','elbow']):
 r=next(r for r in report['rows']if r['side']=='L'and r['pose']==kind);route=np.array(r['path_unique_vertex_ids']);d=np.load(OUT/'qa-lane/poses'/f'v5-{kind}-1.npz');D=d['matrices'];posed=deform([b[f'p{i}']for i in range(5)],[b[f'W{i}']for i in range(5)],D);world=np.zeros_like(U);np.add.at(world,INV,np.concatenate(posed));world/=np.bincount(INV)[:,None]
 aa.scatter(rest[ids,2],rest[ids,1],s=.4,c='#c6cbd2',alpha=.35,rasterized=True);aa.scatter(world[ids,2],world[ids,1],s=.4,c='#8ea8af',alpha=.25,rasterized=True);aa.plot(rest[route,2],rest[route,1],c='#777777',lw=2,label='Rest material route');ends=r['rest_unique_vertex_anchors'];aa.plot(world[ends,2],world[ends,1],c='#bd4928',lw=2,label='Required endpoint span');aa.scatter(world[ends,2],world[ends,1],s=25,c=['#bd4928','#26749b'],zorder=5)
 aa.set_title(kind.upper()+f"\n≥{r['required_path_average_stretch_lower_bound']:.2f}× required stretch",fontsize=11);aa.set_aspect('equal');aa.set_xlim(-.35,.9);aa.set_ylim(.85,2.1);aa.set_xlabel('Lateral z (m)');aa.grid(alpha=.15)
ax[0].set_ylabel('Up y (m)');ax[0].legend(fontsize=8,loc='upper left');fig.suptitle('Source garment material constraint under held torso + actual sewn cuff points',fontsize=14);fig.text(.04,.045,'Measured in 3D: endpoint distance / shortest rest edge path. Front projection shown.\nConditional lower bound; permitting torso-cloth motion changes it. Does not prove a collision-free deformation.',fontsize=10);fig.tight_layout(rect=[0,.12,1,.92]);fig.savefig(OUT3/'deliverables/material-path-constraint.png',dpi=160);plt.close(fig)
