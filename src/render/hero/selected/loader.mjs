import { createSelectedRiderClass } from './rider.mjs';
import { SELECTED_RIDER_ASSET } from '../selectedAsset';

export async function loadSelectedRiderClass() {
  const response = await fetch(new URL('rider-remaster-contract.json', globalThis.document.baseURI));
  if (!response.ok) throw new Error(`Rider metadata HTTP ${response.status}`);
  const metadata = await response.json();
  if (metadata.sourceSHA256 !== SELECTED_RIDER_ASSET.sha256 || metadata.metadataSHA256 !== SELECTED_RIDER_ASSET.contractSHA256) {
    throw new Error('Remastered rider source identity differs from its pinned contract');
  }
  return createSelectedRiderClass(metadata);
}
