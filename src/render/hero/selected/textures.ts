import type { WebGLRenderer } from 'three';
import type { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { KTX2Loader } from 'three/examples/jsm/loaders/KTX2Loader.js';

let textures: KTX2Loader | undefined;
let textureRenderer: WebGLRenderer | undefined;

/** Pinned Three codec assets are emitted by Vite with their content hashes. */
export function configureSelectedTextures(loader: GLTFLoader, renderer: WebGLRenderer): void {
  textures ??= new KTX2Loader().setWorkerLimit(2);
  if (textureRenderer !== renderer) {
    textures.detectSupport(renderer);
    textureRenderer = renderer;
  }
  loader.setKTX2Loader(textures);
}
