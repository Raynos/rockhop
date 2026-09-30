/** Immutable collider/placement guide for offline Coast art, never a game edit.
 * Usage: pnpm exec tsx prototypes/coast-family-v1/extract-guides.mts
 */
import fs from 'node:fs';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { compileTrack, getTrack, hashColliders } from '../../src/tracks/index';

const root = path.resolve(import.meta.dirname,'../..');
const out = path.join(import.meta.dirname,'collider-guides.json');
const sha = (file: string): string => createHash('sha256').update(fs.readFileSync(path.join(root,file))).digest('hex');
const ids = ['c1-low-tide','c2-crane-hop','c3-hull-breach'] as const;
const courses = ids.map(id => {
  const def = getTrack(id);
  if (!def) throw new Error(`Missing ${id}`);
  const t = compileTrack(def);
  const floor = Math.min(...def.profile.map(point => point.y))-0.42;
  const seaY = floor-2.4;
  return {
    id, seed:def.seed, colliderHash:hashColliders(t.colliders),
    xEnd:def.profile.at(-1)!.x, seaY,
    profile:def.profile,
    checkpoints:def.checkpoints,
    placed:t.placed.map(p => ({kind:p.kind,pos:p.pos,colliderIds:p.colliderIds,
      colliders:t.colliders.filter(c => p.colliderIds.includes(c.id))})),
  };
});
const data = {
  status:'offline art guides; collision/physics unchanged',
  sourceSHA256:{
    'src/tracks/rockhop/coast.ts':sha('src/tracks/rockhop/coast.ts'),
    'src/tracks/compile.ts':sha('src/tracks/compile.ts'),
  },
  courses,
};
fs.writeFileSync(out,JSON.stringify(data,null,2)+'\n');
console.log(`${out}: ${courses.map(c=>`${c.id} ${c.colliderHash}`).join('; ')}`);
