/**
 * The recorded music cues (store release Phase 4, assets/audio/LEDGER.md). Seven cues: the front
 * end (`menu`), the world map (`map`), one ride loop per zone, and the results sting (`results`).
 *
 * Each file is MP3 under `public/audio/`, content-hashed in its name. A loop is stored as
 *
 *   [ pre s: the loop's last pre seconds ][ len s: the loop, cut on bar lines ][ pre s: its first pre seconds ]
 *
 * so the padded body is periodic with period `len` everywhere. Any window of exactly `len` seconds inside it
 * loops seamlessly, which makes the seam immune to how a decoder treats codec priming / padding
 * samples (native browser and ffmpeg decoder offsets are measured by the harness;
 * the 2112-sample probe stays far inside `pre`). The player loops [pre, pre + len).
 *
 * `cues.generated.ts` is written by assets/audio/pipeline/remaster_master.py; hand edits are overwritten.
 */
import type { MusicZone } from './zone';
import { CUE_FILES } from './cues.generated';

export type MusicCue = 'menu' | 'map' | MusicZone | 'results';

export interface CueFile {
  /** File name under public/audio/. */
  file: string;
  /** Loops (menu, map, zones) or plays once (results). */
  loop: boolean;
  /** Seconds of wrap-around padding before (and after) the loop body; 0 for a one-shot. */
  pre: number;
  /** Loop length in seconds (a whole number of bars), or the one-shot's length. */
  len: number;
  /** Per-file trim on top of the scene level, dB (loops are −18 LUFS, the finish sting −16 LUFS; this is taste). */
  gainDb: number;
  /** Tempo, for the ledger and any future bar-synced transition. */
  bpm: number;
  bytes: number;
}

export const MUSIC_CUES: Readonly<Partial<Record<MusicCue, CueFile>>> = CUE_FILES;
