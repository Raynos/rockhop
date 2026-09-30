import type { AudioScene } from '../index';
import { TK, type AudioParams, type Transient } from '../params';
import type { MusicZone } from '../music/zone';
import defaultManifest from './manifest.json';

export interface SampleClip {
  file: string;
  start: number;
  duration: number;
  gain: number;
}
export interface SampleManifest {
  oneshots: Readonly<Partial<Record<string, readonly SampleClip[]>>>;
  beds: Readonly<Partial<Record<MusicZone, SampleClip>>>;
}
export interface SamplePlayerOptions {
  manifest?: SampleManifest;
  base?: string;
  fetchBytes?: (url: string) => Promise<ArrayBuffer>;
  onCoverage?: (coverage: { kinds: number[]; ambience: boolean }) => void;
}
interface Voice {
  source: AudioBufferSourceNode;
  gain: GainNode;
  pan: StereoPannerNode | null;
}
const KINDS = ['grunt', 'crowdRoar', 'crowdCheer', 'crowdGroan', 'crowdApplause'] as const;
const FAMILY = new Map<number, string>(KINDS.map((kind) => [TK[kind], kind]));
const MAX_VOICES = 6;
const MAX_BEDS = 2;
const clamp = (n: number): number => Math.max(0, Math.min(1, Number.isFinite(n) ? n : 0));

/** Recorded voices share the unlocked context. Failed or pending files leave the procedural voice available. */
export class SamplePlayer {
  readonly output: GainNode;
  private readonly duck: GainNode;
  private readonly manifest: SampleManifest;
  private readonly fetchBytes: (url: string) => Promise<ArrayBuffer>;
  private readonly base: string;
  private readonly coverage: NonNullable<SamplePlayerOptions['onCoverage']>;
  private readonly buffers = new Map<string, AudioBuffer>();
  private readonly loads = new Map<string, Promise<void>>();
  private readonly failed = new Set<string>();
  private readonly shots = new Set<Voice>();
  private readonly bedFiles: string[] = [];
  private readonly counters = new Map<number, number>();
  private bed: (Voice & { file: string }) | null = null;
  private zone: MusicZone = 'coast';
  private scene: AudioScene = 'menu';
  private master = 1;
  private disposed = false;
  private ambientGain = 0;

  constructor(private readonly context: BaseAudioContext, destination: AudioNode, options: SamplePlayerOptions = {}) {
    this.manifest = options.manifest ?? defaultManifest;
    this.base = options.base ?? './audio/sfx/';
    this.fetchBytes = options.fetchBytes ?? (async (url) => {
      const response = await fetch(url);
      if (!response.ok) throw new Error(`${url}: ${response.status}`);
      return response.arrayBuffer();
    });
    this.coverage = options.onCoverage ?? (() => undefined);
    this.output = context.createGain();
    this.output.connect(destination);
    this.duck = context.createGain();
    this.duck.connect(this.output);
    // One short atlas carries every one-shot; individual ambience beds load only on demand.
    for (const clips of Object.values(this.manifest.oneshots)) for (const clip of clips ?? []) this.load(clip.file);
  }

  private load(file: string): void {
    if (this.disposed || this.buffers.has(file) || this.loads.has(file) || this.failed.has(file)) return;
    const pending = this.fetchBytes(this.base + file).then((bytes) => {
      if (this.disposed) return null;
      return new Promise<AudioBuffer>((resolve, reject) => {
        const decoding = this.context.decodeAudioData(bytes, resolve, reject) as Promise<AudioBuffer> | undefined;
        if (decoding) decoding.then(resolve, reject);
      });
    }).then((buffer) => {
      if (buffer && !this.disposed) {
        let stored = buffer;
        const oneShot = Object.values(this.manifest.oneshots).some((clips) => clips?.some((clip) => clip.file === file));
        if (oneShot && buffer.numberOfChannels > 1) {
          // Stereo delivery avoids codec priming differences; reactions still enter the panner as mono.
          stored = this.context.createBuffer(1, buffer.length, buffer.sampleRate);
          const mono = stored.getChannelData(0);
          const channels = Array.from({ length: buffer.numberOfChannels }, (_, channel) => buffer.getChannelData(channel));
          for (let frame = 0; frame < mono.length; frame++) {
            let sum = 0;
            for (const channel of channels) sum += channel[frame]!;
            mono[frame] = sum / channels.length;
          }
        }
        this.buffers.set(file, stored);
        if (Object.values(this.manifest.beds).some((clip) => clip?.file === file)) {
          this.bedFiles.push(file);
          while (this.bedFiles.length > MAX_BEDS) {
            const oldest = this.bedFiles.shift()!;
            if (oldest === this.bed?.file) this.bedFiles.push(oldest);
            else this.buffers.delete(oldest);
          }
        }
      }
    }).catch(() => { if (!this.disposed) this.failed.add(file); }).finally(() => {
      this.loads.delete(file);
      if (!this.disposed) { this.ensureBed(); this.notifyCoverage(); }
    });
    this.loads.set(file, pending);
  }

  /** User/run edges can recover a flaky download; ordinary frames and volume changes never retry. */
  private retryFailed(): void {
    if (this.disposed || this.master <= 0 || this.scene !== 'run') return;
    const files = new Set<string>();
    for (const clips of Object.values(this.manifest.oneshots)) for (const clip of clips ?? []) files.add(clip.file);
    const bed = this.manifest.beds[this.zone];
    if (bed) files.add(bed.file);
    for (const file of files) {
      if (!this.failed.delete(file)) continue;
      this.load(file);
    }
  }

  private notifyCoverage(): void {
    const kinds = [...FAMILY].filter(([, family]) => this.manifest.oneshots[family]?.some((clip) => this.buffers.has(clip.file))).map(([kind]) => kind);
    this.coverage({ kinds, ambience: this.bed !== null && this.scene === 'run' && this.master > 0 });
  }

  handles(kind: number): boolean {
    return !!this.manifest.oneshots[FAMILY.get(kind) ?? '']?.some((clip) => this.buffers.has(clip.file));
  }

  /** True only when scheduled: callers suppress that procedural transient, never a pending load. */
  playTransient(transient: Transient): boolean {
    if (this.disposed || this.master <= 0) return false;
    const clips = this.manifest.oneshots[FAMILY.get(transient.kind) ?? '']?.filter((clip) => this.buffers.has(clip.file));
    if (!clips?.length) return false;
    const count = this.counters.get(transient.kind) ?? 0;
    const clip = clips[count % clips.length]!;
    const buffer = this.buffers.get(clip.file)!;
    if (!(clip.duration > 0) || clip.start < 0 || clip.start + clip.duration > buffer.duration + 0.01) return false;
    while (this.shots.size >= MAX_VOICES) this.stop(this.shots.values().next().value!);
    let voice: Voice;
    try { voice = this.makeVoice(buffer, clamp(transient.pan * 0.5 + 0.5) * 2 - 1); }
    catch { return false; }
    const when = this.context.currentTime + Math.max(0, Number.isFinite(transient.delay) ? transient.delay : 0);
    const level = clamp(transient.gain) * clip.gain;
    try {
      voice.gain.gain.setValueAtTime(0, when);
      voice.gain.gain.linearRampToValueAtTime(level, when + Math.min(0.008, clip.duration / 4));
      voice.gain.gain.setValueAtTime(level, when + Math.max(0.008, clip.duration - 0.025));
      voice.gain.gain.linearRampToValueAtTime(0, when + clip.duration);
      this.shots.add(voice);
      voice.source.onended = () => this.disconnect(voice);
      voice.source.start(when, clip.start, clip.duration);
    }
    catch { this.stop(voice); return false; }
    this.counters.set(transient.kind, count + 1);
    return true;
  }

  private makeVoice(buffer: AudioBuffer, pan: number): Voice {
    const source = this.context.createBufferSource();
    const gain = this.context.createGain();
    const panner = typeof this.context.createStereoPanner === 'function' ? this.context.createStereoPanner() : null;
    source.buffer = buffer;
    source.connect(gain);
    if (panner) { panner.pan.value = pan; gain.connect(panner); panner.connect(this.duck); }
    else gain.connect(this.duck);
    return { source, gain, pan: panner };
  }

  private ensureBed(): void {
    if (this.disposed || this.scene !== 'run' || this.master <= 0) return;
    const clip = this.manifest.beds[this.zone];
    if (!clip) return;
    const buffer = this.buffers.get(clip.file);
    if (!buffer) { this.load(clip.file); return; }
    if (this.bed?.file === clip.file) return;
    this.stopBed();
    if (clip.duration <= 0 || clip.start + clip.duration > buffer.duration + 0.01) return;
    let voice: Voice;
    try { voice = this.makeVoice(buffer, 0); }
    catch { return; }
    this.bed = { ...voice, file: clip.file };
    try {
      voice.source.loop = true;
      voice.source.loopStart = clip.start;
      voice.source.loopEnd = clip.start + clip.duration;
      voice.gain.gain.value = 0;
      voice.source.start(this.context.currentTime, clip.start);
    }
    catch { this.stopBed(); this.failed.add(clip.file); this.buffers.delete(clip.file); return; }
    const index = this.bedFiles.indexOf(clip.file);
    if (index >= 0) this.bedFiles.splice(index, 1);
    this.bedFiles.push(clip.file);
    while (this.bedFiles.length > MAX_BEDS) this.buffers.delete(this.bedFiles.shift()!);
    this.notifyCoverage();
  }

  update(params: AudioParams): void {
    if (this.disposed) return;
    this.ambientGain = clamp(params.ambientGain);
    const duckDb = Number.isFinite(params.duckDb) ? Math.max(0, Math.min(24, params.duckDb)) : 0;
    this.duck.gain.setTargetAtTime(Math.pow(10, -duckDb / 20), this.context.currentTime, 0.015);
    this.ensureBed();
    const clip = this.manifest.beds[this.zone];
    this.bed?.gain.gain.setTargetAtTime(this.ambientGain * (clip?.gain ?? 0), this.context.currentTime, 0.2);
  }

  setZone(zone: MusicZone): void {
    if (zone !== this.zone) { this.zone = zone; this.stopBed(); }
    this.ensureBed();
    this.notifyCoverage();
  }

  setScene(scene: AudioScene): void {
    if (scene === this.scene) return;
    this.scene = scene;
    if (scene !== 'run') { this.restart(false); this.stopBed(); }
    else { this.retryFailed(); this.ensureBed(); }
    this.notifyCoverage();
  }

  setVolume(volume: number): void {
    if (this.disposed) return;
    this.master = clamp(volume);
    this.output.gain.setTargetAtTime(this.master, this.context.currentTime, 0.008);
    if (this.master === 0) { this.restart(false); this.stopBed(); }
    else this.ensureBed();
    this.notifyCoverage();
  }

  /** Hard stop reactions and retry failed active-run files. Passive cleanup passes false. */
  restart(retryFailed = true): void {
    for (const voice of [...this.shots]) this.stop(voice);
    this.counters.clear();
    if (retryFailed) this.retryFailed();
  }
  private disconnect(voice: Voice): void {
    this.shots.delete(voice);
    voice.source.disconnect(); voice.gain.disconnect(); voice.pan?.disconnect();
  }
  private stop(voice: Voice): void {
    voice.source.onended = null;
    try { voice.source.stop(); } catch { /* already ended */ }
    this.disconnect(voice);
  }
  private stopBed(): void {
    if (this.bed) this.stop(this.bed);
    this.bed = null;
  }
  dispose(): void {
    if (this.disposed) return;
    this.disposed = true;
    this.restart(false); this.stopBed(); this.duck.disconnect(); this.output.disconnect();
    this.buffers.clear(); this.loads.clear(); this.failed.clear();
    this.notifyCoverage();
  }
}
