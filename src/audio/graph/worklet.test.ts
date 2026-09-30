import { afterEach, describe, expect, it, vi } from 'vitest';

const synths = vi.hoisted(() => [] as { setMaster: ReturnType<typeof vi.fn>; setMusicVolume: ReturnType<typeof vi.fn>; setAmbienceEnabled: ReturnType<typeof vi.fn>; setBed: ReturnType<typeof vi.fn>; setScene: ReturnType<typeof vi.fn>; setParams: ReturnType<typeof vi.fn>; process: ReturnType<typeof vi.fn> }[]);
vi.mock('../dsp/synth', () => ({
  RockhopSynth: class {
    pool = { killBuses: vi.fn() };
    crowd = { kill: vi.fn() };
    setMaster = vi.fn();
    setMusicVolume = vi.fn();
    setAmbienceEnabled = vi.fn();
    setBed = vi.fn();
    setScene = vi.fn();
    setParams = vi.fn();
    process = vi.fn();
    constructor() { synths.push(this); }
  },
}));

interface Processor {
  port: { onmessage: (event: { data: unknown }) => void };
  process(inputs: Float32Array[][], outputs: Float32Array[][]): boolean;
}

afterEach(() => {
  vi.unstubAllGlobals();
  synths.length = 0;
});

describe('worklet mixer state', () => {
  it('retains mute, music volume, scene and sample ambience coverage across track reseeds', async () => {
    vi.resetModules();
    vi.stubGlobal('sampleRate', 48_000);
    vi.stubGlobal('AudioWorkletProcessor', class { port = { onmessage: null }; });
    let ProcessorClass: (new () => Processor) | undefined;
    vi.stubGlobal('registerProcessor', (_name: string, ctor: new () => Processor) => { ProcessorClass = ctor; });
    await import('./worklet');
    const processor = new ProcessorClass!();
    const send = (data: unknown): void => processor.port.onmessage({ data });
    send({ master: 0 });
    expect(synths[0]!.setMaster).toHaveBeenCalledWith(0, true);
    send({ musicVolume: 0.25 });
    send({ scene: 1 });
    send({ bed: false });
    send({ ambience: false });
    send({ seed: 42 });
    const next = synths[1]!;
    expect(next.setMaster).toHaveBeenCalledWith(0, true);
    expect(next.setMusicVolume).toHaveBeenCalledWith(0.25, true);
    expect(next.setScene).toHaveBeenCalledWith(1);
    expect(next.setBed).toHaveBeenCalledWith(false);
    expect(next.setAmbienceEnabled).toHaveBeenCalledWith(false);
    const params = new Float32Array(64);
    send(params);
    expect(next.setParams).toHaveBeenCalledWith(params);
    send({ paused: true });
    const pausedSynth = next as unknown as { pool: { killBuses: ReturnType<typeof vi.fn> }; crowd: { kill: ReturnType<typeof vi.fn> } };
    expect(pausedSynth.pool.killBuses).toHaveBeenCalledWith(true, true, true);
    expect(pausedSynth.crowd.kill).toHaveBeenCalledOnce();
    send({ stop: true });
    expect(processor.process([], [[new Float32Array(128), new Float32Array(128)]])).toBe(false);
  });
});
