import type { AudioScene } from '../index';
import { TK, type AudioParams, type Transient } from '../params';
import type { MusicZone } from '../music/zone';
import type { SampleClip, SampleManifest } from './player';

export interface SamplePCM {
  channels: readonly Float32Array[];
  sampleRate: number;
}
interface Shot {
  clip: SampleClip;
  pcm: SamplePCM;
  startsAt: number;
  gain: number;
  left: number;
  right: number;
}
const FAMILIES = new Map<number, string>([TK.grunt, TK.crowdRoar, TK.crowdCheer, TK.crowdGroan, TK.crowdApplause].map((kind, i) => [kind, ['grunt', 'crowdRoar', 'crowdCheer', 'crowdGroan', 'crowdApplause'][i]!]));
const finite = (n: number, fallback = 0): number => Number.isFinite(n) ? n : fallback;
const clamp = (n: number): number => Math.max(0, Math.min(1, finite(n)));

/** Pure deterministic counterpart to SamplePlayer, with injected decoded PCM and no browser/clock/I/O. */
export class OfflineSampleMixer {
  private position = 0;
  private zone: MusicZone = 'coast';
  private scene: AudioScene = 'run';
  private bedPhase = 0;
  private ambientTarget = 0;
  private ambient = 0;
  private duckTarget = 1;
  private duck = 1;
  private shots: Shot[] = [];
  private counters = new Map<number, number>();
  private readonly ambientCoefficient: number;
  private readonly duckCoefficient: number;

  constructor(readonly sampleRate: number, private readonly manifest: SampleManifest, private readonly pcm: ReadonlyMap<string, SamplePCM>) {
    if (!Number.isFinite(sampleRate) || sampleRate <= 0) throw new Error('sampleRate must be positive');
    this.ambientCoefficient = 1 - Math.exp(-1 / (.2 * sampleRate));
    this.duckCoefficient = 1 - Math.exp(-1 / (.015 * sampleRate));
  }

  private valid(clip: SampleClip): SamplePCM | null {
    const pcm = this.pcm.get(clip.file);
    const frames = pcm?.channels[0]?.length ?? 0;
    if (!pcm || !(pcm.sampleRate > 0) || !pcm.channels.length || !Number.isFinite(clip.start) || !Number.isFinite(clip.duration) || !Number.isFinite(clip.gain) || clip.duration <= 0 || clip.start < 0 || clip.start + clip.duration > frames / pcm.sampleRate + .01) return null;
    return pcm;
  }

  get ambienceCovered(): boolean {
    const clip = this.manifest.beds[this.zone];
    return this.scene === 'run' && !!clip && !!this.valid(clip);
  }

  setZone(zone: MusicZone): void {
    if (zone !== this.zone) { this.zone = zone; this.bedPhase = 0; this.ambient = 0; }
  }
  setScene(scene: AudioScene): void {
    if (this.scene === scene) return;
    this.scene = scene;
    if (scene !== 'run') this.restart();
    this.bedPhase = 0;
  }
  restart(): void { this.shots = []; this.counters.clear(); }

  /** Schedule only valid clips and return transients the procedural synth must retain. */
  consume(params: AudioParams): Transient[] {
    this.ambientTarget = clamp(params.ambientGain);
    this.duckTarget = Math.pow(10, -Math.max(0, Math.min(24, finite(params.duckDb))) / 20);
    const remaining: Transient[] = [];
    for (let i = 0; i < params.transientCount; i++) {
      const transient = params.transients[i]!;
      if (transient.kind === TK.restart || transient.kind === TK.kill) this.restart();
      const available = this.manifest.oneshots[FAMILIES.get(transient.kind) ?? '']?.filter((clip) => this.valid(clip));
      if (!available?.length) { remaining.push(transient); continue; }
      const counter = this.counters.get(transient.kind) ?? 0;
      const clip = available[counter % available.length]!;
      const pan = Math.max(-1, Math.min(1, finite(transient.pan)));
      while (this.shots.length >= 6) this.shots.shift();
      this.shots.push({ clip, pcm: this.valid(clip)!, startsAt: this.position + Math.round(Math.max(0, finite(transient.delay)) * this.sampleRate), gain: clamp(transient.gain) * clip.gain, left: Math.cos((pan + 1) * Math.PI / 4), right: Math.sin((pan + 1) * Math.PI / 4) });
      this.counters.set(transient.kind, counter + 1);
    }
    return remaining;
  }

  private read(pcm: SamplePCM, channel: number, seconds: number): number {
    const data = pcm.channels[channel] ?? pcm.channels[0]!;
    const index = seconds * pcm.sampleRate;
    const i = Math.floor(index);
    const t = index - i;
    return finite(data[i] ?? 0) * (1 - t) + finite(data[i + 1] ?? data[i] ?? 0) * t;
  }

  /** Add onto the synth buffers. Repeating the same calls produces identical PCM bytes. */
  process(left: Float32Array, right: Float32Array, offset: number, count: number, master = 1): void {
    const clip = this.manifest.beds[this.zone];
    const bed = clip && this.ambienceCovered ? this.valid(clip) : null;
    const volume = clamp(master);
    if (volume === 0) this.restart();
    for (let n = 0; n < count; n++) {
      const now = this.position++;
      this.ambient += this.ambientCoefficient * (this.ambientTarget - this.ambient);
      this.duck += this.duckCoefficient * (this.duckTarget - this.duck);
      let l = 0, r = 0;
      if (bed && clip) {
        const seconds = clip.start + (this.bedPhase++ / this.sampleRate) % clip.duration;
        l += this.read(bed, 0, seconds) * this.ambient * clip.gain;
        r += this.read(bed, bed.channels.length > 1 ? 1 : 0, seconds) * this.ambient * clip.gain;
      }
      for (const shot of this.shots) {
        const elapsed = (now - shot.startsAt) / this.sampleRate;
        if (elapsed < 0 || elapsed >= shot.clip.duration) continue;
        const attack = Math.min(.008, shot.clip.duration / 4);
        const release = Math.min(.025, shot.clip.duration / 4);
        const envelope = Math.min(1, elapsed / attack, (shot.clip.duration - elapsed) / release);
        const sample = this.read(shot.pcm, 0, shot.clip.start + elapsed) * shot.gain * envelope;
        l += sample * shot.left; r += sample * shot.right;
      }
      left[offset + n] = (left[offset + n] ?? 0) + l * this.duck * volume;
      right[offset + n] = (right[offset + n] ?? 0) + r * this.duck * volume;
    }
    this.shots = this.shots.filter((shot) => this.position < shot.startsAt + Math.round(shot.clip.duration * this.sampleRate));
  }
}
