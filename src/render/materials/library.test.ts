import { describe, expect, it, vi } from 'vitest';
import * as THREE from 'three';
import type * as Texgen from './texgen';
// Keep real map generation/binding, but shrink painter inputs for this lifecycle test.
vi.mock('./texgen', async (original) => {
  const actual = await original<typeof Texgen>();
  return { ...actual, TexGenJob: class extends actual.TexGenJob {
    constructor(...args: ConstructorParameters<typeof actual.TexGenJob>) {
      super(2, args[1], args[2], args[3]);
    }
  } };
});
import { MaterialLibrary } from './library';

describe('late procedural map binding', () => {
  it('keeps authored tread relief and albedo while binding late normal/ORM maps', () => {
    const library = new MaterialLibrary(42);
    const tread = library.derive('concrete');
    const control = library.derive('concrete');
    const albedo = new THREE.Texture();
    tread.map = albedo;
    tread.userData.normalScaleOverride = true;
    tread.normalScale.set(0.24, 0.24);
    control.normalScale.set(0.24, 0.24);
    const placeholder = tread.normalMap;
    expect(library.hasTextures).toBe(false);
    library.generateTextures();
    const base = library.get('concrete');
    expect(library.hasTextures).toBe(true);
    expect(tread.map).toBe(albedo);
    expect(tread.normalMap).toBe(base.normalMap);
    expect(tread.normalMap).not.toBe(placeholder);
    expect(tread.roughnessMap).toBe(base.roughnessMap);
    expect(tread.normalScale.toArray()).toEqual([0.24, 0.24]);
    expect(control.normalScale.toArray()).toEqual(base.normalScale.toArray());
    expect(control.map).toBe(base.map);
    library.dispose();
    tread.dispose(); control.dispose(); albedo.dispose();
  });
});
