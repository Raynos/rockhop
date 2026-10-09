import * as THREE from 'three';
import type { HeroBike } from '../bike/bikeModel';

/** Empty lifecycle holder behind the initial loader; it has no player artwork. */
export class LoadingRider {
  readonly root = new THREE.Group();
  readonly triangles = 0;
  attach(_bike: HeroBike): void {}
  detach(): void {}
  update(): void {}
  dispose(): void { this.root.removeFromParent(); }
}
