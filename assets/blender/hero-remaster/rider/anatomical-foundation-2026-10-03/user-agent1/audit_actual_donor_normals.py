"""Separate stored shading normals/flags from actual polygon geometry."""
import argparse, collections, hashlib, json, struct, sys
from pathlib import Path
import bpy, numpy as np
ap=argparse.ArgumentParser(description=__doc__)
for k in ['source','field','donor-glb','out']:ap.add_argument('--'+k,required=True)
a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);source,field,glb,out=[Path(getattr(a,k.replace('-','_'))).resolve() for k in ['source','field','donor-glb','out']];sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();pins={str(p):sha(p) for p in [source,field,glb]};assert pins[str(source)]=='86b85d476b13f709ba832e11dfcd14a17f071f5af69f3ebbbaf7dd1dbe6f58f9';f=np.load(field);bpy.ops.wm.open_mainfile(filepath=str(source))
def buffer(items,name,width,dtype):
    q=np.empty(len(items)*width,dtype=dtype);items.foreach_get(name,q);return q.reshape(-1,width) if width>1 else q
def percent(q):return np.percentile(q,[0,50,95,100]).tolist() if len(q) else []
def measure(obj,detail=False):
    m=obj.data;p=buffer(m.vertices,'co',3,np.float32);fn=buffer(m.polygons,'normal',3,np.float32);smooth=buffer(m.polygons,'use_smooth',1,np.bool_);cn=buffer(m.corner_normals,'vector',3,np.float32);starts=buffer(m.polygons,'loop_start',1,np.int32);total=buffer(m.polygons,'loop_total',1,np.int32);li=buffer(m.loops,'vertex_index',1,np.int32);pi=np.repeat(np.arange(len(m.polygons)),total);valid=np.linalg.norm(fn[pi],axis=1)>.5;cos=np.einsum('ij,ij->i',cn[valid],fn[pi[valid]]);angles=np.degrees(np.arccos(np.clip(cos,-1,1)))
    result={'vertices':len(p),'polygons':len(fn),'loops':len(li),'smoothPolygons':int(smooth.sum()),'flatPolygons':int((~smooth).sum()),'hasCustomNormals':m.has_custom_normals,'cornerVsPolygonNormalAngleDegrees':percent(angles),'cornersWithin0p1DegreeOfFace':int((angles<.1).sum()),'cornerNormalBufferSHA256':hashlib.sha256(cn.tobytes()).hexdigest(),'normalAttributeNames':[x.name for x in m.attributes if 'normal' in x.name or 'sharp' in x.name],'sharpEdges':sum(e.use_edge_sharp for e in m.edges)}
    if detail:
        edges=collections.defaultdict(list)
        for poly in m.polygons:
            ids=list(poly.vertices)
            for i in range(len(ids)):edges[tuple(sorted((ids[i],ids[(i+1)%len(ids)])))].append(poly.index)
        adjacent=[(i,j) for faces in edges.values() if len(faces)==2 for i,j in [faces]];pairs=np.array(adjacent);crease=np.degrees(np.arccos(np.clip(np.einsum('ij,ij->i',fn[pairs[:,0]],fn[pairs[:,1]]),-1,1)));result['adjacentPolygonNormalAngleDegrees']=percent(crease);result['adjacentEdgesAbove30Degrees']=int((crease>30).sum());display=buffer(m.attributes['actual_donor_display_xyz'].data,'vector',3,np.float32);regions=collections.defaultdict(list)
        for poly in m.polygons:
            q=display[list(poly.vertices)].mean(0);region='hood' if q[2]>.62 else 'sleeve.R' if q[0]>.43 else 'sleeve.L' if q[0]<-.43 else 'shoulder.R' if q[0]>.35 else 'shoulder.L' if q[0]<-.35 else 'torso';regions[region].append(poly.index)
        result['regions']={}
        for name,ids in regions.items():
            mask=np.isin(pi,np.array(ids));selected=mask&valid;dots=np.einsum('ij,ij->i',cn[selected],fn[pi[selected]]);result['regions'][name]={'polygons':len(ids),'flatPolygons':int((~smooth[ids]).sum()),'cornerVsFaceNormalAngleDegrees':percent(np.degrees(np.arccos(np.clip(dots,-1,1))))}
    return result
g=bpy.data.objects['Actual selected donor, compact interior flow, unaccepted'];g.data.calc_loop_triangles();assert np.array_equal(np.array([v.co[:] for v in g.data.vertices]),f['finalNativeXYZ']);assert np.array_equal(np.array([t.vertices[:] for t in g.data.loop_triangles]),f['triangles']);objects={g.name:measure(g,True)}
for name in ['Exact selected Hunyuan high-poly PBR donor, display frame only','Actual selected donor surface with wearer cuts, unaccepted','Actual selected donor, measured lumen registration, unaccepted']:objects[name]=measure(bpy.data.objects[name])
data=glb.read_bytes();assert sha(glb)=='800d7a9717757b90b296a78c605cddb698c68d399a96e403aa381103e77d2eba';size,kind=struct.unpack_from('<II',data,12);assert kind==0x4e4f534a;doc=json.loads(data[20:20+size]);primitive=doc['meshes'][0]['primitives'][0];normalInput={'originalPrimitiveAttributes':list(primitive['attributes']),'hasNormalAccessor':'NORMAL' in primitive['attributes']}
if normalInput['hasNormalAccessor']:
    binaryStart=20+size+8
    def accessor(index):
        a=doc['accessors'][index];view=doc['bufferViews'][a['bufferView']];dtype=np.dtype({5126:'<f4',5125:'<u4',5123:'<u2'}[a['componentType']]);width={'VEC3':3,'SCALAR':1}[a['type']];return np.ndarray((a['count'],width),dtype=dtype,buffer=data,offset=binaryStart+view.get('byteOffset',0)+a.get('byteOffset',0),strides=(view.get('byteStride',dtype.itemsize*width),dtype.itemsize)).copy()
    vp=accessor(primitive['attributes']['POSITION']);vn=accessor(primitive['attributes']['NORMAL']);indices=accessor(primitive['indices']).reshape(-1,3);face=np.cross(vp[indices[:,1]]-vp[indices[:,0]],vp[indices[:,2]]-vp[indices[:,0]]);length=np.linalg.norm(face,axis=1);valid=length>1e-12;face=face[valid]/length[valid,None];dots=np.einsum('ij,ikj->ik',face,vn[indices[valid]]);normalInput['accessorVsGeometricFaceAngleDegrees']=percent(np.degrees(np.arccos(np.clip(dots,-1,1))).ravel())
result={'status':'UNACCEPTED readonly actual donor normal/geometry isolation','pins':pins,'recipeSHA256':sha(__file__),'objects':objects,'originalGLBNormalInput':normalInput,'bodyPairs':len(f['bodyTrianglePairs']),'selfPairs':len(f['selfTrianglePairs']),'limits':['Corner versus polygon angles and flags distinguish shading state, not played appearance acceptance or a geometry repair. Source region tags are descriptive donor-coordinate thresholds, not final semantic segmentation.','Actual folded/coarse facets remain in vertex/polygon geometry even if smooth display improves appearance. No smoothing/normal mutation/save/recolor/shrink/capture/body-head-51bind change or promotion. Root solejudge/allM0-M5open.']};assert pins=={x:sha(x) for x in pins};out.write_text(json.dumps(result,indent=2)+'\n');print('ACTUAL_DONOR_NORMALS',json.dumps(objects[g.name]),flush=True)
