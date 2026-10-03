import test from 'node:test';
import assert from 'node:assert/strict';
import { makeClosedSolidQuery } from './closed-solid-query.mjs';
await test('closed tetrahedron classifies interior, concave-bounds exterior and boundary',()=>{
 const vertices=[[0,0,0],[1,0,0],[0,1,0],[0,0,1]],faces=[[0,2,1],[0,1,3],[0,3,2],[1,2,3]];
 const query=makeClosedSolidQuery(vertices,faces,[{component:0,triangles:[0,1,2,3],bounds:{min:[0,0,0],max:[1,1,1]}}]);
 const inside=query([.1,.1,.1]);assert(inside.inside);assert(Math.abs(inside.hits[0].winding-1)<1e-14);assert(Math.abs(inside.hits[0].penetrationM-.1)<1e-14);
 assert(!query([.8,.8,.8]).inside);assert(!query([2,0,0]).inside);
 assert(query([0,0,0]).boundary);assert(!query([0,0,0]).inside);
 assert(query([1/3,1/3,1/3]).boundary);assert(query([.01,.01,.01]).inside);
});
