"""Exact-binary polynomial bracket and selected non-cap chord witnesses."""
import hashlib,json
from fractions import Fraction
from pathlib import Path
import numpy as np
root=Path(__file__).resolve().parents[6];ev=root/'docs/evidence/hero-remaster/anatomical-foundation-2026-10-03/user-agent1';out=ev/'neck-interface103';qa=root/'docs/evidence/hero-remaster/user-agent3-qa-2026-10-03';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
events=json.loads((out/'chord-events.json').read_text());data=np.load(out/'path-geometry-and-candidates.npz');P0=data['P0'];D=data['P1']-P0;mapping=data['rawPhysicalMap'];NB=9219
field=ev/'neck-interface102/candidate-fields-ancestry-corrected.npz';f=dict(np.load(field));r=np.load(ev/'neck-interface96/ordered-boundaries.npz');scope=json.loads((qa/'body59/proposal.json').read_text())['preciseInitialAuthoringMargin'];math=np.load(ev/'neck-interface102/solve-witnesses.npz');dof=np.zeros(len(P0),dtype=int);np.add.at(dof,math['freePhysicalNodes'][math['variableOwner']],1)
text=(Path(__file__).with_name('locate_neck_chord_events.py')).read_text();helpers=dict(np=np,upper=1.)
exec(compile(text[text.index('def proper('):text.index('start=time.monotonic()')],'frozen-event-helpers','exec'),helpers)
parts={'body':mapping[:NB],'head':mapping[NB:]};references={'body':data['bodyReferenceTriangles'],'head':data['headReferenceTriangles']};current={'body':f['bodyTriangles'],'head':f['headTriangles']}
first=events['earliestNumericEntry'];a,b='body','head';i,j=first['triangleIDs'];nodes=[parts[a][references[a][i]],parts[b][references[b][j]]];ap,ad,bp,bd=P0[nodes[0]],D[nodes[0]],P0[nodes[1]],D[nodes[1]];alpha=first['onsetRootAlpha'];feature_rows=[]
for source,target,sd,td,label in [(ap,bp,ad,bd,'bodyVertex-headFace'),(bp,ap,bd,ad,'headVertex-bodyFace')]:
 for vertex in range(3):
  vectors=[(source[vertex]-target[0],sd[vertex]-td[0]),(target[1]-target[0],td[1]-td[0]),(target[2]-target[0],td[2]-td[0])];c=helpers['coefficients'](*vectors);roots,zero=helpers['roots'](c)
  if any(abs(t-alpha)<1e-10 for t in roots):feature_rows.append({'feature':label,'vertexInFace':vertex,'vectors':vectors,'floatCoefficients':c.tolist()})
for x,y in [(0,1),(1,2),(2,0)]:
 for u,v in [(0,1),(1,2),(2,0)]:
  vectors=[(ap[y]-ap[x],ad[y]-ad[x]),(bp[v]-bp[u],bd[v]-bd[u]),(bp[u]-ap[x],bd[u]-ad[x])];c=helpers['coefficients'](*vectors);roots,zero=helpers['roots'](c)
  if any(abs(t-alpha)<1e-10 for t in roots):feature_rows.append({'feature':'bodyEdge-headEdge','edges':[[x,y],[u,v]],'vectors':vectors,'floatCoefficients':c.tolist()})
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def cross(a,b):return [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]
def det(a,b,c):return dot(a,cross(b,c))
def exact(vectors):
 (a,ad),(b,bd),(c,cd)=[tuple([Fraction.from_float(float(x)) for x in row] for row in vector) for vector in vectors]
 return [det(a,b,c),det(ad,b,c)+det(a,bd,c)+det(a,b,cd),det(ad,bd,c)+det(ad,b,cd)+det(a,bd,cd),det(ad,bd,cd)]
lo=Fraction.from_float(alpha-2e-12);hi=Fraction.from_float(alpha+2e-12);brackets=[]
for feature in feature_rows:
 c=exact(feature.pop('vectors'));lv=sum(value*lo**degree for degree,value in enumerate(c));hv=sum(value*hi**degree for degree,value in enumerate(c));brackets.append({**feature,'exactBinaryRationalCoefficients':[str(x) for x in c],'bracketAlpha':[float(lo),float(hi)],'exactPolynomialSigns':[-1 if lv<0 else 1 if lv>0 else 0,-1 if hv<0 else 1 if hv>0 else 0],'oppositeSigns':lv*hv<0})
assert any(row['oppositeSigns'] for row in brackets)
selected=[]
for kind,which,indices in [('headSelf',['head','head'],[4,94]),('bodyHead',['body','head'],[208,22652])]:
 nodes=[parts[key][current[key][index]] for key,index in zip(which,indices)];A,AD,B,BD=P0[nodes[0]],D[nodes[0]],P0[nodes[1]],D[nodes[1]];roots,zero,unresolved=helpers['pair_events'](A,AD,B,BD);entry=None
 for left,right in zip(roots[:-1],roots[1:]):
  mid=(left+right)/2
  if helpers['proper'](A+mid*AD,B+mid*BD):entry={'onsetRootAlpha':left,'nextEventAlpha':right,'properWitnessAlpha':mid};break
 assert entry and not helpers['proper'](A,B)
 selected.append({'kind':kind,'finalNativeTriangleIDs':indices,'fixedFinalTemplateEqualsReferenceAtTheseRows':[bool(np.array_equal(current[k][idx],references[k][idx])) for k,idx in zip(which,indices)],'nativeVerticesByFace':[current[k][idx].tolist() for k,idx in zip(which,indices)],'sourcePolygonIDs':[int(f[k+'TriangleSourcePolygonIDs'][idx]) for k,idx in zip(which,indices)],'tangentDOFByCorner':[dof[node].tolist() for node in nodes],'startingProperCrossing':False,**entry,'persistentFeatureCount':zero,'alwaysCollinearFeature':unresolved})
# Exact IDs around the protected decoded-normal discrepancy.
probes=json.loads((out/'path-samples.json').read_text())['protectedNormalProbes'];normal=next(row for row in probes if row['part']=='head' and row['alpha']==1e-6)['witness'];vertex=normal['nativeVertexID'];alias=r['headPositionAlias'];members=np.flatnonzero(alias==alias[vertex]);allowed=set(scope['headInitialBoundaryLedNativeVertexIDs']);normal['exactPositionAliasNativeIDs']=members.tolist();normal['aliasMembersOutsideAuthoringScope']=[int(v) for v in members if v not in allowed];normal['aliasMembersInsideAuthoringScope']=[int(v) for v in members if v in allowed];normal['polygonVertexDisplacementsM']=[D[parts['head'][v]].tolist() for v in normal['nativePolygonVertexIDs']];normal['polygonVertexTangentDOF']=[int(dof[parts['head'][v]]) for v in normal['nativePolygonVertexIDs']]
report={'status':'EXACT_SELECTED_CHORD_CONTACT_ROOT_BRACKET_AND_DECODED_NORMAL_CONFLICT','recipeSHA256':sha(__file__),'chordEventsSHA256':sha(out/'chord-events.json'),'selectedEarliestNumericEntry':first,'selectedRootExactBinaryBracket':brackets,'properAtAlphaRootMinus1e_6':helpers['proper'](ap+(alpha-1e-6)*ad,bp+(alpha-1e-6)*bd),'properAtAlphaRootPlus1e_6':helpers['proper'](ap+(alpha+1e-6)*ad,bp+(alpha+1e-6)*bd),'selectedNonCapDOFExamples':selected,'protectedNormalDirectionConflict':normal,'limits':['Exact rational sign change brackets the selected contact polynomial root only; allother event roots/globalordering were computed numerically. No certified global first or actual solver chronology is claimed.','Normal conflict is for the archived displacement chord, not a proof the entire admitted region lacks any normal-preserving path.','No candidate/fitting/skin solve, source save, extra path choice, scope expansion, rendering/capture/normal edit. AllM0-M5open.']}
assert report['properAtAlphaRootPlus1e_6'] and not report['properAtAlphaRootMinus1e_6']
(out/'exact-path-witnesses.json').write_text(json.dumps(report,indent=2)+'\n');print('SELECTED_NONCAP',selected);print('NORMAL_CONFLICT',normal)
