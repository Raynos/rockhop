/** The menu and in-race stingers share one deterministic sound design. */
import { TK } from '../params';
import { BUS_UI, VoicePool } from './voices';

export type MenuCue = 'menuFocus' | 'menuConfirm' | 'menuBack' | 'menuLaunch';
const LENGTHS: Record<MenuCue, number> = { menuFocus: 0.08, menuConfirm: 0.52, menuBack: 0.25, menuLaunch: 0.72 };

/** Offline PCM only: callers choose whether to create any Web Audio nodes. */
export function renderMenuCue(cue: MenuCue, sampleRate: number): [Float32Array, Float32Array] {
  const n = Math.ceil(LENGTHS[cue] * sampleRate);
  const buses: [Float32Array, Float32Array][] = Array.from({ length: 3 }, () => [new Float32Array(n), new Float32Array(n)]);
  const pool = new VoicePool(sampleRate, 0x52484f50, 4);
  pool.trigger({ kind: TK[cue], gain: 1, pitch: 0, pan: 0, delay: 0 });
  pool.process(buses, 0, n);
  return buses[BUS_UI]!;
}
