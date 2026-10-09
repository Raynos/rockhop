import fs from 'node:fs';
import { beforeEach, expect, it, vi } from 'vitest';
import { SELECTED_RIDER_ASSET } from './selectedAsset';

const load = vi.hoisted(() => vi.fn());
vi.mock('./selected/loader.mjs', () => ({ loadSelectedRiderClass: load }));
beforeEach(() => { vi.resetModules(); load.mockReset(); });

it('shares optional native loading and permits retry after a transient failure', async () => {
  class NativeRider { readonly native = true; }
  load.mockRejectedValueOnce(new Error('transient')).mockResolvedValue(NativeRider);
  const module = await import('./selectedDriver');
  const first = module.loadSelectedRiderClass();
  expect(module.loadSelectedRiderClass()).toBe(first);
  await expect(first).rejects.toThrow('transient');
  await expect(module.loadSelectedRiderClass()).resolves.toBe(NativeRider);
  expect(module.selectedRiderClass).toBe(NativeRider);
  expect(load).toHaveBeenCalledTimes(2);
});

it('ships the selected 75-joint contract with separate left/right clothes and fingers', () => {
  const contract = JSON.parse(fs.readFileSync('public/rider-remaster-contract.json', 'utf8')) as {
    sourceSHA256: string; metadataSHA256: string;
    specification: { jointNames: Record<string, string>; meshNames: Record<string, string>; hands: Record<string, { digits: Record<string, number[]> }> };
  };
  expect(contract.sourceSHA256).toBe(SELECTED_RIDER_ASSET.sha256);
  expect(contract.metadataSHA256).toBe('6fb6e726ee5f6b6c3dc3e378354a11c086a4fd5e8345169e26a80234f5cbc996');
  expect(Object.keys(contract.specification.jointNames)).toHaveLength(75);
  const roles = contract.specification.meshNames;
  for (const part of ['Glove', 'Boot']) {
    expect(roles[`ActualSelected${part}.L`]).toBe(`ActualSelected${part}.L`);
    expect(roles[`ActualSelected${part}.R`]).toBe(`ActualSelected${part}.R`);
  }
  expect(roles['RiderHoodie']).toBe('RiderHoodie');
  expect(roles['RiderJeans']).toBe('RiderJeans');
  const digits = ['left', 'right'].map(side => Object.values(contract.specification.hands[side]!.digits).flat());
  expect(digits.every(side => side.length >= 15)).toBe(true);
  expect(digits[0]!.some(id => digits[1]!.includes(id))).toBe(false);
});
