/** Exact current source09 mesh rows sampled from the actual engine skeleton. */
export function makeBootSurfaces(debug, native) {
  const T = debug.THREE, meshes = [];
  debug.rider.scene.traverse(o => { if (o.isSkinnedMesh) meshes.push(o); });
  const specs = [['body', 9981, 18016], ['upper', 1158, 1898], ['sole', 466, 328]];
  const parts = specs.map(([name, rows, triangles]) => {
    const matches = meshes.filter(m => m.geometry.attributes.position.count === rows && m.geometry.index.count === triangles * 3);
    if (matches.length !== 1) throw new Error('Actual mesh ambiguous: ' + name);
    const mesh = matches[0], faces = Array.from({ length: triangles }, (_, i) => [0, 1, 2].map(k => mesh.geometry.index.getX(i * 3 + k)));
    const ambiguousRows = [];
    const nativeIDs = name === 'body' ? null : Array.from({ length: rows }, (_, i) => {
      const p = new T.Vector3().fromBufferAttribute(mesh.geometry.attributes.position, i), xyz = [p.x - .65, -p.z, p.y];
      const found = native.vertices.filter(v => Math.hypot(...xyz.map((x, k) => x - v.restNativeM[k])) < 2e-6);
      if (found.length === 1) return found[0].nativeVertexID;
      const weights = {};
      for (let k=0;k<4;k++) { const w=mesh.geometry.attributes.skinWeight.getComponent(i,k); if(w>0)weights[mesh.skeleton.bones[mesh.geometry.attributes.skinIndex.getComponent(i,k)].name]=w; }
      const errors = found.map(v => { const nativeWeights=Object.fromEntries(Object.entries(v.normalizedNativeWeights).map(([n,w])=>[n.replaceAll('.',''),w]));
        return { nativeID:v.nativeVertexID,error:Math.max(...[...new Set([...Object.keys(weights),...Object.keys(nativeWeights)])].map(n=>Math.abs((weights[n]??0)-(nativeWeights[n]??0)))) }; });
      const qualified=errors.filter(v=>v.error<1e-7);
      if(qualified.length!==1)throw new Error('Current boot row remains ambiguous after actual weight comparison');
      ambiguousRows.push({row:i,candidates:errors,selectedNativeID:qualified[0].nativeID,qualification:'Rest position <2µm plus actual normalized weight field <1e-7; all native triangle identities verified separately.'});
      return qualified[0].nativeID;
    });
    const materialSlot=name==='upper'?0:1, key=ids=>ids.slice().sort((a,b)=>a-b).join(',');
    if(nativeIDs)for(const face of faces){const ids=face.map(i=>nativeIDs[i]);if(native.triangles.filter(t=>t.materialSlot===materialSlot&&key(t.nativeVertexIDs)===key(ids)).length!==1)throw new Error('Exported boot triangle lacks unique current native identity');}
    return { name, mesh, faces, nativeIDs, rows, triangles, ambiguousRows };
  });
  const contract = parts.map(({ name, mesh, faces, nativeIDs, rows, triangles, ambiguousRows }) => ({ name, meshName: mesh.name, rows, triangles, faces, nativeIDs, ambiguousRows,
    jointOrder: mesh.skeleton.bones.map(b => b.name), bindMatrix: mesh.bindMatrix.toArray(), inverseBinds: mesh.skeleton.boneInverses.map(m => m.toArray()) }));
  return { contract, sample() {
    debug.rider.scene.updateMatrixWorld(true);
    return parts.flatMap(({ mesh, rows }) => {
      mesh.skeleton.update();
      return Array.from({ length: rows }, (_, i) => mesh.getVertexPosition(i, new T.Vector3()).applyMatrix4(mesh.matrixWorld).toArray()).flat();
    });
  } };
}
