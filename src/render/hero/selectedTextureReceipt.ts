import { LinearFilter, NearestFilter, type Material, type Object3D, type Texture } from 'three';
import type { SelectedTextureReceipt } from '../../core/types';

type Entry = SelectedTextureReceipt['textures'][number];
type PayloadImage = { width?: number; height?: number; data?: unknown };
const dimension = (value: unknown): number | null => typeof value === 'number' && Number.isInteger(value) && value > 0 ? value : null;

/** The rider scene remains its visual owner after attachment under the bike. */
export function activeRiderTextureReceipt(rider: { root: Object3D }): SelectedTextureReceipt {
  // The legacy driver keeps scene private in TypeScript; the selected driver
  // exposes it. Both own this scene at runtime, independently of its parent.
  const scene = Reflect.get(rider, 'scene') as Object3D | undefined;
  return selectedTextureReceipt(scene?.isObject3D ? scene : rider.root);
}

function inspect(texture: Texture): Entry {
  const image = texture.image as PayloadImage | undefined;
  const width = dimension(image?.width), height = dimension(image?.height);
  const mipmapped = texture.generateMipmaps || (texture.minFilter !== LinearFilter && texture.minFilter !== NearestFilter);
  const expectedMipLevels = width && height ? (mipmapped ? Math.floor(Math.log2(Math.max(width, height))) + 1 : 1) : null;
  // KTX2 retains the complete transcoded stream in mipmaps. DataTexture without
  // explicit mips retains its base in image.data. Never count both copies.
  const sources = texture.mipmaps.length ? texture.mipmaps : [image];
  const mipLevels = sources.map((source, level) => {
    const mip = source as PayloadImage | undefined;
    return {
      level, width: dimension(mip?.width), height: dimension(mip?.height),
      payloadBytes: ArrayBuffer.isView(mip?.data) ? mip.data.byteLength : null,
    };
  });
  const payloadBytes = mipLevels.reduce((sum, mip) => sum + (mip.payloadBytes ?? 0), 0);
  const dimensionsMatch = width !== null && height !== null && mipLevels.every((mip, level) =>
    mip.width === Math.max(1, Math.floor(width / 2 ** level)) && mip.height === Math.max(1, Math.floor(height / 2 ** level)));
  const available = mipLevels.some(mip => mip.payloadBytes !== null);
  const complete = expectedMipLevels !== null && mipLevels.length === expectedMipLevels
    && dimensionsMatch && mipLevels.every(mip => mip.payloadBytes !== null && mip.payloadBytes > 0);
  return {
    slots: [], references: 0,
    // Literal Three codes: the compressed wrapper can also hold an RGBA fallback.
    format: texture.format, type: texture.type, colorSpace: texture.colorSpace,
    compressed: (texture as Texture & { isCompressedTexture?: boolean }).isCompressedTexture === true,
    width, height, generateMipmaps: texture.generateMipmaps, expectedMipLevels,
    payloadBytes, payloadStatus: !available ? 'unavailable' : complete ? 'complete' : 'incomplete', mipLevels,
  };
}

/** Snapshot only. Reads CPU-side payload metadata, without renderer or GL access. */
export function selectedTextureReceipt(root: Object3D): SelectedTextureReceipt {
  const seen = new Map<Texture, Entry>();
  let mapReferences = 0;
  root.traverse(object => {
    const mesh = object as Object3D & { isMesh?: boolean; material?: Material | Material[] };
    if (!mesh.isMesh || !mesh.material) return;
    const materials = Array.isArray(mesh.material) ? mesh.material : [mesh.material];
    for (const material of materials) for (const [slot, value] of Object.entries(material)) {
      if (!value || typeof value !== 'object' || (value as Texture).isTexture !== true) continue;
      const texture = value as Texture;
      let entry = seen.get(texture);
      if (!entry) { entry = inspect(texture); seen.set(texture, entry); }
      entry.references++;
      if (!entry.slots.includes(slot)) entry.slots.push(slot);
      mapReferences++;
    }
  });
  const textures = [...seen.values()];
  return {
    method: 'selected-rider-material-typed-array-payloads', textureCount: textures.length, mapReferences,
    payloadBytes: textures.reduce((sum, entry) => sum + entry.payloadBytes, 0),
    compressedTextures: textures.filter(entry => entry.compressed).length,
    unavailableTextures: textures.filter(entry => entry.payloadStatus === 'unavailable').length,
    incompleteTextures: textures.filter(entry => entry.payloadStatus === 'incomplete').length, textures,
  };
}
