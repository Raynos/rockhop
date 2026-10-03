/** Install current owner-proposed patches on actual merged runtime geometry. */
/* oxlint-disable eslint/no-undef -- serialized headless browser diagnostics. */
export async function installContactProposals(page, riderPatches, bikeSource) {
  return page.evaluate(async ({ riderPatches, bikeSource }) => {
    const d=window.__render.debug,T=d.THREE,rider=d.rider,bike=d.bike,meshes=rider.sleeveGeometry.map(i=>i.mesh);
    const digest=async payload=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(payload))),b=>b.toString(16).padStart(2,'0')).join('');
    const locator=(o,root)=>{const path=[];while(o!==root){if(!o.parent)throw new Error('Object outside owning root');path.unshift(o.parent.children.indexOf(o));o=o.parent;}return path;};
    const obsolete=[];for(const root of[rider.scene,bike.root])root.traverse(o=>{if(o.name.startsWith('agent3-proposed:')||o.name.startsWith('agent3-proposed-target:'))obsolete.push(o);});for(const o of obsolete)o.removeFromParent();
    const ancestors=[];const patchRows=[];
    for(const s of riderPatches.surfaces){
      const sources=[...rider.source.parser.associations].filter(([o,a])=>o.isSkinnedMesh&&a.meshes===s.source.mesh&&a.primitives===s.source.primitive);if(sources.length!==1)throw new Error('Ambiguous source patch primitive '+s.label);
      const src=sources[0][0],sp=src.geometry.attributes.position,si=src.geometry.index;const matches=[];
      for(const m of meshes){const mp=m.geometry.attributes.position,mi=m.geometry.index;
        for(let base=0;base+sp.count<=mp.count;base++){
          if(mp.getX(base)!==sp.getX(0)||mp.getY(base)!==sp.getY(0)||mp.getZ(base)!==sp.getZ(0))continue;
          if(Object.keys(src.geometry.attributes).some(k=>!m.geometry.attributes[k]))continue;
          let exact=true;for(const[k,a]of Object.entries(src.geometry.attributes)){const b=m.geometry.attributes[k];if(a.itemSize!==b.itemSize){exact=false;break;}for(let i=0;i<a.count&&exact;i++)for(let c=0;c<a.itemSize;c++)if(a.getComponent(i,c)!==b.getComponent(base+i,c)){exact=false;break;}}
          if(!exact)continue;
          for(let ib=0;ib+si.count<=mi.count;ib++){if(mi.getX(ib)!==si.getX(0)+base)continue;let indices=true;for(let i=0;i<si.count;i++)if(mi.getX(ib+i)!==si.getX(i)+base){indices=false;break;}if(indices&&ib%3===0)matches.push({mesh:m,vertexBase:base,triangleBase:ib/3});}
        }
      }if(matches.length!==1)throw new Error('Nonunique complete source/runtime segment '+s.label);
      const match=matches[0],m=match.mesh;
      if(JSON.stringify(m.skeleton.bones.map(b=>b.name))!==JSON.stringify(s.jointOrder.map(n=>n.replaceAll('.',''))))throw new Error('Patch skin order differs');
      for(const v of s.vertices)if(v.rawPositionM.some((x,c)=>x!==sp.getComponent(v.vertexID,c)))throw new Error('Owner patch source positions differ');
      for(const tr of s.triangles)for(let k=0;k<3;k++)if(si.getX(tr.triangleID*3+k)!==tr.vertexIDs[k])throw new Error('Owner patch source triangle differs');
      const triangles=s.triangles.map(tr=>tr.triangleID+match.triangleBase),vertices=s.vertices.map(v=>v.vertexID+match.vertexBase);
      const payload=JSON.stringify({positions:Array.from({length:m.geometry.attributes.position.count},(_,i)=>[m.geometry.attributes.position.getX(i),m.geometry.attributes.position.getY(i),m.geometry.attributes.position.getZ(i)]),indices:Array.from({length:m.geometry.index.count},(_,i)=>m.geometry.index.getX(i))});
      ancestors.push({label:s.label,source:s.source,runtimeMesh:m.name,runtimeChildPath:locator(m,rider.scene),runtimeGeometryPositionIndexSHA256:await digest(payload),vertexBase:match.vertexBase,triangleBase:match.triangleBase,sourceTriangleIDs:s.triangles.map(t=>t.triangleID),runtimeTriangleIDs:triangles,exactCompleteSourceAttributeAndIndexSegment:true,patchReviewed:false});
      const g=new T.BufferGeometry();for(const[k,a]of Object.entries(m.geometry.attributes))g.setAttribute(k,a);g.setIndex(triangles.flatMap(tr=>[0,1,2].map(c=>m.geometry.index.getX(tr*3+c))));
      g.morphAttributes=m.geometry.morphAttributes;g.morphTargetsRelative=m.geometry.morphTargetsRelative;
      const overlay=new T.SkinnedMesh(g,new T.MeshBasicMaterial({color:new T.Color(...s.color),wireframe:true,depthTest:false,transparent:true,opacity:.45}));overlay.name='agent3-proposed:'+s.label;overlay.bind(m.skeleton,m.bindMatrix);overlay.frustumCulled=false;overlay.renderOrder=9999;m.add(overlay);
      patchRows.push({source:s,mesh:m,triangles,vertices,overlay});
    }
    const targets={};const targetReceipts=[];
    for(const s of bikeSource.sources){const matches=bike.root.getObjectsByProperty('name',s.sourceNodeName).filter(o=>o.isMesh);if(matches.length!==1)throw new Error('Bike target ambiguity');const mesh=matches[0],p=mesh.geometry.attributes.position,idx=mesh.geometry.index;
      const payload=JSON.stringify({positions:Array.from({length:p.count},(_,i)=>[p.getX(i),p.getY(i),p.getZ(i)]),indices:Array.from({length:idx.count},(_,i)=>idx.getX(i))});if(await digest(payload)!==s.geometrySHA256)throw new Error('Current bike target geometry drift');
      const selections=s.sourceNodeName==='bodywork'?[['seat',[3],0xff55ff]]:s.sourceNodeName==='handlebar'?[['palm-L',[0],0x00ff77],['palm-R',[3],0x00ff77]]:[['sole-L',Array.from({length:11},(_,i)=>i),0x00ddff],['sole-R',Array.from({length:11},(_,i)=>i+12),0x00ddff]];
      for(const[key,parts,color]of selections){const triangles=s.components.filter(c=>parts.includes(c.component)).flatMap(c=>c.sourceTriangleOrdinals);
        const restFrame=new T.Matrix4().makeTranslation(...bikeSource.frameOriginFileFrameM.map(v=>-v)).multiply(new T.Matrix4().fromArray(s.sourceNodeMatrixWorld));
        const faces=triangles.map(ordinal=>{const ids=[0,1,2].map(c=>idx.getX(ordinal*3+c)),points=ids.map(i=>new T.Vector3(p.getX(i),p.getY(i),p.getZ(i)).applyMatrix4(restFrame)),normal=new T.Vector3().subVectors(points[1],points[0]).cross(new T.Vector3().subVectors(points[2],points[0])).normalize();return{ordinal,ids,restPoints:points,restNormal:normal};});
        const support=key==='seat'||key.startsWith('sole')?faces.filter(f=>f.restNormal.y>0):[];
        targets[key]={mesh,faces,support,restFrame};targetReceipts.push({key,mesh:mesh.name,childPath:locator(mesh,bike.root),assetSHA256:bikeSource.assetSHA256,sourceNode:s.nodeIndex,sourceMesh:s.sourceMeshIndex,sourcePrimitive:s.primitiveIndex,selectedShellTriangles:triangles,
          majorPartReview:'Parent root approved major part identities via bridge; detailed support subsets and rider masks remain unaccepted.',
          proposedUpwardSupportTriangles:support.map(f=>({ordinal:f.ordinal,restNormalBikeFrame:f.restNormal.toArray()})),closure:'unproved',sourceGeometrySHA256:s.geometrySHA256});
        const g=new T.BufferGeometry();g.setAttribute('position',p);g.setIndex(triangles.flatMap(tr=>[0,1,2].map(c=>idx.getX(tr*3+c))));const overlay=new T.Mesh(g,new T.MeshBasicMaterial({color,wireframe:true,depthTest:false,transparent:true,opacity:.45}));overlay.name='agent3-proposed-target:'+key;overlay.renderOrder=9999;mesh.add(overlay);
      }
    }
    const measure=()=>{
      const results=[],bikeInverse=bike.frame.matrixWorld.clone().invert();
      for(const patch of patchRows){const mesh=patch.mesh;mesh.skeleton.update();patch.overlay.morphTargetInfluences=mesh.morphTargetInfluences?.slice();
        const target=targets[patch.source.kind==='seat'?'seat':`${patch.source.kind}-${patch.source.side}`];if(!target)throw new Error('No corresponding target');
        const posed=new Map(),normalByVertex=new Map(),samples=[];
        for(const id of patch.vertices)posed.set(id,mesh.getVertexPosition(id,new T.Vector3()).applyMatrix4(mesh.matrixWorld));
        for(const ordinal of patch.triangles){const ids=[0,1,2].map(c=>mesh.geometry.index.getX(ordinal*3+c)),ps=ids.map(id=>posed.get(id));if(ps.some(p=>!p))throw new Error('Incomplete patch vertex coverage');const normal=new T.Vector3().subVectors(ps[1],ps[0]).cross(new T.Vector3().subVectors(ps[2],ps[0])).normalize();
          samples.push({point:ps[0].clone().add(ps[1]).add(ps[2]).multiplyScalar(1/3),normal,source:'triangle-centroid',ordinal});for(const id of ids)normalByVertex.set(id,(normalByVertex.get(id)??new T.Vector3()).add(normal));}
        for(const[id,point]of posed)samples.push({point,normal:normalByVertex.get(id).normalize(),source:'vertex',ordinal:id});
        const expectedTargetWorld=bike.frame.matrixWorld.clone().multiply(target.restFrame);const targetMatrixResidual=Math.max(...target.mesh.matrixWorld.elements.map((v,k)=>Math.abs(v-expectedTargetWorld.elements[k])));if(targetMatrixResidual>1e-9)throw new Error('Static target/bike-frame correspondence changed');
        const faces=target.faces.map(f=>{const pts=f.ids.map(id=>{const p=target.mesh.geometry.attributes.position;return new T.Vector3(p.getX(id),p.getY(id),p.getZ(id)).applyMatrix4(target.mesh.matrixWorld);});const normal=new T.Vector3().subVectors(pts[1],pts[0]).cross(new T.Vector3().subVectors(pts[2],pts[0])).normalize();return{...f,triangle:new T.Triangle(...pts),normal};});
        let minimumUnsignedGapM=Infinity,minimumLocalFaceSidedDistanceM=Infinity,maximumLocalFaceSidedDistanceM=-Infinity,witness=null,supportSamples=0,minSupportGapM=Infinity,maxSupportGapM=-Infinity,supportWitness=null;const closest=new T.Vector3();
        for(const sample of samples){let nearest=null,gap=Infinity;for(const face of faces){face.triangle.closestPointToPoint(sample.point,closest);const distance=closest.distanceTo(sample.point);if(distance<gap){gap=distance;nearest={face,point:closest.clone()};}}
          const sided=sample.point.clone().sub(nearest.point).dot(nearest.face.normal);minimumLocalFaceSidedDistanceM=Math.min(minimumLocalFaceSidedDistanceM,sided);maximumLocalFaceSidedDistanceM=Math.max(maximumLocalFaceSidedDistanceM,sided);
          if(gap<minimumUnsignedGapM){minimumUnsignedGapM=gap;witness={sampleSource:sample.source,sampleOrdinal:sample.ordinal,world:sample.point.toArray(),targetWorld:nearest.point.toArray(),targetTriangle:nearest.face.ordinal,opposingNormalAngleDeg:Math.acos(Math.max(-1,Math.min(1,-sample.normal.dot(nearest.face.normal))))*180/Math.PI};}
          if(target.support.length){const p=sample.point.clone().applyMatrix4(bikeInverse);let top=null;
            for(const f of target.support){const[a,b,c]=f.restPoints,den=(b.z-c.z)*(a.x-c.x)+(c.x-b.x)*(a.z-c.z);if(Math.abs(den)<1e-12)continue;const u=((b.z-c.z)*(p.x-c.x)+(c.x-b.x)*(p.z-c.z))/den,v=((c.z-a.z)*(p.x-c.x)+(a.x-c.x)*(p.z-c.z))/den,w=1-u-v;if(u<0||v<0||w<0)continue;const y=u*a.y+v*b.y+w*c.y;if(!top||y>top.y)top={y,face:f,barycentric:[u,v,w]};}
            if(top){const signed=p.y-top.y;supportSamples++;minSupportGapM=Math.min(minSupportGapM,signed);maxSupportGapM=Math.max(maxSupportGapM,signed);if(!supportWitness||Math.abs(signed)<Math.abs(supportWitness.signedBikeUpGapM))supportWitness={signedBikeUpGapM:signed,sampleBikeFrame:p.toArray(),targetBikeFrame:[p.x,top.y,p.z],targetTriangle:top.face.ordinal,targetRestNormal:top.face.restNormal.toArray(),barycentric:top.barycentric};}
          }
        }
        results.push({label:patch.source.label,status:'numerically-measured-unaccepted-proposal',sampleCount:samples.length,targetMatrixResidual,patchTriangles:patch.triangles.length,minimumUnsignedGapM,minimumLocalFaceSidedDistanceM,maximumLocalFaceSidedDistanceM,witness,
          supportProjectionSamples:supportSamples,supportProjectionFraction:supportSamples/samples.length,minSignedBikeUpSupportGapM:supportSamples?minSupportGapM:null,maxSignedBikeUpSupportGapM:supportSamples?maxSupportGapM:null,supportWitness,
          limitations:'Vertex+centroid sampling only. Local face-sided distance is not closed-volume penetration. Support uses upward rest faces and exact same-X/Z bike-up projection; nearest underside/side/nose clearance never becomes support. No threshold or pass flag. Automatic rider masks await parent review.'});
      }return results;
    };
    window.__agent3ProposalContacts={measure};
    return{candidateSHA256:riderPatches.candidateGLBSHA256,ancestors,targetReceipts,patchReview:'pending parent played review',supportRule:'Rest bike-frame normal.y > 0, same X/Z projection into upward face, highest projected top face; signed gap along bike-local +Y. Selected shell is separate unsigned/local-face clearance. Numerical projected degeneracies below1e-12 area skipped.',sampling:'Every selected triangle centroid plus each unique selected vertex; finite samples, no continuous/intersection certificate.'};
  }, {riderPatches,bikeSource});
}
