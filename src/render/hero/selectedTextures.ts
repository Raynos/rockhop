import type { WebGLRenderer } from 'three';
import type { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';

let renderer: WebGLRenderer | undefined;

/** Texture format support belongs to the real device renderer. */
export function setHeroTextureRenderer(value: WebGLRenderer): void {
  renderer = value;
}

/** Keep the selected texture decoder in the separately measured rider chunk. */
export async function configureSelectedTextures(loader: GLTFLoader): Promise<void> {
  if (!renderer) throw new Error('Remaster texture renderer is not ready');
  const module = await import('./selected/textures');
  module.configureSelectedTextures(loader, renderer);
}
