"""Generate a review-only integration patch against the pinned accepted C1 tree.

Only writes runtime.patch in this prototype directory. Never edits live src.
"""
from pathlib import Path
from difflib import unified_diff
import hashlib

ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
PINNED={
    'src/render/world/biomeKit.ts':'1aa86cace1a5b8f80da816c47e6d941993d7529946280b8b2da6559dfd4e21aa',
    'src/render/world/zones/coastHarbor.ts':'09d5c076a43b751ca938aa7ec75664ba7aded4fa7701c8e284c845adc4da248b',
    'src/render/world/zones/coastHarborSite.ts':'5311f70c80b5d2dc23bc1adea2c65af24527d1f0190dc9cd53199dcc19ede74f',
    'src/render/index.ts':'f876e45b0afaa45856b837a8fdb2e534d93e126a7e64a6be2824e9a2ffa1fd21',
}

def replace_one(source, before, after, path):
    if source.count(before)!=1:raise RuntimeError(f'{path}: expected one exact anchor, found {source.count(before)}: {before[:100]}')
    return source.replace(before,after)

def modify(path, source):
    if path.endswith('/coastHarbor.ts'):
        source=replace_one(source,"  'loading-pier', 'open-warehouse', 'logistics-yard', 'dock-station'] as const;",
          "  'loading-pier', 'open-warehouse', 'brick-repair-shed', 'sawtooth-maintenance-hall', 'logistics-yard', 'dock-station'] as const;",path)
        source=replace_one(source,"export const COAST_HARBOR_MAPS = ['coast-albedo.phone.webp', 'coast-normal.phone.webp', 'coast-arm.phone.webp'] as const;",
          "export const COAST_HARBOR_MAPS = ['coast-albedo.phone.webp', 'coast-normal.phone.webp', 'coast-arm.phone.webp',\n  'frontage-albedo.phone.webp', 'frontage-normal.phone.webp', 'frontage-arm.phone.webp'] as const;",path)
        source=replace_one(source,"const PREFIX = 'models/course-kits/coast-harbor/';","const PREFIX = 'models/course-kits/coast-frontage/';",path)
        source=replace_one(source,"  for (const [x,scale] of [[32,.64],[109,.68],[282,.62],[370,.68],[450,.60]] as const)\n    add('open-warehouse',x,-9.8,scale);",
          "  for (const [x,scale,variant] of [[32,.64,'brick-repair-shed'],[109,.68,'sawtooth-maintenance-hall'],\n    [282,.62,'open-warehouse'],[370,.68,'brick-repair-shed'],[450,.60,'sawtooth-maintenance-hall']] as const)\n    add(variant,x,-9.8,scale);",path)
        source=replace_one(source,"const logical = PREFIX + (options.detail === 'full' ? 'coast-harbor.glb' : 'coast-harbor-lod.glb');",
          "const logical = PREFIX + (options.detail === 'full' ? 'coast-frontage.glb' : 'coast-frontage-lod.glb');",path)
        source=replace_one(source,"if (material.name === 'coast manufactured PBR atlas' && (!material.map || !material.normalMap || !material.roughnessMap || !material.metalnessMap))",
          "if ((material.name === 'coast manufactured PBR atlas' || material.name === 'frontage brick/steel PBR atlas')\n          && (!material.map || !material.normalMap || !material.roughnessMap || !material.metalnessMap))",path)
        return source
    if path.endswith('/coastHarborSite.ts'):
        source=replace_one(source,"  'open-warehouse': [-14.15, 14.15, -6.6, 7.56],",
          "  'open-warehouse': [-14.15, 14.15, -6.6, 7.56],\n  'brick-repair-shed': [-14.15, 14.15, -6.6, 7.56],\n  'sawtooth-maintenance-hall': [-14.15, 14.15, -6.6, 7.56],",path)
        return source
    if path=='src/render/index.ts':
        return replace_one(source,"const kit = buildBiomeKit(track, this.biome, this.lib, art, this.tier, !this.trackBackdrop);",
          "const kit = buildBiomeKit(track, this.biome, this.lib, art, this.tier, !this.trackBackdrop, ribbons.group);",path)
    if path.endswith('/biomeKit.ts'):
        source=replace_one(source,"import { buildCoastWater } from './zones/coastWater';",
          "import { buildCoastWater } from './zones/coastWater';\nimport { coastGroundSurface, loadCoastGroundMaterials, type CoastGroundMaterialDelivery } from './zones/coastGroundMaterials';",path)
        source=replace_one(source,"detail: WorldDetail = 'high', authoredCourse = false): BiomeKit {",
          "detail: WorldDetail = 'high', authoredCourse = false, rideSurfaceGroup: THREE.Group | null = null): BiomeKit {",path)
        old="""        void harbor.ready.then(() => {
          if (harbor.root.children.length) {
            harborFallback.visible = false;
            if (originalCoastPlate) originalCoastPlate.visible = false;
            if (originalSea) originalSea.visible = false;
          }
        });
        courseAssets = combineCourseAssets(tug,harbor); group.add(courseAssets.root);"""
        new="""        void harbor.ready.then(() => {
          if (harbor.root.children.length) {
            harborFallback.visible = false;
            if (originalCoastPlate) originalCoastPlate.visible = false;
            if (originalSea) originalSea.visible = false;
          }
        });
        // The deck top/face are in the renderer's ribbons.group, not zk.meshes.
        // Capture only C1 ground; edge stripe, obstacles, pads and sea stay untouched.
        const groundTargets = [
          ...(rideSurfaceGroup?.children ?? []), ...zk.meshes,
        ].filter((object): object is THREE.Mesh => object instanceof THREE.Mesh && coastGroundSurface(object.name) !== null);
        const borrowed = new Map<THREE.Mesh, THREE.Material | THREE.Material[]>();
        const restoreBorrowed = (): void => {
          for (const [mesh, material] of borrowed) mesh.material = material;
          borrowed.clear();
        };
        let groundDelivery: CoastGroundMaterialDelivery | undefined;
        let groundActive = true;
        const ground = mountCourseAssets(loadCoastGroundMaterials({
          completeMaterial: material => { lib.complete(material); },
        }).then(asset => { groundDelivery = asset; return asset; }));
        const combined = combineCourseAssets(tug, harbor, ground);
        void combined.ready.then(() => {
          // cancel() runs before a world is removed. A late response cannot mutate
          // another course, and a missing required map leaves borrowed art intact.
          if (!groundActive || !ground.root.children.length || !harbor.root.children.length ||
              !combined.root.children.length || !groundDelivery) return;
          const typed = groundTargets.map(mesh => ({mesh, surface:coastGroundSurface(mesh.name)}));
          if (!(['top','wall','terrain'] as const).every(surface => typed.some(target => target.surface === surface))) return;
          try {
            for (const {mesh,surface} of typed) {
              if (!surface) continue;
              borrowed.set(mesh,mesh.material);
              mesh.material = groundDelivery.materials[surface];
            }
          } catch (error) { restoreBorrowed(); console.warn('[render] Coast ground swap failed',error); }
        });
        courseAssets = {
          root: combined.root, ready: combined.ready,
          get textureBytes() { return combined.textureBytes; },
          cancel() { groundActive = false; restoreBorrowed(); combined.cancel(); },
          dispose() { groundActive = false; restoreBorrowed(); combined.dispose(); },
        };
        group.add(courseAssets.root);"""
        return replace_one(source,old,new,path)
    raise RuntimeError(path)

parts=[]
for path,expected in PINNED.items():
    current=(ROOT/path).read_bytes();digest=hashlib.sha256(current).hexdigest()
    if digest!=expected:raise RuntimeError(f'{path}: source drift {digest}; rebase explicitly before capture')
    before=current.decode();after=modify(path,before)
    # Zero context avoids carrying legacy whitespace-only context into this
    # prototype patch; all actual changed lines remain byte-identical.
    diff=''.join(unified_diff(before.splitlines(keepends=True),after.splitlines(keepends=True),
      fromfile='a/'+path,tofile='b/'+path,n=0))
    parts.append('diff --git a/'+path+' b/'+path+'\n'+diff)
(OUT/'runtime.patch').write_text(''.join(parts))
print('runtime.patch generated from pinned accepted C1 sources; no live source changed')
