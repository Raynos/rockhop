import { describe, expect, it } from 'vitest';
import { captureOptions } from './capture-options.mjs';

describe('private hero capture options', () => {
  const positional = ['build', 'recording', 'out', '0', '120', 'high', 'street', '60', '1280x720', 'webkit', '1', 'desktop'];
  it('preserves the complete existing positional invocation', () => {
    expect(captureOptions(positional)).toEqual({ positional, surfaceMap: null });
  });
  it('accepts a surface mapping anywhere without shifting positional arguments', () => {
    expect(captureOptions(['--surface-map', '/absolute/contact map.json', ...positional])).toEqual({ positional, surfaceMap: '/absolute/contact map.json' });
    expect(captureOptions([...positional, '--surface-map=/absolute/map.json'])).toEqual({ positional, surfaceMap: '/absolute/map.json' });
  });
  it('rejects ambiguous or missing mappings before launching a browser', () => {
    expect(() => captureOptions([...positional, '--surface-map'])).toThrow('requires a file path');
    expect(() => captureOptions([...positional, '--surface-map='])).toThrow('requires a file path');
    expect(() => captureOptions(['--surface-map', '--surface-map=a'])).toThrow('requires a file path');
    expect(() => captureOptions(['--surface-map=a', '--surface-map=b'])).toThrow('duplicate');
  });
});
