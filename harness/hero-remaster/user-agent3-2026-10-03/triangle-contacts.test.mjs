import test from 'node:test';
import assert from 'node:assert/strict';
import { triangleContact } from './triangle-contacts.mjs';
await test('independent contact predicate separates planes and coplanar faces',()=>{
  const a=[[0,0,0],[1,0,0],[0,1,0]];
  assert(triangleContact(a,[[.2,.2,-1],[.2,.2,1],[.8,.2,0]]));
  assert(!triangleContact(a,[[0,0,1],[1,0,1],[0,1,1]]));
  assert(!triangleContact(a,[[1,1,0],[2,1,0],[1,2,0]]));
  assert(triangleContact(a,[[.1,.1,0],[.2,.1,0],[.1,.2,0]]));
  assert.throws(()=>triangleContact(a,[[0,0,0],[0,0,0],[0,0,0]]));
});
