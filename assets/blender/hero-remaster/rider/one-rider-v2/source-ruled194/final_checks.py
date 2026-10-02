"""Additional literal boundary/reference conservation on the same frozen dump."""
from common import *
C,a,F,U,q,c,charts,comparison,sep,refs=source();z=np.load(S/'construction.npz');pr=json.loads((S/'construction-provenance.json').read_text());pf=z['attributeRowPhysicalIDs'][z['indices']];ee=edges(pf);cycle=c['fixedOrientedBoundaryPhysicalIDs'];fixed=zip(cycle,cycle[1:]+cycle[:1]);records=[]
for i,j in fixed:
 edge=tuple(sorted((i,j)));owners=ee[edge];records.append({'physicalEdge':[i,j],'candidateIncidentCount':len(owners),'incidentTriangles':[int(fi) for fi,direction in owners],'oppositeWinding':len(owners)==2 and owners[0][1]!=owners[1][1]})
sourceArea=sum(c2(sub(t[1],t[0]),sub(t[2],t[0]))/2 for t in refs.values());fragmentArea=Q(0);bySource=defaultdict(lambda:Q(0))
for fr in pr['fragments']:
 pts=[tuple(Q(int(n),int(d)) for n,d in p) for p in fr['referenceCorners']];area=c2(sub(pts[1],pts[0]),sub(pts[2],pts[0]))/2;fragmentArea+=area;bySource[fr['sourceFace']]+=area
chartAreaExact=all(bySource[fi]==c2(sub(t[1],t[0]),sub(t[2],t[0]))/2 for fi,t in refs.items());seam=[]
for key,coords in pr['physicalReferenceParameters'].items():
 p=tuple(Q(int(n),int(d)) for n,d in coords)
 if p[1]==0:seam.append(int(key))
endpointPositions=U[c['highSeamEndpointPhysicalIDs']].astype(float);seamResidual=[]
for pid in seam:
 coords=pr['physicalReferenceParameters'][str(pid)];u=float(Q(int(coords[0][0]),int(coords[0][1])));expected=(1-u)*endpointPositions[0]+u*endpointPositions[1];seamResidual.append(float(np.linalg.norm(z['physicalPositions'][pid].astype(float)-expected)))
report={'sameDumpSHA256':sha((S/'construction.npz').read_bytes()),'fixed49OriginalBoundaryEdgesUnsplit':all(x['candidateIncidentCount']==2 and x['oppositeWinding'] for x in records),'fixedBoundaryEdges':records,'exactParameterLensAreaConserved':fragmentArea==sourceArea,'exactPerOriginal47ReferenceFaceAreaConserved':chartAreaExact,'sourceReferenceArea':float(sourceArea),'fragmentReferenceArea':float(fragmentArea),'highSharedChordPhysicalPoints':len(seam),'highSharedChordMinimumY_M':float(z['physicalPositions'][seam,1].min()),'maximumFloat32SharedChordResidualM':max(seamResidual),'uniqueFailedNormalBoundaryPhysicalIDs':sorted({x['physicalID'] for x in pr['constructionFailures'] if x['type']=='missing_retained_boundary_chart_normal'}),'geometryGenerated':False,'elapsedSeconds':time.monotonic()-start,'anonymousGBSamples':mem,'inputs':pins}
assert report['fixed49OriginalBoundaryEdgesUnsplit'] and report['exactParameterLensAreaConserved'] and report['exactPerOriginal47ReferenceFaceAreaConserved'];save(E/'literal-final-checks.json',report);print(json.dumps({k:v for k,v in report.items() if k not in ['fixedBoundaryEdges','inputs']}),flush=True)
