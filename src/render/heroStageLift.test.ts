import { expect, it } from 'vitest';
import * as THREE from 'three';
import { ThreeRenderer } from './index';
import type { GltfRider } from './hero/gltfRider';

function fixture(material: THREE.MeshStandardMaterial) {
  const renderer = Object.assign(Object.create(ThreeRenderer.prototype) as object, { heroStageLift: new Map() }) as unknown as {
    applyHeroStageLift(instance: GltfRider, on: boolean): void;
  };
  const instance = { materials: [material] } as unknown as GltfRider;
  return (on: boolean) => renderer.applyHeroStageLift(instance, on);
}

it('preserves vertex-painted dark surfaces instead of self-lighting their neutral map', () => {
  const map = new THREE.Texture();
  const material = new THREE.MeshStandardMaterial({ vertexColors: true, map, emissive: 0x000000 });
  material.emissiveMap = map;
  const stage = fixture(material);
  for (const on of [true, false, true, false]) {
    stage(on);
    expect(material.emissive.getHex()).toBe(0);
    expect(material.emissiveMap).toBe(map);
    expect(material.vertexColors).toBe(true);
  }
});

it('restores authored emission after repeated textured-material stage entry and exit', () => {
  const albedo = new THREE.Texture(), emission = new THREE.Texture();
  const material = new THREE.MeshStandardMaterial({ map: albedo, color: 0x203040, emissive: 0x102030 });
  material.emissiveMap = emission;
  const stage = fixture(material);
  for (let i = 0; i < 2; i++) {
    stage(true);
    expect(material.emissiveMap).toBe(albedo);
    expect(material.color.getHex()).toBe(0x203040);
    const expected = new THREE.Color().setRGB(0.3, 0.4, 0.7).multiply(material.color);
    expect(material.emissive.toArray()).toEqual(expected.toArray());
    stage(false);
    expect(material.emissiveMap).toBe(emission);
    expect(material.emissive.getHex()).toBe(0x102030);
  }
});
