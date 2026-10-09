/** Immutable selected source; both detail names intentionally draw the same high-resolution asset. */
export const SELECTED_RIDER_BYTES = 358409072;
export const SELECTED_RIDER_ASSET = {
  url: 'https://b47ghqoufyfsjh9t.public.blob.vercel-storage.com/rider-remaster/127e316a8ff7910a4918b63f83e086e4e658062f102c73f17d0ee2f956750649/rider.glb',
  bytes: SELECTED_RIDER_BYTES,
  sha256: '127e316a8ff7910a4918b63f83e086e4e658062f102c73f17d0ee2f956750649',
} as const;

export function isSelectedRiderLogical(path: string): boolean {
  return /^models\/rider-street-remastered(-lod)?\.glb$/.test(path);
}
