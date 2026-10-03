from pathlib import Path
import sys,json,numpy as np,hashlib
ROOT=Path(__file__).resolve().parents[3];Q=ROOT/'hoodie-repair02/qa-lane'
src=(ROOT/'runtime/prepare_references.py').read_text();ns={};exec('import struct,json,copy,hashlib\nfrom pathlib import Path\nimport numpy as np\n'+src[src.index('def decode('):src.index("manifest={'tolerance_m'")],ns)
p=Path(sys.argv[1]);label=sys.argv[2];doc,bin,sha=ns['decode'](p);array=ns['array'];source,sbin,ssha=ns['decode'](Q/'C19-source.glb');rows=[];bad=[];pr=[p for m in doc['meshes']for p in m['primitives']];sp=[p for m in source['meshes']for p in m['primitives']]
for i,prim in enumerate(pr):
 for k,ai in [('base',prim['attributes']['POSITION'])]+[(str(j),t['POSITION'])for j,t in enumerate(prim.get('targets',[]))if'POSITION'in t]:
  a=doc['accessors'][ai];v=array(doc,bin,ai);err=float(max(np.max(abs(v.min(0)-a['min'])),np.max(abs(v.max(0)-a['max']))))if'min'in a and'max'in a else None;ok=err is not None and err<1e-6;rows.append({'primitive':i,'target':k,'accessor':ai,'bounds_present':'min'in a and'max'in a,'max_bounds_error':err,'pass':ok});
  if not ok:bad.append(rows[-1])
protected={}
for attr in ['TEXCOORD_0','COLOR_0']:
 protected[attr]=all((attr not in a['attributes']and attr not in b['attributes'])or np.array_equal(array(doc,bin,a['attributes'][attr]),array(source,sbin,b['attributes'][attr]))for a,b in zip(pr,sp))
protected['head_and_glove_POSITION']=all(np.array_equal(array(doc,bin,pr[i]['attributes']['POSITION']),array(source,sbin,sp[i]['attributes']['POSITION']))for i in [1,3,4]);protected['images_and_materials_JSON']=doc.get('images')==source.get('images')and doc.get('materials')==source.get('materials');protected['original_BIN_prefix_exact']=bin[:len(sbin)]==sbin
out={'sha256':sha,'source_sha256':ssha,'position_bounds_checked':len(rows),'bounds_failures':bad,'protected_attributes':protected,'targets_per_primitive':[len(p.get('targets',[]))for p in pr],'normal_targets_per_primitive':[sum('NORMAL'in t for t in p.get('targets',[]))for p in pr],'clips':[c['name']for c in doc.get('animations',[])],'pass':not bad and all(protected.values()),'limits':'Static data/bounds checks plus preserved bytes. Shader normal directions and PBR appearance are not certified by this check.'};(Q/'runtime'/label/'bounds-integrity.json').write_text(json.dumps(out,indent=2));print(json.dumps(out))
