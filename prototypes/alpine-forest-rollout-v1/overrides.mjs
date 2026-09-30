/** One private forest hook. Current A1 material/forest hooks remain byte-identical. */
export function overrides(files) {
  const key='src/render/world/biomeKit.ts';
  let source=files[key];
  const anchor="import { a1ForestApplicable, loadA1Forest, removeA1ForestPlaceholders } from './zones/a1Forest';";
  const end='      meshes.push(...zk.meshes);';
  if(source.split(anchor).length!==2||source.split(end).length!==2)throw new Error('Current integration anchors changed');
  source=source.replace(anchor,anchor+"\nimport { alpineForestApplicable, planAlpineForest, removeAlpineForestPlaceholders, loadAlpineForest } from './zones/alpineForest';");
  source=source.replace(end,"      if (authoredCourse && alpineForestApplicable(track)) {\n        let prepared: { plan: ReturnType<typeof planAlpineForest>; originals: PropBatch[] } | undefined;\n        try {\n          const forestPlan = planAlpineForest(track, zk.batches);\n          const removed = removeAlpineForestPlaceholders(track, zk.batches);\n          prepared = { plan: forestPlan, originals: removed.originals };\n        } catch (error) { console.warn('[render] Alpine forest source validation failed; retaining originals', error); }\n        if (prepared) {\n          const fallback = new THREE.Group(); fallback.name = 'alpine-original-forest-fallback';\n          fallback.add(...buildBatches(prepared.originals).objects); group.add(fallback);\n          const owner = mountCourseAssets(loadAlpineForest(prepared.plan, {\n            completeMaterial: material => { lib.complete(material); },\n          }).then(asset => {\n            asset.root.traverse(object => {\n              if (!(object as THREE.Mesh).isMesh) return;\n              object.name = `props:${object.name}`;\n              object.userData['castHigh'] = object.castShadow;\n              object.userData['receiveHigh'] = object.receiveShadow;\n            }); return asset;\n          }));\n          void owner.ready.then(() => { if (owner.root.children.length) fallback.visible = false; });\n          courseAssets = owner; group.add(owner.root);\n        }\n      }\n"+end);
  return {[key]:source};
}
