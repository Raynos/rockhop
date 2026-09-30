import { readFileSync } from 'node:fs';
import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { MeshoptDecoder } from 'three/examples/jsm/libs/meshopt_decoder.module.js';
import { afterEach, describe, expect, it, vi } from 'vitest';
vi.mock('../../hero/urls', () => ({ modelAssetUrl: (path: string) => path }));
import { compileTrack } from '../../../tracks/compile';
import { S1, S2, S3 } from '../../../tracks/rockhop/snowline';
import { PropBatch } from '../props';
import { loadSnowlineStandard, snapshotSnowlineAnchors, snowContactFaceGeometry } from './snowlineStandard';

async function asset(lod = false) {
  const file = new URL(`../../../../harness/fixtures/snowline-standard/snowline-standard${lod ? '-lod' : ''}-packed.glb`, import.meta.url);
  const bytes = readFileSync(file);
  const jsonLength=bytes.readUInt32LE(12);
  const doc=JSON.parse(bytes.subarray(20,20+jsonLength).toString());
  delete doc.images;delete doc.textures;delete doc.samplers;
  for(const m of doc.materials??[]){
    delete m.normalTexture;delete m.occlusionTexture;delete m.emissiveTexture;
    if(m.pbrMetallicRoughness){delete m.pbrMetallicRoughness.baseColorTexture;delete m.pbrMetallicRoughness.metallicRoughnessTexture;}
  }
  const json=Buffer.from(JSON.stringify(doc));
  const pad=Buffer.alloc((4-json.length%4)%4,32);
  const bin=bytes.subarray(20+jsonLength);
  const rebuilt=Buffer.alloc(20+json.length+pad.length+bin.length);
  rebuilt.writeUInt32LE(0x46546c67,0);rebuilt.writeUInt32LE(2,4);rebuilt.writeUInt32LE(rebuilt.length,8);
  rebuilt.writeUInt32LE(json.length+pad.length,12);rebuilt.writeUInt32LE(0x4e4f534a,16);
  json.copy(rebuilt,20);pad.copy(rebuilt,20+json.length);bin.copy(rebuilt,20+json.length+pad.length);
  return new GLTFLoader().setMeshoptDecoder(MeshoptDecoder)
    .parseAsync(rebuilt.buffer.slice(rebuilt.byteOffset, rebuilt.byteOffset + rebuilt.byteLength), '');
}

afterEach(() => vi.restoreAllMocks());
describe('Snowline Standard isolated candidate', () => {
  it('clones legacy anchors and does not advance their batch state', () => {
    const b = new PropBatch('lifttower', new THREE.BoxGeometry(1,1,1), new THREE.MeshStandardMaterial());
    b.add(34, -1, -62);
    const anchors=snapshotSnowlineAnchors([b]);
    expect(anchors.lifttower).toHaveLength(1);
    expect(anchors.icewall0).toHaveLength(0);
    b.items[0]!.m.elements[12]=999;
    expect(anchors.lifttower[0]!.elements[12]).toBe(34);
    expect(b.count).toBe(1);
  });

  it.each([S1,S2,S3])('keeps carved foreground faces below contact and removes gap spans: $id', def => {
    const track=compileTrack(def);
    const face=snowContactFaceGeometry(track,0,Math.min(track.def.finishX,180));
    const p=face.getAttribute('position');
    expect(p.count).toBeGreaterThan(50);
    const gaps=track.placed.filter(o=>o.kind==='gap').map(o=>({a:o.pos.x,b:o.pos.x+Number(o.params.width)}));
    for(let i=0;i<p.count;i++) {
      const x=p.getX(i), y=p.getY(i);
      const profile=track.def.profile;
      let k=0;while(k<profile.length-2 && profile[k+1]!.x<x)k++;
      const a=profile[k]!,b=profile[k+1]!;
      const contact=a.y+(b.y-a.y)*Math.max(0,Math.min(1,(x-a.x)/(b.x-a.x)));
      expect(y).toBeLessThanOrEqual(contact-.10);
      expect(gaps.some(g=>x>g.a+.08 && x<g.b-.08)).toBe(false);
    }
    face.dispose();
  });

  it('decodes full and LOD through runtime path, mounts named instances, and disposes once', async () => {
    const full=await asset();
    const lod=await asset(true);
    const bitmap={width:16,height:16,close:vi.fn()};
    const normalBitmap={width:8,height:8,close:vi.fn()};
    const wall=full.scene.getObjectByName('snowlinegorge-wall') as THREE.Mesh;
    (wall.material as THREE.MeshStandardMaterial).map=new THREE.Texture(bitmap);
    (wall.material as THREE.MeshStandardMaterial).normalMap=new THREE.Texture(normalBitmap);
    vi.spyOn(GLTFLoader.prototype,'loadAsync').mockImplementation(async url=>url.includes('-lod')?lod:full);
    const track=compileTrack(S2);
    const old=new THREE.Matrix4().makeTranslation(92,-12,-52);
    old.scale(new THREE.Vector3(11,12,1));
    const anchors={icewall0:[old],icewall1:[],lifttower:[new THREE.Matrix4().makeTranslation(110,-1,-72)],
      liftchair:[],snowcat:[]};
    const lib={complete:()=>{}} as never;
    const delivery=await loadSnowlineStandard(track,anchors,'full',lib);
    expect(delivery.root.getObjectByName('snowline:gorge-wall:2:0')).toBeInstanceOf(THREE.InstancedMesh);
    expect(delivery.root.getObjectByName('snowline:lift-tower:2:0')).toBeInstanceOf(THREE.InstancedMesh);
    expect(delivery.root.children.some(o=>o.name.startsWith('snowline:contact-face:'))).toBe(true);
    expect(delivery.root.children.some(o=>o.name.startsWith('snowline:snowcat:'))).toBe(true);
    expect(delivery.textureBytes).toBeGreaterThan(1500);
    delivery.dispose();delivery.dispose();
    expect(delivery.root.children).toHaveLength(0);
    expect(bitmap.close).toHaveBeenCalledTimes(1);
    expect(normalBitmap.close).toHaveBeenCalledTimes(1);
    const second=await loadSnowlineStandard(track,anchors,'lod',lib);
    expect(second.root.children.length).toBeGreaterThan(0);
    second.dispose();
  });
});
