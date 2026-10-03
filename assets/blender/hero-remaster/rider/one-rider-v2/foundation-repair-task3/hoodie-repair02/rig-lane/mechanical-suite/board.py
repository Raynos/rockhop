from motion import *
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
fig,axes=plt.subplots(2,4,figsize=(15,8),gridspec_kw={'height_ratios':[1,1]})
colors={'fixed_ik':'#387ab9','girdle':'#df7c32'}
kinds=['horizontal','overhead','functional_overhead','forward']
for col,kind in enumerate(kinds):
 ax=axes[0,col]
 for variant in colors:
  D,rec=arm_pose(kind,1,variant);q=centres(D)
  for chain in [[2,5,6,7,8],[2,9,10,11,12]]:
   ax.plot(q[chain,2],q[chain,1],'-o',color=colors[variant],markersize=3,lw=1.7,label=variant if chain[1]==5 else None)
 for chain in [[0,1,2,3,4]]:ax.plot(P[chain,2],P[chain,1],'-o',color='.4',markersize=3,lw=1)
 ax.set_title({'horizontal':'T: lateral arms','overhead':'Legacy overhead:174.3°','functional_overhead':'Authored overhead:140°','forward':'Forward reaching:90°'}[kind],fontsize=11)
 ax.set_aspect('equal');ax.set_xlim(-.83,.83);ax.set_ylim(1.03,2.14);ax.set_xlabel('Lateral worldz (m)');ax.set_ylabel('Worldy (m)');ax.grid(alpha=.2)
manifest=json.loads((HERE/'manifest.json').read_text())
for ax,kind in zip(axes[1],['horizontal','overhead','forward','legacy_elbow']):
 for variant in colors:
  rows=sorted([r for r in manifest['rows']if r['variant']==variant and r['kind']==kind],key=lambda r:r['fraction'])
  ax.plot([r['fraction']for r in rows],[r['upperClothMaxEdge2mm']for r in rows],'-o',color=colors[variant],markersize=3,label=variant)
 ax.set_title(kind.replace('_',' ')+' | real garment strain',fontsize=11);ax.set_xlabel('Continuous curve fraction');ax.set_ylabel('Max edge ratio (rest≥2mm)');ax.set_ylim(.8,12.5);ax.grid(alpha=.2)
handles,labels=axes[0,0].get_legend_handles_labels();fig.legend(handles,['Fixed shoulder, matched IK','Existing girdle participation'],loc='lower center',ncol=2,bbox_to_anchor=(.5,.045),fontsize=11)
fig.suptitle('V7 motion-only ablation | Same hand positions/orientations, same mesh and weights',fontsize=16,y=.98)
fig.text(.5,.012,'Skeleton/metric illustration, not a garment render. Small girdle participation preserves lengths but does not fix T/forward/elbow clothing failure.',ha='center',fontsize=11)
fig.tight_layout(rect=[0,.08,1,.95]);fig.savefig(HERE/'mechanical-comparison.png',dpi=160)
print(HERE/'mechanical-comparison.png')
