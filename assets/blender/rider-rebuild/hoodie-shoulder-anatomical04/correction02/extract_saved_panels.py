"""One readonly actual saved-panel topology/UV dump; never saves or edits native."""
import hashlib,json,sys
from pathlib import Path
import bpy,numpy as np
ROOT=Path(__file__).resolve().parents[5]
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb')as f:
  while b:=f.read(1024*1024):h.update(b)
 return h.hexdigest()
def main():
 args=sys.argv[sys.argv.index('--')+1:];assert len(args)==1
 out=Path(args[0]).resolve();assert not out.exists()and out.is_relative_to(ROOT/'harness/out/rider-rebuild/hoodie-shoulder-anatomical04')
 native=ROOT/'harness/out/rider-rebuild/hoodie-shoulder-anatomical04/authored01/selected-panel-outfit.blend'
 expected='1ad5c5aa21553bbb3eb84898572200b2d4418e81e1e1995d774a763707f0124f';assert sha(native)==expected
 bpy.ops.wm.open_mainfile(filepath=str(native));o=bpy.data.objects['Hoodie__RiderHoodie'];m=o.data
 data={'vertices':np.asarray([v.co[:]for v in m.vertices]),'polygonStarts':np.asarray([p.loop_start for p in m.polygons]),'polygonCounts':np.asarray([p.loop_total for p in m.polygons]),'cornerVertexIds':np.asarray([l.vertex_index for l in m.loops]),'UV':np.asarray([v.uv[:]for v in m.uv_layers.active.data]),'polygonNormals':np.asarray([p.normal[:]for p in m.polygons])};attrs=[]
 for a in m.attributes:
  if a.name.startswith('_panel04_')or a.name=='actual_donor_display_xyz':
   field='vector'if a.data_type=='FLOAT_VECTOR'else'value'
   data[a.name]=np.asarray([getattr(v,field)[:]if field=='vector'else getattr(v,field)for v in a.data]);attrs.append({'name':a.name,'domain':a.domain,'type':a.data_type})
 body_arrays=ROOT/'docs/evidence/rider-rebuild/native-hand-repair01/native02/native-body.npz'
 assert sha(body_arrays)=='e62e9969503b7761e99463eccc3ca7be39e0c230a2948f2f87a224db52d0f9a2'
 canonical=np.load(body_arrays)
 data['canonicalBodyVertices']=canonical['vertices'];data['canonicalBodyFaces']=canonical['faces']
 out.mkdir(parents=True);np.savez_compressed(out/'saved-panels.npz',**data)
 assert sha(native)==expected
 (out/'intake.json').write_text(json.dumps({'accepted':False,'nativeSHA256':expected,'extractorSHA256':sha(__file__),'npzSHA256':sha(out/'saved-panels.npz'),'vertices':len(m.vertices),'polygons':len(m.polygons),'attributes':attrs,'canonicalBodyArraysSHA256':sha(body_arrays),'nativeUnchanged':True,'noGeometryEditOrSave':True},indent=2)+'\n')
 print('ACTUAL_SAVED_PANEL_TOPOLOGY_UV_READONLY',flush=True)
if __name__=='__main__':main()
