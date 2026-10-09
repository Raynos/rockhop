import { describe, expect, it } from 'vitest';
import * as THREE from 'three';
import { activeRiderTextureReceipt, selectedTextureReceipt } from './selectedTextureReceipt';

function rider(...materials: THREE.Material[]): THREE.Group {
  const root = new THREE.Group();
  for (const material of materials) root.add(new THREE.Mesh(undefined, material));
  return root;
}

function compressed(format: THREE.CompressedPixelFormat, data: Uint8Array[]): THREE.CompressedTexture {
  const texture = new THREE.CompressedTexture(data.map((bytes, level) => ({ data: bytes, width: Math.max(1, 4 >> level), height: Math.max(1, 4 >> level) })), 4, 4, format);
  texture.minFilter = THREE.LinearMipmapLinearFilter;
  texture.colorSpace = THREE.SRGBColorSpace;
  return texture;
}

describe('selected rider texture payload receipt', () => {
  it('follows the rider scene after bike attachment without including bike maps', () => {
    const map = compressed(THREE.RGBA_ASTC_4x4_Format, [new Uint8Array(16), new Uint8Array(16), new Uint8Array(16)]);
    const scene = rider(new THREE.MeshStandardMaterial({ map }));
    const placement = new THREE.Group(), root = new THREE.Group();
    placement.add(scene); root.add(placement);
    const bike = rider(new THREE.MeshStandardMaterial({ map: new THREE.DataTexture(new Uint8Array(64), 4, 4) }));
    bike.add(placement); // Actual selected rider attach reparents the placement.
    expect(root.children).toHaveLength(0);
    expect(selectedTextureReceipt(root).textureCount).toBe(0);
    const attachedRider = { root, scene };
    expect(activeRiderTextureReceipt(attachedRider)).toMatchObject({
      textureCount: 1, mapReferences: 1, payloadBytes: 48, unavailableTextures: 0, incompleteTextures: 0,
    });
    expect(scene.parent).toBe(placement); expect(placement.parent).toBe(bike);
    expect(activeRiderTextureReceipt({ root: scene }).textureCount).toBe(1);
  });

  it('sums actual ASTC mip views once across shared material maps and meshes', () => {
    const storage = new Uint8Array(128);
    const texture = compressed(THREE.RGBA_ASTC_4x4_Format, [storage.subarray(0, 16), storage.subarray(16, 32), storage.subarray(32, 48)]);
    const material = new THREE.MeshStandardMaterial({ map: texture, normalMap: texture });
    const result = selectedTextureReceipt(rider(material, material));
    expect(result).toMatchObject({ textureCount: 1, mapReferences: 4, payloadBytes: 48, compressedTextures: 1, unavailableTextures: 0, incompleteTextures: 0 });
    expect(result.textures[0]).toMatchObject({ slots: ['map', 'normalMap'], references: 4, format: THREE.RGBA_ASTC_4x4_Format, type: THREE.UnsignedByteType, colorSpace: THREE.SRGBColorSpace, width: 4, height: 4, payloadStatus: 'complete' });
    expect(result.textures[0]!.mipLevels.map(mip => mip.payloadBytes)).toEqual([16, 16, 16]);
    expect(texture.mipmaps[0]!.data).toBeInstanceOf(Uint8Array);
  });

  it('records literal RGBA fallback inside a compressed wrapper and counts image unavailability', () => {
    // KTX2Loader can return a CompressedTexture wrapper with an RGBA format.
    const fallback = compressed(THREE.RGBAFormat as THREE.CompressedPixelFormat, [new Uint8Array(64), new Uint8Array(16), new Uint8Array(4)]);
    const image = new THREE.Texture({ width: 8, height: 4 } as HTMLImageElement);
    const result = selectedTextureReceipt(rider(new THREE.MeshStandardMaterial({ map: fallback, roughnessMap: image })));
    expect(result).toMatchObject({ textureCount: 2, payloadBytes: 84, compressedTextures: 1, unavailableTextures: 1, incompleteTextures: 0 });
    expect(result.textures[0]).toMatchObject({ format: THREE.RGBAFormat, compressed: true, payloadStatus: 'complete' });
    expect(result.textures[1]).toMatchObject({ width: 8, height: 4, payloadBytes: 0, payloadStatus: 'unavailable' });
    expect(result.textures[1]!.mipLevels[0]!.payloadBytes).toBeNull();
  });

  it('marks missing mip streams and generated-on-upload mips as incomplete', () => {
    const partial = compressed(THREE.RGBA_ASTC_4x4_Format, [new Uint8Array(16), new Uint8Array(16)]);
    const generated = new THREE.DataTexture(new Uint8Array(64), 4, 4);
    generated.generateMipmaps = true;
    const result = selectedTextureReceipt(rider(new THREE.MeshStandardMaterial({ map: partial, normalMap: generated })));
    expect(result).toMatchObject({ payloadBytes: 96, incompleteTextures: 2, unavailableTextures: 0 });
    expect(result.textures.map(entry => entry.expectedMipLevels)).toEqual([3, 3]);
    expect(result.textures[1]).toMatchObject({ compressed: false, generateMipmaps: true, payloadStatus: 'incomplete' });
    expect(result.textures[1]!.mipLevels).toHaveLength(1);
  });

  it('reads a base-only typed image and excludes other roots without mutating materials', () => {
    const map = new THREE.DataTexture(new Uint16Array(8), 2, 1, THREE.RGBAFormat, THREE.UnsignedShortType);
    const selected = new THREE.MeshStandardMaterial({ map });
    const other = new THREE.MeshStandardMaterial({ map: compressed(THREE.RGBA_ASTC_4x4_Format, [new Uint8Array(16)]) });
    rider(other); // A pooled document or ghost outside the selected root is excluded.
    const version = map.version;
    const result = selectedTextureReceipt(rider(selected));
    expect(result).toMatchObject({ textureCount: 1, mapReferences: 1, payloadBytes: 16, unavailableTextures: 0, incompleteTextures: 0 });
    expect(result.textures[0]).toMatchObject({ format: THREE.RGBAFormat, type: THREE.UnsignedShortType, compressed: false, expectedMipLevels: 1, payloadStatus: 'complete' });
    expect(map.version).toBe(version);
    expect(selected.map).toBe(map);
    expect(selectedTextureReceipt(new THREE.Group()).textureCount).toBe(0);
  });
});
