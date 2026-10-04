"""Whole-surface CPU metrology on existing fields/streams; no posing or capture."""
import collections, gzip, hashlib, json, time
from pathlib import Path
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

root=Path.cwd();out=Path(__file__).resolve().parent;source=out.parent/'body52'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
freeze=json.loads((source/'source.json').read_text())
for path,pin in freeze['pins'].items():assert sha(root/path)==pin['sha256']
n=np.load(source/'native-fields.npz');e=np.load(source/'export-fields.npz')
old=root/'docs/evidence/hero-remaster/anatomical-foundation-2026-10-03/user-agent1/diagnostic02'
driver=json.loads((old/'driver.json').read_text());names=n['boneNames'].tolist()
normalize=lambda name:name.replace('.','').replace('_','')
order=[list(map(normalize,names)).index(normalize(s)) for s in e['jointNames']]
C=np.array([[1,0,0,0],[0,0,1,0],[0,-1,0,0],[0,0,0,1]],float)
rest=lambda label:(np.column_stack([n[label+'XYZ'],np.ones(len(n[label+'XYZ']))])@(C@n[label+'World']).T)[:,:3]
full=np.memmap(old/'body-native-full.f64',dtype='<f8',mode='r',shape=(529,13380,3))
four=np.memmap(old/'body-native-four.f64',dtype='<f8',mode='r',shape=(529,13380,3))
assert np.max(np.linalg.norm(four[0]-rest('canonicalFour'),axis=1))<2e-6
assert np.max(np.linalg.norm(full[0]-rest('originalFull'),axis=1))<2e-6
assert all(trs=={'location':[0.,0.,0.],'quaternionWXYZ':[1.,0.,0.,0.],'scale':[1.,1.,1.]}
           for trs in driver['frames'][0]['poseBasisBlender'].values())
assert not (out/'assessment.json').exists()
start=time.monotonic()
def topo(vertices,triangles):
    edges=np.concatenate([triangles[:,[0,1]],triangles[:,[1,2]],triangles[:,[2,0]]])
    keys=np.sort(edges,axis=1);unique,inverse,counts=np.unique(keys,axis=0,return_inverse=True,return_counts=True)
    directed=np.where(edges[:,0]<edges[:,1],1,-1);tot=np.bincount(inverse,weights=directed,minlength=len(unique))
    neighbors=[set() for _ in vertices]
    for a,b in unique:neighbors[a].add(int(b));neighbors[b].add(int(a))
    seen=set();components=[]
    for v in range(len(vertices)):
        if v in seen:continue
        todo=[v];seen.add(v);size=0
        while todo:
            k=todo.pop();size+=1
            for q in neighbors[k]:
                if q not in seen:seen.add(q);todo.append(q)
        components.append(size)
    boundary=unique[counts==1];bn=collections.defaultdict(set)
    for a,b in boundary:bn[int(a)].add(int(b));bn[int(b)].add(int(a))
    seen=set();loops=0;branches=0
    for v in bn:
        if v in seen:continue
        todo=[v];seen.add(v);valid=True
        while todo:
            k=todo.pop();valid=valid and len(bn[k])==2
            for q in bn[k]:
                if q not in seen:seen.add(q);todo.append(q)
        if valid:loops+=1
        else:branches+=1
    tri=vertices[triangles];area=np.linalg.norm(np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]),axis=1)/2
    return {'vertices':len(vertices),'triangles':len(triangles),'edges':len(unique),
            'components':sorted(components,reverse=True),'boundaryEdges':int((counts==1).sum()),
            'boundaryLoops':loops,'branchedBoundaryComponents':branches,'nonManifoldEdges':int((counts>2).sum()),
            'inconsistentTwoFaceEdgeDirections':int(((counts==2)&(tot!=0)).sum()),
            'zeroAreaTrianglesBelow1e12M2':int((area<1e-12).sum()),'minimumAreaM2':float(area.min()),
            'EulerCharacteristic':len(vertices)-len(unique)+len(triangles)},neighbors
def sat(a,b,epsilon=1e-9):
    # Same normalized finite-triangle separating-axis rule as existing JS audit.
    ea=np.roll(a,-1,axis=1)-a;eb=np.roll(b,-1,axis=1)-b
    na=np.cross(ea[:,0],ea[:,1]);nb=np.cross(eb[:,0],eb[:,1]);axes=[na,nb]
    for i in range(3):
        for j in range(3):axes.append(np.cross(ea[:,i],eb[:,j]))
    parallel=np.linalg.norm(np.cross(na,nb),axis=1)<1e-8*np.linalg.norm(na,axis=1)*np.linalg.norm(nb,axis=1)
    for edges in [ea,eb]:
        for j in range(3):axes.append(np.where(parallel[:,None],np.cross(na,edges[:,j]),0))
    keep=np.ones(len(a),bool)
    for axis in axes:
        length=np.linalg.norm(axis,axis=1);valid=length>1e-14
        unit=axis/np.where(valid,length,1)[:,None]
        pa=np.einsum('nvc,nc->nv',a,unit);pb=np.einsum('nvc,nc->nv',b,unit)
        keep&=~(valid&((pa.max(1)<pb.min(1)-epsilon)|(pb.max(1)<pa.min(1)-epsilon)))
    return keep
def crossing(a,b):
    # Strict segment/triangle interior crossing, with >2um endpoint plane separation.
    found=np.zeros(len(a),bool)
    for x,y in [(a,b),(b,a)]:
        u=y[:,1]-y[:,0];v=y[:,2]-y[:,0];normal=np.cross(u,v);normal/=np.linalg.norm(normal,axis=1)[:,None]
        uu=np.einsum('nc,nc->n',u,u);vv=np.einsum('nc,nc->n',v,v);uv=np.einsum('nc,nc->n',u,v);det=uu*vv-uv*uv
        for edge in range(3):
            p=x[:,edge];q=x[:,(edge+1)%3];d0=np.einsum('nc,nc->n',p-y[:,0],normal);d1=np.einsum('nc,nc->n',q-y[:,0],normal)
            valid=((d0>2e-6)&(d1<-2e-6))|((d0<-2e-6)&(d1>2e-6))
            denominator=d0-d1;t=d0/np.where(abs(denominator)>1e-20,denominator,1)
            r=p+t[:,None]*(q-p)-y[:,0];ru=np.einsum('nc,nc->n',r,u);rv=np.einsum('nc,nc->n',r,v)
            beta=(vv*ru-uv*rv)/np.where(det>1e-30,det,1);gamma=(uu*rv-uv*ru)/np.where(det>1e-30,det,1)
            found|=valid&(beta>1e-6)&(gamma>1e-6)&(beta+gamma<1-1e-6)
    return found
def detect(vertices,faces,logical_ids):
    tree=BVHTree.FromPolygons([Vector(x) for x in vertices],faces.tolist(),all_triangles=True)
    pairs=np.array(tree.overlap(tree),dtype=int).reshape(-1,2);pairs=pairs[pairs[:,0]<pairs[:,1]]
    shared=np.any(logical_ids[faces[pairs[:,0]]][:,:,None]==logical_ids[faces[pairs[:,1]]][:,None,:],axis=(1,2))
    pairs=pairs[~shared]
    a=vertices[faces[pairs[:,0]]];b=vertices[faces[pairs[:,1]]]
    good=(np.linalg.norm(np.cross(a[:,1]-a[:,0],a[:,2]-a[:,0]),axis=1)>1e-14)&(np.linalg.norm(np.cross(b[:,1]-b[:,0],b[:,2]-b[:,0]),axis=1)>1e-14)
    degenerate=int((~good).sum());pairs=pairs[good];a=a[good];b=b[good]
    keep=sat(a,b);pairs=pairs[keep];proper=crossing(a[keep],b[keep]) if len(pairs) else np.array([],bool)
    return pairs,proper,degenerate
analytic=np.array([[-1.,-1.,0.],[1.,-1.,0.],[0.,1.,0.]])
fixtures=[('parallelSeparated',analytic+np.array([0,0,.1]),False,False),
          ('coplanarSeparated',analytic+np.array([4,0,0]),False,False),
          ('coplanarOverlap',analytic*.8,True,False),
          ('strictInteriorCross',np.array([[0.,0.,-1.],[0.,0.,1.],[.7,0.,0.]]),True,True)]
method_checks=0
for label,b,contact,strict in fixtures:
    for reverse in [False,True]:
        for transformed in [False,True]:
            a=analytic[::-1] if reverse else analytic;bb=b[::-1] if reverse else b
            if transformed:
                angle=.27;rotation=np.array([[1,0,0],[0,np.cos(angle),-np.sin(angle)],[0,np.sin(angle),np.cos(angle)]])
                a=a@rotation.T+[.65,.12,-.08];bb=bb@rotation.T+[.65,.12,-.08]
            assert bool(sat(a[None],bb[None])[0])==contact,label
            assert bool(crossing(a[None],bb[None])[0])==strict,label
            method_checks+=2
print('FINITE_METROLOGY_ANALYTIC_CHECKS',method_checks,flush=True)
canonical_tri=n['canonicalFourTriangles'];canonical_rest=rest('canonicalFour')
body_topology,neighbors=topo(canonical_rest,canonical_tri)
H=float(np.ptp(canonical_rest[:,1]));radius=H*.08
joint_native=np.einsum('ab,jbc->jac',C@n['rigWorld'],n['rigRest'])
rois={}
for label,joint in [('shoulder.L','upperArm.L'),('shoulder.R','upperArm.R'),('hip.L','thigh.L'),('hip.R','thigh.R')]:
    rois[label]=np.linalg.norm(canonical_rest-joint_native[names.index(joint),:3,3],axis=1)<=radius
dom=np.argmax(n['canonicalFourWeights'],axis=1)
face_class=[]
for face in canonical_tri:
    count=collections.Counter(dom[face]);face_class.append(names[max(count,key=count.get)])
logical=np.arange(len(canonical_rest));records=[];witnesses=[]
def body_record(vertices,domain,frame):
    pairs,proper,degenerate=detect(vertices,canonical_tri,logical)
    classes=collections.Counter('|'.join(sorted([face_class[a],face_class[b]])) for a,b in pairs)
    local=0
    for a,b in pairs[proper]:
        targets=set(canonical_tri[b]);local+=any(neighbors[int(v)]&targets for v in canonical_tri[a])
    regional={k:int(np.any(mask[canonical_tri[pairs]].reshape(len(pairs),-1),axis=1).sum()) if len(pairs) else 0 for k,mask in rois.items()}
    area=np.linalg.norm(np.cross(vertices[canonical_tri[:,1]]-vertices[canonical_tri[:,0]],vertices[canonical_tri[:,2]]-vertices[canonical_tri[:,0]]),axis=1)
    base=np.linalg.norm(np.cross(canonical_rest[canonical_tri[:,1]]-canonical_rest[canonical_tri[:,0]],canonical_rest[canonical_tri[:,2]]-canonical_rest[canonical_tri[:,0]]),axis=1)
    ratio=area/base
    row={'domain':domain,'frame':frame,'pairs':len(pairs),'strictCrossingPairs':int(proper.sum()),'localOneEdgeStrictPairs':local,
         'classes':dict(classes),'strictClasses':dict(collections.Counter('|'.join(sorted([face_class[a],face_class[b]])) for a,b in pairs[proper])),'regionPairs':regional,'regionStrictPairs':{k:int(np.any(mask[canonical_tri[pairs[proper]]].reshape(int(proper.sum()),-1),axis=1).sum()) if proper.any() else 0 for k,mask in rois.items()},'minimumAreaRatio':float(ratio.min()),'areaRatioBelow0p1Triangles':int((ratio<.1).sum()),
         'degenerateCandidatePairsUnclassified':degenerate}
    for a,b in pairs[proper][:6]:
        witnesses.append({'domain':domain,'frame':frame,'triangleA':int(a),'triangleB':int(b),'nativeIDsA':canonical_tri[a].tolist(),'nativeIDsB':canonical_tri[b].tolist(),
                          'XYZ_A':vertices[canonical_tri[a]].tolist(),'XYZ_B':vertices[canonical_tri[b]].tolist()})
    records.append(row);return row
rest_records=[body_record(canonical_rest,'canonical_rest',0)]
differences=[]
for frame in range(529):
    body_record(full[frame],'syntheticFull',frame);body_record(four[frame],'syntheticFour',frame)
    gap=np.linalg.norm(full[frame]-four[frame],axis=1)
    differences.append({'frame':frame,'timeS':driver['frames'][frame]['timeS'],'maximumM':float(gap.max()),'nativeVertexID':int(gap.argmax()),
                        'regions':{k:{'maximumM':float(gap[mask].max()),'verticesAbove1mm':int((gap[mask]>1e-3).sum())} for k,mask in rois.items()}})
    if frame%48==0:print('FULL_BODY_EXISTING_NATIVE',frame,records[-1]['pairs'],records[-1]['strictCrossingPairs'],flush=True)
    assert time.monotonic()-start<900,'Own CPU metrology cap'
# Assemble current rendered native parts. Only head's exactly co-located seam
# positions are logical aliases for adjacency exclusion; no geometry is welded.
parts=['renderedBody','protectedHead','cheek'];vertices=[];faces=[];part_ids=[];logical_ids=[];offset=0;logical_offset=0
rest_parts={};dense_parts={};topologies={};rep_parts={}
for code,label in enumerate(parts):
    xyz=rest(label);rest_parts[label]=xyz
    w=n[label+'Weights'][:,order];w=w/w.sum(1)[:,None];dense_parts[label]=w
    f=n[label+'Triangles'];topologies[label],_=topo(xyz,f)
    _,aliases=np.unique(xyz,axis=0,return_inverse=True)
    logical_ids.extend((aliases+logical_offset).tolist());logical_offset+=int(aliases.max())+1
    vertices.append(xyz);faces.append(f+offset);part_ids.extend([code]*len(f));offset+=len(xyz)
    # Current export representatives preserve the installed normalized Float32 field.
    rep={int(native):i for i,native in enumerate(e[label+'NativeIDs'])}
    if label=='renderedBody':
        representative=np.array([rep[i] for i in range(len(xyz))]);rep_parts[label]=representative
        dw=np.zeros((len(xyz),51));weights=e[label+'NormalizedWeights'][representative].astype(np.float32).astype(float)
        for k in range(4):np.add.at(dw,(np.arange(len(xyz)),e[label+'JointIndices'][representative,k]),weights[:,k])
        dense_parts[label]=dw;rest_parts[label]=e[label+'FileWorldXYZ'][representative]
    unique_xyz=np.unique(xyz,axis=0);topologies[label]['virtualExactPositionWeldTopology'],_=topo(unique_xyz,aliases[f])
    topologies[label]['exactCoLocatedNativePositions']=len(xyz)-len(set(map(tuple,xyz)))
assembled_faces=np.concatenate(faces);assembled_part=np.array(part_ids);assembled_logical=np.array(logical_ids)
def deform(label,K):
    p=np.column_stack([rest_parts[label],np.ones(len(rest_parts[label]))])
    return np.einsum('vj,jab,vb->va',dense_parts[label],K,p,optimize=True)[:,:3]
assembled=[]
def assembly_record(pos,domain,frame):
    pairs,proper,degenerate=detect(pos,assembled_faces,assembled_logical)
    classes=collections.Counter('|'.join(sorted([parts[assembled_part[a]],parts[assembled_part[b]]])) for a,b in pairs)
    strict=collections.Counter('|'.join(sorted([parts[assembled_part[a]],parts[assembled_part[b]]])) for a,b in pairs[proper])
    assembled.append({'domain':domain,'frame':frame,'pairs':len(pairs),'strictCrossingPairs':int(proper.sum()),'classes':dict(classes),
                      'strictClasses':dict(strict),'degenerateCandidatePairsUnclassified':degenerate})
    for a,b in pairs[proper][:4]:witnesses.append({'domain':domain,'frame':frame,'triangleA':int(a),'triangleB':int(b),'partA':parts[assembled_part[a]],'partB':parts[assembled_part[b]],
                                               'XYZ_A':pos[assembled_faces[a]].tolist(),'XYZ_B':pos[assembled_faces[b]].tolist()})
    return assembled[-1]
assembly_record(np.concatenate(vertices),'assembledCanonicalRest',0)
native_parity=[]
for frame,row in enumerate(driver['frames']):
    W=np.array([np.array(row['jointWorldColumnMajor'][names[j]]).reshape(4,4).T for j in order]);K=W@e['inverseBinds']
    posed=[deform(label,K) for label in parts]
    native_ids=n['renderedBodySourceIDs'].astype(int)
    native_parity.append(float(np.linalg.norm(posed[0]-four[frame,native_ids],axis=1).max()))
    assembly_record(np.concatenate(posed),'assembledSyntheticFour',frame)
    if frame%48==0:print('WHOLE_CURRENT_ASSEMBLY_NATIVE',frame,assembled[-1]['pairs'],assembled[-1]['strictCrossingPairs'],flush=True)
    assert time.monotonic()-start<1200,'Own CPU metrology cap'
actual_path=root/'docs/evidence/hero-remaster/user-agent3-qa-2026-10-03/garment47/first.weights.ndjson.gz'
with gzip.open(actual_path,'rt') as f:actual=[json.loads(line) for line in f]
assert len(actual)==703
matrices=np.array([r['matrices'] for r in actual]).reshape(703,51,4,4).transpose(0,1,3,2)
film_path=root/'docs/evidence/hero-remaster/user-agent3-qa-2026-10-03/presentation50/report.json.gz'
film=json.loads(gzip.decompress(film_path.read_bytes()));samples=film['cases'][0]['samples'][:176]
bone_world=np.array([K@np.linalg.inv(e['inverseBinds']) for K in matrices])
max_matrix_gap=0.
for sample in samples:
    tick=int(sample['label'].split('input ')[1].split('/')[0]);by_name={normalize(x[0]):np.array(x[1:]).reshape(4,4).T for x in sample['matrices']}
    for j,name in enumerate(e['jointNames']):max_matrix_gap=max(max_matrix_gap,float(np.abs(bone_world[tick-1,j]-by_name[normalize(name)]).max()))
assert max(native_parity)<2e-6,('Existing native body field mismatch',max(native_parity))
# Captures have distinct render histories; retain measured mismatch rather than
# pretending the separate film is a visual witness of the703matrix stream.
actual_equivalence={'maximumAbsMatrixDifference':max_matrix_gap,'samePerTickBodyPose':max_matrix_gap<2e-12,'conclusion':'Separate existing captures; do not pair garment47 numeric frames with presentation50 film.'}
actual_body_differences=[]
def full_deform(label,K):
    p=np.column_stack([rest(label),np.ones(len(n[label+'XYZ']))]);w=n[label+'Weights'][:,order];w=w/w.sum(1)[:,None]
    return np.einsum('vj,jab,vb->va',w,K,p,optimize=True)[:,:3]
for frame,K in enumerate(matrices):
    pf=full_deform('originalFull',K);p4=full_deform('canonicalFour',K)
    body_record(pf,'actual47Full',frame+1);body_record(p4,'actual47Four',frame+1)
    gap=np.linalg.norm(pf-p4,axis=1);actual_body_differences.append({'inputTick':frame+1,'maximumM':float(gap.max()),'nativeVertexID':int(gap.argmax()),'regions':{k:{'maximumM':float(gap[mask].max()),'verticesAbove1mm':int((gap[mask]>1e-3).sum())} for k,mask in rois.items()}})
    assembly_record(np.concatenate([deform(label,K) for label in parts]),'assembledActualRookie',frame+1)
    if frame%120==0:print('WHOLE_CURRENT_ASSEMBLY_ACTUAL',frame+1,assembled[-1]['pairs'],assembled[-1]['strictCrossingPairs'],flush=True)
    assert time.monotonic()-start<2400,'Own CPU metrology cap'
for sample in samples:
    tick=int(sample['label'].split('input ')[1].split('/')[0]);by_name={normalize(x[0]):np.array(x[1:]).reshape(4,4).T for x in sample['matrices']}
    W=np.array([by_name[normalize(name)] for name in e['jointNames']]);K=W@e['inverseBinds']
    body_record(full_deform('canonicalFour',K),'actual50Four',tick)
    assembly_record(np.concatenate([deform(label,K) for label in parts]),'assembledActual50',tick)
report={'status':'UNACCEPTED_WHOLE_CURRENT_BODY_EXISTING_STREAM_ASSESSMENT',
        'sourceFreezeSHA256':sha(source/'source.json'),'recipeSHA256':sha(__file__),
        'wholeFittingBodyTopology':body_topology,'currentPartTopologies':topologies,
        'figureHeightM':H,'regionalSphereRadiusM':radius,'regionalSphereCentersFileWorldM':{label:joint_native[names.index(j),:3,3].tolist() for label,j in [('shoulder.L','upperArm.L'),('shoulder.R','upperArm.R'),('hip.L','thigh.L'),('hip.R','thigh.R')]},
        'records':records,'assemblyRecords':assembled,'fullVsFourDifferences':differences,
        'nativeFourVsCurrentExportFieldMaxResidualM':max(native_parity),'distinctActualCaptureComparison':actual_equivalence,'actual47FullVsFourDifferences':actual_body_differences,
        'actualMatrixStreamSHA256':sha(actual_path),'existingPlayedFilmReportSHA256':sha(film_path),'elapsedS':time.monotonic()-start,
        'method':{'analyticSATAndStrictCrossingChecks':method_checks,'broadphase':'Blender BVHTree triangle self-overlap; unordered pairs only.',
                  'narrowphase':'Independent normalized finite triangle SAT, epsilon1e-9m; vertex-sharing adjacency excluded.',
                  'strictCrossing':'Segment crosses opposite triangle interior; both signed endpoint distances >2um; barycentric components >1e-6. Witness is finite crossing, not global penetration depth.',
                  'areaRatio':'Actual world-area ratio includes global character scale; synthetic area ratios share rest frame. Fixed canonical rest tessellation, not per-pose retriangulation.',
                  'headSeams':'Exact co-located positions within each native part are adjacency aliases only. Geometry/indices remain unchanged; raw and seam-aware topology reported separately.',
                  'regions':'Sphere of radius0.08*figureHeight around rest upper-arm heads and thigh heads; explicit proxies, not anatomical segmentation ground truth.'},
        'limits':['Full fitting native body includes its historical gray native head. Current rendered body plus protected generated head and cheek are assessed separately.',
                  '529native samples cover existing11s forward/reverse synthetic48Hz FK;703actual matrices cover only one5.858s Rookie backward-lean window. No Pro/landing/full86-bank/device/facial animation coverage implied.',
                  'Existing actual47 effective51 skin matrices repeat byte-exact and its manual-four residual is0. Separate actual50 film has176 existing bone-world samples. These two body-pose streams differ; film50 does not witness stream47 numerical frames. No new Game, pose, rig/export or render capture.',
                  'Offline skin fields use current installed primary-four contract; no GPU readback, corrective shape/collision or unsampled-time guarantee.',
                  'Any degenerate candidate pair remains unclassified, never a clearance pass. Parent alone judges clips; all M0–M5 remain open.']}
with gzip.open(out/'witnesses.json.gz','wt') as f:json.dump(witnesses,f,separators=(',',':'))
report['witnessArchiveSHA256']=sha(out/'witnesses.json.gz')
(out/'assessment.json').write_text(json.dumps(report,indent=2)+'\n')
for path,pin in freeze['pins'].items():assert sha(root/path)==pin['sha256']
print('WHOLE_BODY_METROLOGY_READY',len(records),len(assembled),report['elapsedS'],flush=True)
