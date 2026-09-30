import { describe, expect, it } from 'vitest';
import { assertRequestedBootRenderer, selectOfflineBrowserBackend } from './boot-trace';

describe('normal offline benchmark backend qualification', () => {
  it('retains portable flags by default and rejects unavailable hardware', () => {
    expect(selectOfflineBrowserBackend('swiftshader', 'linux')).toEqual({backend:'swiftshader',args:['--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist']});
    expect(selectOfflineBrowserBackend('metal', 'darwin').args).toContain('--use-angle=metal');
    expect(() => selectOfflineBrowserBackend('metal', 'linux')).toThrow('requires macOS');
    expect(() => selectOfflineBrowserBackend('vulkan', 'darwin')).toThrow('Unsupported');
  });
  it('refuses silent renderer fallback or missing context instead of blessing Metal', () => {
    for (const actual of [null,{contextKind:'webgl2',renderer:'ANGLE SwiftShader'}, {contextKind:'webgl',renderer:'ANGLE Metal Apple GPU'}, {contextKind:'webgl2',renderer:'Metal software fallback'}]) {
      expect(() => assertRequestedBootRenderer('metal', actual, 'cached boot')).toThrow('cached boot: requested Metal WebGL2');
    }
    expect(() => assertRequestedBootRenderer('metal', {contextKind:'webgl2',renderer:'Google Inc. (Apple) / ANGLE Metal Renderer: Apple M5 Max'}, 'cached boot')).not.toThrow();
    expect(() => assertRequestedBootRenderer('swiftshader', null, 'failed startup')).not.toThrow();
  });
});
