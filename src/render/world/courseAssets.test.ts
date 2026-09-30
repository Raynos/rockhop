import * as THREE from 'three';
import { describe, expect, it, vi } from 'vitest';
import { combineCourseAssets, mountCourseAssets, type CourseAssetDelivery } from './courseAssets';

function delayed() {
  let resolve!: (asset: CourseAssetDelivery) => void;
  let reject!: (error: unknown) => void;
  const promise = new Promise<CourseAssetDelivery>((yes, no) => { resolve = yes; reject = no; });
  const asset = { root: new THREE.Group(), textureBytes: 1024, dispose: vi.fn() };
  return { promise, resolve, reject, asset };
}

describe('authored course asset lifetime', () => {
  it('waits for art before entry warm-up and keeps it alive until owner retirement', async () => {
    const f = delayed();
    const owner = mountCourseAssets(f.promise);
    expect(owner.root.children).toHaveLength(0);
    f.resolve(f.asset);
    await owner.ready;
    expect(owner.root.children).toEqual([f.asset.root]);
    expect(owner.textureBytes).toBe(1024);
    owner.cancel();
    expect(f.asset.dispose).not.toHaveBeenCalled();
    owner.dispose();
    owner.dispose();
    expect(f.asset.dispose).toHaveBeenCalledOnce();
    expect(owner.root.children).toHaveLength(0);
    expect(owner.textureBytes).toBe(0);
  });

  it.each(['cancel', 'dispose'] as const)('discards late art after %s instead of attaching it to the next world', async action => {
    const f = delayed();
    const owner = mountCourseAssets(f.promise);
    owner[action]();
    f.resolve(f.asset);
    await owner.ready;
    expect(owner.root.children).toHaveLength(0);
    expect(f.asset.dispose).toHaveBeenCalledOnce();
    expect(owner.textureBytes).toBe(0);
    owner.dispose();
    expect(f.asset.dispose).toHaveBeenCalledOnce();
  });

  it('allows the procedural course to enter when authored art cannot load', async () => {
    const f = delayed();
    const report = vi.fn();
    const owner = mountCourseAssets(f.promise, report);
    const error = new Error('offline art unavailable');
    f.reject(error);
    await owner.ready;
    expect(report).toHaveBeenCalledExactlyOnceWith(error);
    expect(owner.root.children).toHaveLength(0);
    owner.dispose();
  });
});

describe('combined authored families', () => {
  it('waits for both, counts both, and retires their resources once', async () => {
    const a = delayed(), b = delayed();
    const combined = combineCourseAssets(mountCourseAssets(a.promise), mountCourseAssets(b.promise));
    a.resolve(a.asset); await Promise.resolve(); expect(combined.root.children).toHaveLength(0);
    b.resolve(b.asset); await combined.ready;
    expect(combined.root.children).toHaveLength(2); expect(combined.textureBytes).toBe(2048);
    combined.dispose(); combined.dispose();
    expect(a.asset.dispose).toHaveBeenCalledOnce(); expect(b.asset.dispose).toHaveBeenCalledOnce();
    expect(combined.textureBytes).toBe(0); expect(combined.root.children).toHaveLength(0);
  });
  it('rejects late attachment to a cancelled combined world', async () => {
    const a = delayed(), b = delayed();
    const combined = combineCourseAssets(mountCourseAssets(a.promise), mountCourseAssets(b.promise));
    combined.cancel(); a.resolve(a.asset); b.resolve(b.asset); await combined.ready;
    expect(combined.root.children).toHaveLength(0);
    expect(a.asset.dispose).toHaveBeenCalledOnce(); expect(b.asset.dispose).toHaveBeenCalledOnce();
  });
});
