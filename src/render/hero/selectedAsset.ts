/** Immutable selected source; both detail names intentionally draw the same high-resolution asset. */
export const SELECTED_RIDER_BYTES = 77876632;
export const SELECTED_RIDER_ASSET = {
  url: 'https://b47ghqoufyfsjh9t.public.blob.vercel-storage.com/rider-remaster/a069b90c847734513ed8c79df596cfcfa0602363e767659655458eb045d319b7/rider.glb',
  bytes: SELECTED_RIDER_BYTES,
  sha256: 'a069b90c847734513ed8c79df596cfcfa0602363e767659655458eb045d319b7',
  contractSHA256: 'ba355c07e5e520fa2a91e6c16e58ada3b7568212eb914855fa13f45161c34a5b',
} as const;

export function isSelectedRiderLogical(path: string): boolean {
  return /^models\/rider-street-remastered(-lod)?\.glb$/.test(path);
}
