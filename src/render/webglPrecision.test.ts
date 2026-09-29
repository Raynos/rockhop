import { describe, expect, it } from 'vitest';
import { guardWebGLPrecision } from './webglPrecision';

function context(read: () => { precision: number } | null): WebGL2RenderingContext {
  return { getShaderPrecisionFormat: read } as unknown as WebGL2RenderingContext;
}

describe('WebGL2 precision guard', () => {
  it('keeps normal high-precision answers', () => {
    const gl = context(() => ({ precision: 23 }));
    expect(guardWebGLPrecision(gl)).toBe('highp');
    expect(gl.getShaderPrecisionFormat(1, 2)?.precision).toBe(23);
  });

  it('lets Three fall back when Safari returns null', () => {
    const gl = context(() => null);
    expect(guardWebGLPrecision(gl)).toBe('highp');
    expect(gl.getShaderPrecisionFormat(1, 2)?.precision).toBe(0);
  });

  it('handles a null answer on a later Three query', () => {
    let calls = 0;
    const gl = context(() => (++calls % 2 === 1 ? { precision: 23 } : null));
    expect(guardWebGLPrecision(gl)).toBe('highp');
    expect(gl.getShaderPrecisionFormat(1, 2)?.precision).toBe(23);
    expect(gl.getShaderPrecisionFormat(1, 2)?.precision).toBe(0);
  });

  it('uses lowp when a context forbids the guard', () => {
    const gl = context(() => null);
    Object.defineProperty(gl, 'getShaderPrecisionFormat', { configurable: false, value: gl.getShaderPrecisionFormat });
    expect(guardWebGLPrecision(gl)).toBe('lowp');
  });
});
