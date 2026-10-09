import { createSelectedRiderClass } from './rider.mjs';
import { SELECTED_RIDER_ASSET } from '../selectedAsset';

export async function loadSelectedRiderClass() {
  const response = await fetch(new URL('rider-remaster-contract.json', globalThis.document.baseURI));
  if (!response.ok) throw new Error(`Rider metadata HTTP ${response.status}`);
  const metadata = await response.json();
  if (metadata.sourceSHA256 !== SELECTED_RIDER_ASSET.sha256 || metadata.metadataSHA256 !== '6fb6e726ee5f6b6c3dc3e378354a11c086a4fd5e8345169e26a80234f5cbc996') {
    throw new Error('Remastered rider source identity differs from its pinned contract');
  }
  return createSelectedRiderClass(metadata);
}
