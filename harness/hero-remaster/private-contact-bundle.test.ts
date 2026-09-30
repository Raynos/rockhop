import { describe, expect, it } from 'vitest';
import vm from 'node:vm';
import * as THREE from 'three';
import type * as ContactBrowserModule from './contact-browser.mjs';
import { privateContactBundle } from './private-contact-bundle.mjs';

describe('private surface bundle', () => {
  it('runs as a standalone browser global and returns four unmeasured slots without a mapping', async () => {
    const code = await privateContactBundle();
    const context = vm.createContext({ __rockhopContactTHREE: THREE });
    vm.runInContext(code, context);
    const helper = context.RockhopContactProbe as typeof ContactBrowserModule;
    expect(helper.ContactVector3).toBe(THREE.Vector3);
    expect(helper.CONTACT_IDS).toEqual(['hand.L', 'hand.R', 'foot.L', 'foot.R']);
    // The bundle executes without a Node import resolver. The empty mapping path
    // intentionally does not inspect/guess any mesh patch on these group roots.
    const root = new THREE.Group();
    const probe = await helper.prepareSurfaceContacts(null, { rider: root, bike: root },
      { riderSHA256: 'a'.repeat(64), bikeSHA256: 'b'.repeat(64) });
    expect(Object.values(probe.sample())).toEqual(helper.CONTACT_IDS.map(() => ({ status: 'unmeasured', reason: 'mapping missing or unsupported' })));
  });
});
