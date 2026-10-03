import assert from 'node:assert/strict';
import test from 'node:test';
import { meshContacts } from './triangle-contacts.mjs';
import { triangleRows, bvhContacts } from './triangle-bvh.mjs';

await test('conservative broadphase retains crossing, coplanar, epsilon and adjacency cases', () => {
  const vertices = [[0,0,0],[1,0,0],[0,1,0], [.2,.2,-1],[.2,.2,1],[.8,.2,0],
    [.1,.1,0],[.3,.1,0],[.1,.3,0], [1+5e-10,0,0],[2,0,0],[1+5e-10,1,0],
    [3,0,0],[4,0,0],[3,1,0]];
  const faces = [[0,1,2],[3,4,5],[6,7,8],[9,10,11],[12,13,14]];
  const rows = triangleRows(vertices, faces), result = bvhContacts(rows, rows, true, true);
  assert.equal(result.pairs, meshContacts(vertices, faces, vertices, faces, true).pairs);
  assert(result.pairs >= 4);
  assert(result.witnesses.some(w => w.triangleA === 0 && w.triangleB === 3), 'epsilon boundary cannot be culled');
  const aliases = triangleRows([...vertices, ...vertices.slice(0,3)], [[0,1,2],[15,16,17]], [...vertices.map((_,i)=>i),0,1,2]);
  assert.equal(bvhContacts(aliases, aliases, true, true).pairs, 0, 'UV rows sharing native IDs are adjacent');
});

await test('broadphase agrees with full finite SAT across a deterministic dispersed population', () => {
  let state = 0x5eed;
  const random = () => { state = (Math.imul(state, 1664525) + 1013904223) >>> 0; return state / 2**32; };
  const vertices = Array.from({ length: 240 }, () => [random()*2-1, random()*2-1, random()*2-1]);
  const faces = Array.from({ length: 80 }, (_,i) => [i*3,i*3+1,i*3+2]);
  const rows = triangleRows(vertices, faces);
  assert.equal(bvhContacts(rows, rows, true, true).pairs, meshContacts(vertices, faces, vertices, faces, true).pairs);
});
