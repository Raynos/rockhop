import { describe, expect, it, vi } from 'vitest';
import { WebGL2ContextUnavailableError } from './index';
import { retryWebGL2Startup } from './startupRetry';

describe('WebGL2 startup recovery', () => {
  it('recovers after two unavailable contexts without duplicating the successful renderer', async () => {
    const pause = vi.fn(async (_ms: number) => undefined);
    const create = vi.fn((attempt: number) => {
      if (attempt < 2) throw new WebGL2ContextUnavailableError('null');
      return { canvas: 'third, fresh canvas' };
    });
    await expect(retryWebGL2Startup(create, pause)).resolves.toEqual({ canvas: 'third, fresh canvas' });
    expect(create.mock.calls.map(([attempt]) => attempt)).toEqual([0, 1, 2]);
    expect(pause.mock.calls.map(([ms]) => ms)).toEqual([250, 750]);
  });

  it('stops after five failures, leaving the boot error visible', async () => {
    const pause = vi.fn(async (_ms: number) => undefined);
    const create = vi.fn(() => { throw new WebGL2ContextUnavailableError('null'); });
    await expect(retryWebGL2Startup(create, pause)).rejects.toBeInstanceOf(WebGL2ContextUnavailableError);
    expect(create).toHaveBeenCalledTimes(5);
    expect(pause.mock.calls.map(([ms]) => ms)).toEqual([250, 750, 1500, 3000]);
  });

  it('does not retry a non-context startup error', async () => {
    const pause = vi.fn(async (_ms: number) => undefined);
    const create = vi.fn(() => { throw new Error('shader bug'); });
    await expect(retryWebGL2Startup(create, pause)).rejects.toThrow('shader bug');
    expect(create).toHaveBeenCalledTimes(1);
    expect(pause).not.toHaveBeenCalled();
  });
});
