/** Native75 metadata belongs to the optional selected-rider module. */
import { createPrivateRiderClass } from './private-rider.mjs';

export async function loadSelectedRiderClass(baseURL = globalThis.document.baseURI) {
  const response = await fetch(new URL('model-catalog.json', baseURL));
  if (!response.ok) throw new Error('Rider metadata HTTP ' + response.status);
  const { privateRiderMetadata } = await response.json();
  if (!privateRiderMetadata) throw new Error('Missing rider metadata');
  return createPrivateRiderClass(privateRiderMetadata);
}
