import * as THREE from 'three';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { MaterialLibrary } from '../../materials/library';
import { loadC1Harbor } from './c1Harbor';

const { loadAsync } = vi.hoisted(() => ({ loadAsync: vi.fn() }));
vi.mock('three/examples/jsm/loaders/GLTFLoader.js', () => ({
  GLTFLoader: class { setMeshoptDecoder() { return this; } loadAsync = loadAsync; },
}));
vi.mock('../../hero/urls', () => ({ modelAssetUrl: (url: string) => url }));

describe('C1 authored map lifetime', () => {
  beforeEach(() => loadAsync.mockReset());

  it('closes a shared decoded bitmap once and leaves library maps alone', async () => {
    const bitmap = { width: 512, height: 256, close: vi.fn() };
    const authoredMap = new THREE.Texture(bitmap as unknown as HTMLImageElement);
    const sharedMap = new THREE.Texture();
    const authoredDispose = vi.spyOn(authoredMap, 'dispose');
    const sharedDispose = vi.spyOn(sharedMap, 'dispose');
    const root = new THREE.Group();
    for (let i = 0; i < 2; i++) {
      root.add(new THREE.Mesh(new THREE.BoxGeometry(), new THREE.MeshStandardMaterial({ map: authoredMap })));
    }
    loadAsync.mockResolvedValue({ scene: root });
    const lib = { complete: (mat: THREE.MeshStandardMaterial) => { mat.normalMap = sharedMap; } } as MaterialLibrary;

    const asset = await loadC1Harbor('lod', lib);
    expect(loadAsync).toHaveBeenCalledWith('models/c1-harbor-tug-lod.glb');
    expect(asset.textureBytes).toBeGreaterThan(0);
    asset.dispose();
    asset.dispose();
    expect(authoredDispose).toHaveBeenCalledTimes(1);
    expect(bitmap.close).toHaveBeenCalledTimes(1);
    expect(sharedDispose).not.toHaveBeenCalled();
  });
});
