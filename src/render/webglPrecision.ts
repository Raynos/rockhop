/**
 * Three r186 dereferences WebGL2 getShaderPrecisionFormat(...).precision during
 * construction and again after context restoration. Safari sometimes returns
 * null instead of a precision format. Keep the native answer whenever present;
 * turn an absent answer into an unsupported format so Three can try mediump.
 *
 * If a browser forbids an instance method override, lowp skips Three's unsafe
 * precision probes entirely. This is a startup fallback, not a quality choice.
 */
export function guardWebGLPrecision(gl: WebGL2RenderingContext): 'highp' | 'lowp' {
  const query = gl.getShaderPrecisionFormat.bind(gl);
  try {
    Object.defineProperty(gl, 'getShaderPrecisionFormat', {
      configurable: true,
      value: (shader: number, format: number): WebGLShaderPrecisionFormat => {
        try {
          const result = query(shader, format);
          if (result) return result;
        } catch { /* Treat a failed probe as unsupported. */ }
        return { precision: 0, rangeMin: 0, rangeMax: 0 };
      },
    });
    return 'highp';
  } catch {
    return 'lowp';
  }
}
