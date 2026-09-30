import * as THREE from 'three';

/** GPU resources are owned by one course entry, never the shared material library. */
export interface CourseAssetDelivery {
  root: THREE.Group;
  textureBytes: number;
  dispose(): void;
}

export interface CourseAssetOwner {
  root: THREE.Group;
  ready: Promise<void>;
  readonly textureBytes: number;
  /** Immediately prevent a pending load from attaching to a retired world. */
  cancel(): void;
  /** Call after the renderer has retired this owner's material programs. */
  dispose(): void;
}

/** Keep authored course art inside entry warm-up and the world's resource lifetime. */
export function mountCourseAssets(
  load: Promise<CourseAssetDelivery>,
  report: (error: unknown) => void = error => console.warn('[render] course assets failed', error),
): CourseAssetOwner {
  const root = new THREE.Group();
  root.name = 'course-owned-assets';
  let cancelled = false;
  let disposed = false;
  let delivery: CourseAssetDelivery | null = null;
  const ready = load.then(asset => {
    if (cancelled || disposed) {
      asset.dispose();
      return;
    }
    delivery = asset;
    root.add(asset.root);
  }).catch(report);
  return {
    root,
    ready,
    get textureBytes() { return delivery?.textureBytes ?? 0; },
    cancel() { cancelled = true; },
    dispose() {
      if (disposed) return;
      disposed = cancelled = true;
      delivery?.dispose();
      delivery = null;
      root.clear();
    },
  };
}

/** Multiple authored families share one entry barrier and retirement lifetime. */
export function combineCourseAssets(...owners: CourseAssetOwner[]): CourseAssetOwner {
  const root = new THREE.Group(); root.name = 'course-owned-assets';
  let cancelled = false, disposed = false;
  const ready = Promise.all(owners.map(owner => owner.ready)).then(() => {
    if (!cancelled && !disposed) root.add(...owners.filter(owner => owner.root.children.length).map(owner => owner.root));
  });
  return {
    root, ready,
    get textureBytes() { return owners.reduce((sum, owner) => sum + owner.textureBytes, 0); },
    cancel() { cancelled = true; for (const owner of owners) owner.cancel(); },
    dispose() {
      if (disposed) return;
      disposed = cancelled = true;
      for (const owner of owners) owner.dispose();
      root.clear();
    },
  };
}
