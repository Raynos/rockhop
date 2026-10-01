"""Actual native anatomical graft continuation of source-sheet clipping."""
from scipy.interpolate import RBFInterpolator

NATIVE=ROOT/'rig-adapter01/anatomical-eye-donor01/standalone01'
bridge=[];graft_reports=[];rays=[]
def surface_hit(points,faces,y,z):
    xyz=points[faces];yz=xyz[:,:,1:];p=np.array([y,z])
    eligible=np.flatnonzero((yz.min(1)<=p+1e-10).all(1)&(yz.max(1)>=p-1e-10).all(1))
    a=yz[eligible,1]-yz[eligible,0];b=yz[eligible,2]-yz[eligible,0];d=p-yz[eligible,0]
    det=a[:,0]*b[:,1]-a[:,1]*b[:,0];keep=abs(det)>1e-15
    eligible=eligible[keep];a=a[keep];b=b[keep];d=d[keep];det=det[keep]
    u=(d[:,0]*b[:,1]-d[:,1]*b[:,0])/det;q=(a[:,0]*d[:,1]-a[:,1]*d[:,0])/det
    bary=np.c_[1-u-q,u,q];inside=(bary>=-1e-8).all(1)
    return None if not inside.any() else float(np.max(np.sum(bary[inside]*xyz[eligible[inside],:,0],axis=1)))

def ordered(loop,cy,cz,points):
    loop=np.array(loop);p=points[loop,1:]-[cy,cz]
    if np.sum(p[:,1]*np.roll(p[:,0],-1)-p[:,0]*np.roll(p[:,1],-1))<0:loop=loop[::-1]
    loop=np.roll(loop,-int(np.argmax(points[loop,2])))
    lengths=np.linalg.norm(np.roll(points[loop],-1,axis=0)-points[loop],axis=1)
    return loop,np.r_[0,np.cumsum(lengths[:-1])]/lengths.sum()*2*np.pi

def zipper(a,aa,b,bb):
    i=j=0;result=[]
    while i<len(a) or j<len(b):
        na=aa[(i+1)%len(a)]+(2*np.pi if i+1>=len(a) else 0) if i<len(a) else np.inf
        nb=bb[(j+1)%len(b)]+(2*np.pi if j+1>=len(b) else 0) if j<len(b) else np.inf
        if na<=nb:result.append([int(a[i%len(a)]),int(b[j%len(b)]),int(a[(i+1)%len(a)])]);i+=1
        else:result.append([int(a[i%len(a)]),int(b[j%len(b)]),int(b[(j+1)%len(b)])]);j+=1
    return np.array(result,dtype=int)

def orient_strip(strip,reference,reference_vertices):
    points=np.array(expanded['POSITION'],dtype='<f4')
    _,canonical=np.unique(points,axis=0,return_inverse=True)
    directed=set((int(a),int(b)) for f in canonical[reference] for a,b in zip(f,np.roll(f,-1)))
    physical_vertices=set(canonical[list(reference_vertices)])
    shared=[(int(a),int(b)) for f in canonical[strip] for a,b in zip(f,np.roll(f,-1)) if a in physical_vertices and b in physical_vertices]
    same=sum(edge in directed for edge in shared);opposite=sum(edge[::-1] in directed for edge in shared)
    assert same+opposite==len(shared) and (same==0 or opposite==0),'Consistent existing seam winding'
    return strip[:,::-1] if same else strip

def add_points(points,normals=None):
    indices=[]
    for i,point in enumerate(points):
        indices.append(len(expanded['POSITION']))
        for key in expanded:
            expanded[key].append({'POSITION':point,'NORMAL':normals[i] if normals is not None else [1.,0,0],
                'TEXCOORD_0':[.5,.5],'JOINTS_0':[4,0,0,0],'WEIGHTS_0':[1.,0,0,0]}[key])
    return np.array(indices)

def native_loops(quads):
    count=Counter(tuple(sorted((int(a),int(b)))) for f in quads for a,b in zip(f,np.roll(f,-1)))
    edges=[edge for edge,n in count.items() if n==1];adj=defaultdict(list)
    for a,b in edges:adj[a].append(b);adj[b].append(a)
    assert all(len(n)==2 for n in adj.values());unseen=set(adj);result=[]
    while unseen:
        first=min(unseen);loop=[first];prev=None;cur=first
        while True:
            nxt=next(n for n in adj[cur] if n!=prev)
            if nxt==first:break
            assert nxt not in loop;loop.append(nxt);prev,cur=cur,nxt
        unseen-=set(loop);result.append(loop)
    return result

def eye_geometry(prefix,cy,cz,apex,shift=0):
    result=[]
    for suffix in ['cornea','sclera_iris']:
        mesh=next(m for m in ddoc['meshes'] if m['name']==prefix+'_'+suffix);p0=mesh['primitives'][0]
        points=array(ddoc,dbin,p0['attributes']['POSITION']).astype(float)
        offset=np.array([apex-.0152355616+shift,cy,cz-(-.033 if prefix=='R' else .033)])
        result.append((points+offset,array(ddoc,dbin,p0['indices']).reshape(-1,3)))
    return result

eye_shifts={}
for eye,cy,cz,apex in SEEDS:
    rings=[l for l in loops if np.max(abs(positions[l,1]-cy))<HEIGHT+.0001 and np.max(abs(positions[l,2]-cz))<WIDTH+.0001]
    assert len(rings)==2;rings.sort(key=lambda l:positions[l,0].mean(),reverse=True)
    front,fa=ordered(rings[0],cy,cz,positions);back,ba=ordered(rings[1],cy,cz,positions)
    native_side='R' if eye=='positiveZ' else 'L';prefix='L' if eye=='positiveZ' else 'R'
    nd=np.load(NATIVE/f'fitted-native-{native_side}-lids.npz')
    raw_native=nd['positions'].copy();np0=raw_native.copy();nq=nd['quads'];boundary=native_loops(nq)
    assert len(boundary)==2
    boundary.sort(key=lambda l:np.ptp(np0[l,1])*np.ptp(np0[l,2]),reverse=True)
    outer=boundary[0];inner=boundary[1]
    neighbors=defaultdict(set)
    for f in nq:
        for a,b in zip(f,np.roll(f,-1)):neighbors[int(a)].add(int(b));neighbors[int(b)].add(int(a))
    distances={i:0 for i in outer};fringe=set(outer)
    for depth in range(1,3):
        nxt={b for a in fringe for b in neighbors[a]}-set(distances)
        distances.update({i:depth for i in nxt});fringe=nxt
    shifts=[]
    for i in outer:
        angle=np.arctan2((np0[i,1]-cy)/HEIGHT,(np0[i,2]-cz)/WIDTH)
        yy=cy+.90*HEIGHT*np.sin(angle);zz=cz+.90*WIDTH*np.cos(angle)
        xx=surface_hit(v,tri,yy,zz);assert xx is not None
        shifts.append(np.array([xx,yy,zz])-np0[i])
    shifts=np.array(shifts)
    for i,depth in distances.items():
        if depth>=2:continue
        nearest=int(np.argmin(np.linalg.norm(raw_native[outer]-raw_native[i],axis=1)))
        np0[i]+=shifts[nearest]*(1. if depth==0 else .5)
    assert np.array_equal(np0[inner],raw_native[inner]),'Actual native anatomical aperture preserved'
    indices=add_points(np0,nd['normals']);nt=np.concatenate([nq[:,[0,1,2]],nq[:,[0,2,3]]])
    nt=indices[nt];current=np.array(expanded['POSITION'],dtype='<f4')
    outloop,oa=ordered(indices[outer],cy,cz,current);inloop,ia=ordered(indices[inner],cy,cz,current)
    join=orient_strip(zipper(front,fa,outloop,oa),output,set(front))
    wall=orient_strip(zipper(inloop,ia,back,ba),nt,set(inloop))
    local=np.concatenate([nt,join,wall]);bridge.extend(local.tolist())
    # Place actual donor behind retained anatomical tissue, never overwrite lid
    # geometry with sampled sphere/cornea coordinates. Deterministic dense
    # triangle probes bound clearance before exact triangle intersections.
    cp,ct=eye_geometry(prefix,cy,cz,apex)[0]
    tri_points=current[local].astype(float);samples=[]
    for i in range(5):
        for j in range(5-i):
            weights=np.array([i,j,4-i-j])/4
            for ti,point in enumerate(np.einsum('i,tij->tj',weights,tri_points)):
                category='native_lid' if ti<len(nt) else ('front_join' if ti<len(nt)+len(join) else 'inward_wall')
                samples.append((point,category,ti,weights.tolist()))
    gap=0.;covered=0;worst=None;categories=defaultdict(lambda:{'samples':0,'samplesInsideGlobeProjection':0,'maxFrontPenetrationM':0.})
    for point,category,ti,bary in samples:
        categories[category]['samples']+=1
        hit=surface_hit(cp,ct,point[1],point[2])
        if hit is not None:
            covered+=1;categories[category]['samplesInsideGlobeProjection']+=1
            penetration=hit-point[0]
            categories[category]['maxFrontPenetrationM']=max(categories[category]['maxFrontPenetrationM'],float(penetration))
            if penetration>gap:
                gap=penetration;worst={'category':category,'localTriangle':int(ti),'globalVertexIDs':local[ti].tolist(),
                    'trianglePositionsM':tri_points[ti].tolist(),'barycentricProbe':bary,
                    'probePositionM':point.tolist(),'actualCorneaFrontXM':hit,'frontPenetrationM':float(penetration)}
    shift=-(gap+.00025)
    if abs(shift)>=.008:
        iris=eye_geometry(prefix,cy,cz,apex)[1]
        np.savez_compressed(OUT/'clearance-registration-failure.npz',positions=current,sourceTriangles=output,
            nativeTriangles=nt,frontJoinTriangles=join,inwardWallTriangles=wall,
            actualCorneaPositions=cp,actualCorneaTriangles=ct,actualIrisPositions=iris[0],actualIrisTriangles=iris[1],
            nativeSourcePositions=raw_native,nativeRegisteredPositions=np0)
        failure={'status':'REJECTED before export at unchanged8mm eye-registration safety bound',
            'eye':eye,'nativeSide':native_side,'eyeDonorPrefix':prefix,
            'sourceSHA256':hashlib.sha256(raw).hexdigest(),'actualEyeDonorSHA256':hashlib.sha256(draw).hexdigest(),
            'nativeAperturePositionsExact':True,'nativeRegistrationOnlyOuterBoundaryAndOneRow':True,
            'originalBinarySourceUnchanged':source.read_bytes()==raw,
            'requiredEyeDepthShiftM':shift,'safetyBoundM':.008,'worstProbe':worst,'probeCategories':dict(categories),
            'nativeSourceScale':.0841151730831446,'nativeBasisEyeJointRaw':[-.30775,7.28415,1.24535] if native_side=='R' else [.30775,7.28415,1.24535],
            'targetUnshiftedGlobeCenterM':[apex-.0152355616,cy,cz],
            'fitFrame':'Proper native raw Z-forward to riderX,rawY-up toY,rawX to−Z; per-eye translation matching actual retained CC0 donor apex target',
            'candidateExported':False,'GPUWorkPerformed':False,
            'limits':['Sampled front-clearance failure, not an exact triangle intersection report.',
                'Current11 preserved; all registered native and seam geometry retained in private failure NPZ for parent audit.',
                'Initial UV-split raw-index guard failure separately retained. No bound relaxed or new appearance claimed.']}
        (EVIDENCE/'clearance-registration-failure.json').write_text(json.dumps(failure,indent=2)+'\n')
        print(json.dumps(failure,indent=2));raise SystemExit(1)
    eye_shifts[prefix]=shift
    cornea,iris=eye_geometry(prefix,cy,cz,apex,shift)
    for yy,zz in [(cy,cz),(cy-.002,cz),(cy+.002,cz),(cy,cz-.005),(cy,cz+.005)]:
        ix=surface_hit(*iris,yy,zz)
        gx=surface_hit(current,local,yy,zz);sx=surface_hit(positions,output,yy,zz)
        assert ix is not None and (gx is None or ix>gx) and (sx is None or ix>sx),'True aperture exposes actual iris'
        rays.append({'eye':eye,'y':yy,'z':zz,'irisFrontX':ix,'nativeGraftFrontX':gx,'retainedSkinFrontX':sx})
    graft_reports.append({'eye':eye,'nativeSide':native_side,'originalNativeQuads':len(nq),'nativeApertureVertices':len(inner),
        'nativeAperturePositionsExact':True,'outerRegistrationBandMaxGraphDepth':1,
        'maxOuterBoundaryRegistrationM':float(np.linalg.norm(shifts,axis=1).max()),
        'actualEyeDepthShiftM':shift,'clearanceProbes':len(samples),'probesInsideCorneaProjection':covered,
        'nativeTriangles':len(nt),'sourceJoinTriangles':len(join),'inwardWallTriangles':len(wall)})

positions=np.array(expanded['POSITION'],dtype='<f4');bridge=np.array(bridge,dtype=np.int64)
joined=np.concatenate([output,bridge]);final,_,finaldirected,_=topology(positions,joined)
assert final==before,(before,final)
oriented=Counter(map(tuple,finaldirected.tolist()));assert max(oriented.values())==1,'Joined surface winding consistent'
areas=np.linalg.norm(np.cross(positions[joined[:,1]]-positions[joined[:,0]],positions[joined[:,2]]-positions[joined[:,0]]),axis=1)/2
assert areas.min()>1e-14 and np.isfinite(positions).all()

# Source-colored skin bake. Healthy surrounding samples exclude old eye/iris
# region and dark non-skin texels. Exact original boundary color is carried to
# the transition edge; all original image bytes remain untouched.
im=doc['images'][5];view=doc['bufferViews'][im['bufferView']]
atlas=np.array(Image.open(io.BytesIO(original[view['byteOffset']:view['byteOffset']+view['byteLength']])).convert('RGB'))
def sample_uv(uv):
    h,w=atlas.shape[:2];ix=np.clip((uv[:,0]*w).astype(int),0,w-1);iy=np.clip((uv[:,1]*h).astype(int),0,h-1)
    return atlas[iy,ix].astype(float)/255
def linear(x):return np.where(x<=.04045,x/12.92,((x+.055)/1.055)**2.4)
def srgb(x):return np.where(x<=.0031308,12.92*x,1.055*np.maximum(x,0)**(1/2.4)-.055)
used=np.unique(bridge);patchpos=positions[used];newuv=np.empty((len(used),2));bitmap=np.zeros((1024,2048,3),dtype=np.uint8)
skin_reports=[]
for ei,(eye,cy,cz,_) in enumerate(SEEDS):
    mask=abs(patchpos[:,2]-cz)<.023;localids=np.flatnonzero(mask)
    yy=abs(v[:,1]-cy);zz=abs(v[:,2]-cz)
    healthy=np.flatnonzero((v[:,0]>.72)&(((yy>.012)&(yy<.019)&(zz<.022))|((zz>.021)&(zz<.027)&(yy<.009))))
    colors=sample_uv(attrs['TEXCOORD_0'][healthy]);is_skin=(colors[:,0]>.28)&(colors[:,0]>colors[:,1])&(colors[:,1]>colors[:,2])&(colors.mean(1)>.28)
    healthy=healthy[is_skin];colors=colors[is_skin];assert len(healthy)>30,'Measured healthy source skin exists'
    points=v[healthy,1:];unique,uniqueid=np.unique(np.round(points,6),axis=0,return_index=True)
    # Actual source texture samples; spatial interpolation supplies skin, not
    # the retired flat constant material or old painted eye pixels.
    interpolation=RBFInterpolator(unique,linear(colors[uniqueid]),kernel='linear',neighbors=min(32,len(unique)),smoothing=1e-6)
    ytop=cy+.012;zleft=cz-.022
    ygrid=ytop-(np.arange(1024)+.5)/1024*.024
    zgrid=zleft+(np.arange(1024)+.5)/1024*.044
    for row in range(0,1024,32):
        y,z=np.meshgrid(ygrid[row:row+32],zgrid,indexing='ij')
        value=interpolation(np.c_[y.ravel(),z.ravel()]).reshape(y.shape+(3,))
        bitmap[row:row+32,ei*1024:(ei+1)*1024]=(srgb(value).clip(0,1)*255+.5).astype(np.uint8)
    newuv[localids,0]=(ei+(patchpos[localids,2]-zleft)/.044)/2
    newuv[localids,1]=(ytop-patchpos[localids,1])/.024
    skin_reports.append({'eye':eye,'healthySourceTextureSampleVertices':len(healthy),'excludedOldPaintedIrisRegion':True})
assert np.isfinite(newuv).all() and ((newuv>=0)&(newuv<=1)).all()
png=io.BytesIO();Image.fromarray(bitmap).save(png,format='PNG')
binary=bytearray(original);result=copy.deepcopy(doc)
def append(data,target=None):
    binary.extend(b'\0'*((-len(binary))%4));offset=len(binary);binary.extend(data)
    entry={'buffer':0,'byteOffset':offset,'byteLength':len(data)}
    if target:entry['target']=target
    result['bufferViews'].append(entry);return len(result['bufferViews'])-1
def put(a,kind,ctype,target=34962):
    a=np.ascontiguousarray(a);entry={'bufferView':append(a.tobytes(),target),'componentType':ctype,'count':len(a),'type':kind}
    if kind=='VEC3':entry.update(min=a.min(0).tolist(),max=a.max(0).tolist())
    result['accessors'].append(entry);return len(result['accessors'])-1
head=result['meshes'][1]['primitives'][0]
for key,old in attrs.items():
    value=np.array(expanded[key],dtype=old.dtype);assert np.array_equal(value[:len(old)],old)
    spec=doc['accessors'][p['attributes'][key]];head['attributes'][key]=put(value,spec['type'],spec['componentType'])
head['indices']=put(output.astype('<u4').ravel(),'SCALAR',5125,34963)
result['images'].append({'name':'Source skin orbital conversion','bufferView':append(png.getvalue()),'mimeType':'image/png'})
result['textures'].append({'source':len(result['images'])-1,'sampler':0})
result['materials'].append({'name':'NEW actual native anatomical lids with source skin bake','pbrMetallicRoughness':{
    'baseColorTexture':{'index':len(result['textures'])-1},'roughnessFactor':.62,'metallicFactor':0},'doubleSided':False})
lookup={int(q):i for i,q in enumerate(used)};localtri=np.array([[lookup[int(q)] for q in t] for t in bridge],dtype='<u4')
norm=np.zeros((len(positions),3))
for t in bridge:
    n=np.cross(positions[t[1]]-positions[t[0]],positions[t[2]]-positions[t[0]])
    norm[t]+=n
norm=norm[used];norm/=np.maximum(np.linalg.norm(norm,axis=1,keepdims=True),1e-20)
headweights=np.tile(np.array([1,0,0,0],dtype='<f4'),(len(used),1));headjoints=np.tile(np.array([4,0,0,0],dtype='<u2'),(len(used),1))
result['meshes'][1]['primitives'].append({'attributes':{'POSITION':put(patchpos,'VEC3',5126),'NORMAL':put(norm.astype('<f4'),'VEC3',5126),
    'TEXCOORD_0':put(newuv.astype('<f4'),'VEC2',5126),'JOINTS_0':put(headjoints,'VEC4',5123),'WEIGHTS_0':put(headweights,'VEC4',5126)},
    'indices':put(localtri.ravel(),'SCALAR',5125,34963),'material':len(result['materials'])-1,'mode':4})
imageoffset=len(result['images']);texoffset=len(result['textures']);sampoffset=len(result['samplers']);matoffset=len(result['materials'])
for im in ddoc['images']:
    im=copy.deepcopy(im);view=ddoc['bufferViews'][im['bufferView']]
    im['bufferView']=append(dbin[view.get('byteOffset',0):view.get('byteOffset',0)+view['byteLength']]);result['images'].append(im)
result['samplers'].extend(copy.deepcopy(ddoc['samplers']))
for tex in ddoc['textures']:
    tex=copy.deepcopy(tex);tex['source']+=imageoffset;tex['sampler']+=sampoffset;result['textures'].append(tex)
for material in ddoc['materials']:
    material=copy.deepcopy(material)
    if 'baseColorTexture' in material['pbrMetallicRoughness']:material['pbrMetallicRoughness']['baseColorTexture']['index']+=texoffset
    result['materials'].append(material)
for mesh in ddoc['meshes']:
    donorprim=mesh['primitives'][0];name=mesh['name'];prefix=name[0];seed=SEEDS[1] if prefix=='R' else SEEDS[0]
    _,cy,cz,apex=seed;a={key:array(ddoc,dbin,index) for key,index in donorprim['attributes'].items()}
    offset=np.array([apex-.0152355616+eye_shifts[prefix],cy,cz-(-.033 if prefix=='R' else .033)])
    a['POSITION']=(a['POSITION']+offset).astype('<f4');count=len(a['POSITION'])
    a['JOINTS_0']=np.tile(np.array([4,0,0,0],dtype='<u2'),(count,1));a['WEIGHTS_0']=np.tile(np.array([1,0,0,0],dtype='<f4'),(count,1))
    primitive=copy.deepcopy(donorprim);primitive['attributes']={key:put(value,'VEC'+str(value.shape[1]),5123 if key=='JOINTS_0' else 5126) for key,value in a.items()}
    primitive['indices']=put(array(ddoc,dbin,donorprim['indices']).ravel(),'SCALAR',ddoc['accessors'][donorprim['indices']]['componentType'],34963)
    primitive['material']+=matoffset;result['meshes'][1]['primitives'].append(primitive)
assert bytes(binary[:len(original)])==original
for key in ['nodes','skins','animations','scenes','scene']:assert result[key]==doc[key]
assert result['meshes'][0]==doc['meshes'][0] and result['meshes'][1]['primitives'][1]==doc['meshes'][1]['primitives'][1]
result['buffers'][0]['byteLength']=len(binary)
encoded=json.dumps(result,separators=(',',':')).encode();encoded+=b' '*((-len(encoded))%4);binary+=b'\0'*((-len(binary))%4)
glb=struct.pack('<4sII',b'glTF',2,28+len(encoded)+len(binary))+struct.pack('<I4s',len(encoded),b'JSON')+encoded+struct.pack('<I4s',len(binary),b'BIN\0')+binary
(OUT/'rider.glb').write_bytes(glb)
np.savez(OUT/'source-face-provenance.npz',sourceTriangle=np.array(conforming_origins,dtype=np.int32),updatedTriangles=output,positions=positions)
np.savez_compressed(OUT/'joined-geometry.npz',positions=positions,sourceTriangles=output,graftTriangles=bridge)
report={'status':'UNACCEPTED actual native anatomical graft trial; independent clearance/conservation and parent appearance review required',
    'sourceSHA256':hashlib.sha256(raw).hexdigest(),'outputSHA256':hashlib.sha256(glb).hexdigest(),'output':str(OUT/'rider.glb'),
    'approach':'Actual CC0 native lid/canthus quad strips; outer one-row registration, source sheet clipping, inward closure, source-skin conversion',
    'priorEyeDefectFailures':6,'newNativeGraftAttempt':1,'newVisibleAnalyticLidRings':0,
    'originalBinaryPrefixExact':True,'bodyCheek19RigAnimationsExact':True,'nativeInnerAperturesExact':True,
    'sourceTopology':before,'joinedTopology':final,'minimumJoinedTriangleAreaM2':float(areas.min()),
    'nativeGrafts':graft_reports,'apertureRays':rays,'skinConversion':skin_reports,'elapsedSeconds':time.monotonic()-start,
    'limits':['Clearance probes and aperture rays are preliminary; exact triangle intersection audit required before GPU.',
        'Skin field derives healthy neighboring source skin; outer UV/material seam needs physical color reconciliation before acceptance.',
        'No appearance grade, neck-motion, gameplay contacts or checkpoint acceptance claimed.']}
(EVIDENCE/'construction.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({key:value for key,value in report.items() if key not in ['nativeGrafts','apertureRays']},indent=2))
