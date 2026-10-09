/** Immutable selected source; both detail names intentionally draw the same high-resolution asset. */
export const SELECTED_RIDER_BYTES = 101885432;
export const SELECTED_RIDER_ASSET = {
  url: 'https://b47ghqoufyfsjh9t.public.blob.vercel-storage.com/rider-remaster/f814b8d7cde87b1e41b45eec75cd55fdea89b915bf9acae0e5a18b40d3a156af/rider.glb',
  bytes: SELECTED_RIDER_BYTES,
  sha256: 'f814b8d7cde87b1e41b45eec75cd55fdea89b915bf9acae0e5a18b40d3a156af',
  contractSHA256: '0301087649f7e2b2c442299bb21f61dc1e325c6b5b84afbc3ac5c4a594b72813',
} as const;

export function isSelectedRiderLogical(path: string): boolean {
  return /^models\/rider-street-remastered(-lod)?\.glb$/.test(path);
}
