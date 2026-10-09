/** Opt-in note receipt: actual submitted riding frames from the normal App RAF. */
import type { ReviewPerformance } from '../core/types';
import type { FrameSplit } from './bench';

export type ReviewFrameContext = Pick<ReviewPerformance, 'trackId' | 'outfit' | 'bike' | 'quality' | 'cap'>;
const WINDOW_MS = 20_000;
const MAX_FRAMES = 2048; // >20 seconds at the production 60 Hz cap.

/** Mirrors the lazy inbox gate without importing its DOM/transport chunk. */
export function reviewPerformanceEnabled(search: string, password: string | null): boolean {
  return /[?&]review=1(&|$)/.test(search) || !!password;
}

export class ReviewPerformanceWindow {
  private readonly at = new Float64Array(MAX_FRAMES);
  private readonly interval = new Float64Array(MAX_FRAMES);
  private readonly cpu = new Float32Array(MAX_FRAMES);
  private readonly physics = new Float32Array(MAX_FRAMES);
  private readonly submit = new Float32Array(MAX_FRAMES);
  private identity: ReviewFrameContext | null = null;
  private n = 0;
  private next = 0;
  private startedAt = 0;
  private lastAt = -1;

  reset(): void {
    this.n = this.next = this.startedAt = 0;
    this.lastAt = -1;
    this.identity = null;
  }

  /** Caller reuses context/split. No allocation or percentile sorting on this path. */
  frame(now: number, context: ReviewFrameContext, active: boolean, submitted: boolean, split: FrameSplit): void {
    if (!active) { this.reset(); return; }
    const old = this.identity;
    if (!old || old.trackId !== context.trackId || old.outfit !== context.outfit || old.bike !== context.bike
      || old.quality !== context.quality || old.cap !== context.cap) {
      this.reset();
      this.identity = { ...context };
    }
    if (!submitted || !Number.isFinite(now)) return;
    if (this.lastAt < 0) { this.startedAt = this.lastAt = now; return; }
    const interval = now - this.lastAt;
    if (interval <= 0) return;
    const i = this.next;
    this.at[i] = now;
    this.interval[i] = interval; // Wall interval, never the physics elapsed clamp.
    this.cpu[i] = split.totalMs;
    this.physics[i] = split.physicsMs;
    this.submit[i] = split.submitMs;
    this.lastAt = now;
    this.next = (i + 1) % MAX_FRAMES;
    this.n = Math.min(MAX_FRAMES, this.n + 1);
  }

  snapshot(now: number): ReviewPerformance | null {
    if (!this.identity || !this.n) return null;
    const cutoff = this.lastAt - WINDOW_MS;
    const indices: number[] = [];
    for (let i = 0; i < this.n; i++) if (this.at[i]! > cutoff) indices.push(i);
    const percentiles = (values: Float32Array | Float64Array): { p50: number; p95: number; max: number } => {
      const sorted = indices.map(i => values[i]!).sort((a, b) => a - b);
      const round = (v: number): number => Math.round(v * 1000) / 1000;
      return { p50: round(sorted[Math.floor(sorted.length * .5)] ?? 0), p95: round(sorted[Math.floor(sorted.length * .95)] ?? 0), max: round(sorted.at(-1) ?? 0) };
    };
    const durationMs = Math.min(WINDOW_MS, this.lastAt - this.startedAt);
    const ageMs = Math.max(0, now - this.lastAt);
    return {
      method: 'normal-raf-submitted-riding-frames', ...this.identity,
      phase: 'riding', windowMs: durationMs, frames: indices.length,
      fps: durationMs > 0 ? Math.round(indices.length * 1_000_000 / durationMs) / 1000 : 0,
      ready: durationMs >= WINDOW_MS && ageMs < 1000,
      sampleAgeMs: ageMs,
      frameMs: percentiles(this.interval), cpuMs: percentiles(this.cpu),
      physicsMs: percentiles(this.physics), submitMs: percentiles(this.submit),
      dropped: indices.filter(i => this.interval[i]! > 1.5 * 1000 / this.identity!.cap).length,
    };
  }
}
