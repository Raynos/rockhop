/**
 * WebAudioSystem — the live AudioSystem.
 *
 * iOS Safari rules baked in:
 *  - the AudioContext is created *synchronously* inside `unlock()` (call it
 *    from the first touch/key handler, before any await);
 *  - `resume()` is retried on every later `unlock()` call and on statechange
 *    (Safari suspends/interrupts on phone calls, tab switches, silent switch);
 *  - AudioWorklet is tried first; if `addModule` throws or times out the
 *    oscillator-bank FallbackGraph takes over with the same param stream.
 *
 * The engine, tyres, crowd, stingers and the procedural bed live in the model + synth; this file moves
 * a Float32Array per frame. The recorded music (src/audio/music) is the one exception: AudioBuffers
 * on the same context, beside the synth, created with the backend (so never before the first gesture
 * and never under automation), ducked under the engine from the model's own load / engine gain.
 */
import type { BikeClass, CompiledTrack, GameEvent, InputFrame, PhysicsState } from '../../core/types';
import type { PhysicsFactory } from '../../physics';
import type { AudioSystem } from '../index';
import { ModelDriver, silenceGameplay, type AudioScene } from '../driver';
import type { OfflineOptions } from '../offline';
import { FallbackGraph } from './fallback';
import { silentAutomation } from '../automation';
import { MusicPlayer, type MusicPlayerOptions } from '../music/player';
import { zoneOf, type MusicZone } from '../music/zone';
import { SCENE_MENU, SCENE_RESULTS } from '../model/mapParams';
import { P_HEADER, P_TRANSIENT_COUNT, P_TRANSIENT_STRIDE, P_SCENE } from '../params';
import { SamplePlayer, type SamplePlayerOptions } from '../samples/player';

const WORKLET_NAME = 'rockhop-synth';

export interface WebAudioOptions {
  /** Inject a context (tests / OfflineAudioContext). Default: new AudioContext in unlock(). */
  context?: AudioContext;
  /** Force the oscillator-bank fallback (debug / low tier). */
  forceFallback?: boolean;
  /** Physics factory for renderOffline(); without it renderOffline is undefined. */
  makePhysics?: PhysicsFactory;
  offline?: OfflineOptions;
  /** ms to wait for the worklet module before falling back (default 4000). */
  workletTimeoutMs?: number;
  /** Recorded music: false = procedural bed only; an object overrides the player (tests: cues, fetch). */
  music?: boolean | Omit<MusicPlayerOptions, 'onBed'>;
  /** Recorded reactions and biome beds; failed files leave each procedural family available. */
  samples?: boolean | Omit<SamplePlayerOptions, 'onCoverage'>;
}

/**
 * Music ducking under the engine (dB): the ride loop gives way as the throttle opens —
 * 1 dB at a closed throttle, 4 dB wide open; nothing when the engine bus is silent (crash, menu).
 */
export function engineDuckDb(engineGain: number, load: number): number {
  const g = Math.max(0, Math.min(1, engineGain));
  return g * (1 + 3 * Math.max(0, Math.min(1, load)));
}

type Backend = { kind: 'worklet'; node: AudioWorkletNode } | { kind: 'fallback'; graph: FallbackGraph };

export class WebAudioSystem implements AudioSystem {
  readonly driver = new ModelDriver();
  private ctx: AudioContext | null = null;
  private backend: Backend | null = null;
  private mix: DynamicsCompressorNode | null = null;
  private gameplay: GainNode | null = null;
  private paused = false;
  private unlocking: Promise<void> | null = null;
  private master = 1;
  private disposed = false;
  private track: CompiledTrack | null = null;
  private seed = 0;
  private onVisibility: (() => void) | null = null;
  private music: MusicPlayer | null = null;
  private samples: SamplePlayer | null = null;
  private appScene: AudioScene | null = null;
  private zone: MusicZone | null = null;
  private musicVolume = 1;
  readonly renderOffline: ((recordingJson: string, seconds: number) => Promise<Float32Array>) | undefined;

  constructor(private readonly opts: WebAudioOptions = {}) {
    // The offline renderer runs the whole DSP on the main thread: a harness hook (`__rockhop.audio.renderOffline`),
    // never a player path (the player's DSP is the worklet asset). Loaded on first call, it keeps the synth out
    // of the entry chunk.
    const makePhysics = opts.makePhysics;
    if (makePhysics) {
      this.renderOffline = async (json, seconds) => (await import('../offline')).createOfflineRenderer(makePhysics, opts.offline ?? {})(json, seconds);
    }
  }

  /** 'worklet' | 'fallback' | null (not unlocked yet). */
  get backendKind(): Backend['kind'] | null {
    return this.backend?.kind ?? null;
  }

  get context(): AudioContext | null {
    return this.ctx;
  }

  /** Optional (additive): the game calls this from loadTrack so biome + seed follow the track. */
  setTrack(track: CompiledTrack, seed: number): void {
    this.track = track;
    this.seed = seed >>> 0;
    this.zone = zoneOf(track);
    this.music?.setZone(this.zone);
    this.samples?.setZone(this.zone);
    this.driver.setTrack(track, this.seed);
    if (this.backend?.kind === 'worklet') {
      this.backend.node.port.postMessage({ seed: this.seed });
      this.postScene();
    }
  }

  /** Optional (additive): the class the physics was loaded with (Game.setBike / loadTrack). Voicing only. */
  setBike(bike: BikeClass): void {
    this.driver.setBike(bike);
  }

  /**
   * Optional (additive): the app's screen, for the music bed — 'menu' (front end, garage, track select),
   * 'results', or 'run'. Without it the bed is inferred: menu until the first countdown, results 1.4 s
   * after a finish, run again on the next restart. Pass null to return to inference.
   */
  setScene(scene: AudioScene | null): void {
    this.appScene = scene;
    this.driver.setScene(scene);
    this.postScene();
  }

  private frontScene(): boolean {
    const scene = this.musicScene();
    return scene === 'menu' || scene === 'map';
  }

  private gameplayPaused(): boolean {
    return this.paused && !this.frontScene();
  }

  setPaused(paused: boolean): void {
    if (paused === this.paused) return;
    this.paused = paused;
    this.syncPause();
    if (this.gameplayPaused()) {
      this.driver.flush();
      this.samples?.restart(false);
      this.music?.setDuckDb(0);
      if (this.backend?.kind === 'fallback') this.backend.graph.cancelShots();
      else this.backend?.node.port.postMessage({ paused: true });
    }
  }

  private syncPause(): void {
    const context = this.ctx;
    if (this.gameplay && context) this.gameplay.gain.setTargetAtTime(this.gameplayPaused() ? 0 : 1, context.currentTime, 0.008);
  }

  /** The music-only slider (0..1). Scales the recorded cues; the master scales everything. */
  setMusicVolume(v: number): void {
    this.musicVolume = Math.max(0, Math.min(1, v));
    this.music?.setMusicVolume(this.musicVolume);
    if (this.backend?.kind === 'worklet') this.backend.node.port.postMessage({ musicVolume: this.musicVolume * this.musicVolume });
  }

  /** The recorded-music player, once the context exists (null before the first gesture / under automation). */
  get musicPlayer(): MusicPlayer | null {
    return this.music;
  }

  /** The scene the music follows: the app's word when it gave one, else the model's inference. */
  private musicScene(): AudioScene {
    if (this.appScene) return this.appScene;
    const s = this.driver.scene;
    return s === SCENE_MENU ? 'menu' : s === SCENE_RESULTS ? 'results' : 'run';
  }

  private postScene(): void {
    const b = this.backend;
    if (b?.kind === 'worklet') b.node.port.postMessage({ scene: this.driver.scene });
    this.music?.setScene(this.musicScene(), this.zone ?? undefined);
    this.samples?.setScene(this.musicScene());
    this.syncPause();
    if (this.musicScene() !== 'run' && b) {
      const packed = this.driver.packed;
      silenceGameplay(packed);
      packed[P_TRANSIENT_COUNT] = 0;
      packed[P_SCENE] = this.driver.scene;
      if (b.kind === 'worklet') b.node.port.postMessage(packed);
      else b.graph.setParams(packed);
      if (this.frontScene()) {
        this.driver.flush();
        if (b.kind === 'fallback') b.graph.cancelShots();
        else b.node.port.postMessage({ paused: true }); // drop delayed gameplay reactions
      }
    }
  }

  get samplePlayer(): SamplePlayer | null {
    return this.samples;
  }

  private postBed(on: boolean): void {
    const b = this.backend;
    if (b?.kind === 'worklet') b.node.port.postMessage({ bed: on });
  }

  unlock(): Promise<void> {
    if (this.disposed) return Promise.resolve();
    if (!this.ctx && !this.opts.context && silentAutomation()) return Promise.resolve();
    if (!this.ctx) {
      // iOS: an ambient session — the silent switch mutes the game and other apps' audio keeps playing
      // (Safari 17+ / WKWebView; the native shells also set it, store release Phase 5).
      try {
        const session = (navigator as Navigator & { audioSession?: { type: string } }).audioSession;
        if (session) session.type = 'ambient';
      } catch {
        /* not supported */
      }
      // Synchronous creation inside the gesture — this is the iOS requirement.
      try {
        this.ctx = this.opts.context ?? new AudioContext({ latencyHint: 'interactive' });
      } catch {
        return Promise.resolve();
      }
      const ctx = this.ctx;
      const kick = (): void => {
        if (this.disposed || this.ctx !== ctx) return;
        if ((ctx.state as string) === 'interrupted' || ctx.state === 'suspended') void ctx.resume().catch(() => undefined);
      };
      // Safari suspends/interrupts on phone calls, tab switches and the lock screen; resume
      // when the state flips and again when the page becomes visible (iOS needs the latter).
      ctx.onstatechange = kick;
      if (typeof document !== 'undefined') {
        this.onVisibility = () => {
          if (document.visibilityState === 'visible') kick();
        };
        document.addEventListener('visibilitychange', this.onVisibility);
      }
    }
    const ctx = this.ctx;
    // Kick resume() synchronously inside the gesture as well.
    if (ctx.state !== 'running') void ctx.resume().catch(() => undefined);
    if (this.backend) return Promise.resolve();
    if (!this.unlocking) this.unlocking = this.buildBackend(ctx).finally(() => (this.unlocking = null));
    return this.unlocking;
  }

  private async buildBackend(ctx: AudioContext): Promise<void> {
    // The synth limiter cannot see recorded music or samples: protect their summed mix too.
    const mix = ctx.createDynamicsCompressor();
    mix.threshold.value = -2.5;
    mix.knee.value = 0;
    mix.ratio.value = 20;
    mix.attack.value = 0.003;
    mix.release.value = 0.08;
    mix.connect(ctx.destination);
    this.mix = mix;
    const gameplay = ctx.createGain();
    gameplay.gain.value = 0; // no unconfigured startup quantum reaches the shared mix
    gameplay.connect(mix);
    this.gameplay = gameplay;
    let backend: Backend | null = null;
    if (!this.opts.forceFallback && typeof ctx.audioWorklet?.addModule === 'function') {
      try {
        let timeoutId: ReturnType<typeof setTimeout> | undefined;
        const timeout = new Promise<never>((_, reject) => {
          timeoutId = setTimeout(() => reject(new Error('worklet timeout')), this.opts.workletTimeoutMs ?? 4000);
        });
        try {
          await Promise.race([
            (async () => {
              // Vite bundles the DSP as its own worklet asset; the timeout includes importing it.
              const mod = (await import('./worklet?worker&url' as string)) as { default: string };
              await ctx.audioWorklet.addModule(mod.default);
            })(),
            timeout,
          ]);
        } finally {
          clearTimeout(timeoutId);
        }
        if (this.disposed) return;
        const node = new AudioWorkletNode(ctx, WORKLET_NAME, {
          numberOfInputs: 0,
          numberOfOutputs: 1,
          outputChannelCount: [2],
        });
        node.connect(gameplay);
        node.port.postMessage({ seed: this.seed });
        node.port.postMessage({ master: this.master });
        node.port.postMessage({ musicVolume: this.musicVolume * this.musicVolume });
        node.port.postMessage({ scene: this.driver.scene });
        backend = { kind: 'worklet', node };
      } catch {
        backend = null;
      }
    }
    if (this.disposed) return;
    if (!backend) {
      const graph = new FallbackGraph(ctx, gameplay);
      graph.setMaster(this.master);
      backend = { kind: 'fallback', graph };
    }
    if (this.disposed) {
      if (backend.kind === 'fallback') backend.graph.dispose();
      else {
        backend.node.port.postMessage({ stop: true });
        backend.node.disconnect();
      }
      return;
    }
    this.backend = backend;
    if (this.track) this.driver.setTrack(this.track, this.seed);
    if (this.opts.music !== false) {
      const mo = typeof this.opts.music === 'object' ? this.opts.music : {};
      try {
        this.music = new MusicPlayer(ctx, mix, { ...mo, onBed: (on) => this.postBed(on) });
        this.music.setVolume(this.master);
        this.music.setMusicVolume(this.musicVolume);
        this.music.setScene(this.musicScene(), this.zone ?? undefined);
      } catch {
        this.music = null; // the procedural bed stays
      }
    }
    if (this.opts.samples !== false) {
      const sampleOptions = typeof this.opts.samples === 'object' ? this.opts.samples : {};
      try {
        this.samples = new SamplePlayer(ctx, gameplay, {
          ...sampleOptions,
          onCoverage: ({ ambience }) => {
            if (this.backend?.kind === 'worklet') this.backend.node.port.postMessage({ ambience: !ambience });
          },
        });
        this.samples.setVolume(this.master);
        this.samples.setZone(this.zone ?? 'coast');
        this.samples.setScene(this.musicScene());
      } catch {
        this.samples = null;
      }
    }
    this.postScene();
  }

  update(state: PhysicsState, dt: number, input?: Readonly<InputFrame>): void {
    if (this.gameplayPaused()) {
      this.driver.flush();
      return;
    }
    const packed = this.driver.update(state, dt, input);
    const m = this.music;
    if (m) {
      const p = this.driver.params;
      m.setDuckDb(this.driver.scene === SCENE_MENU || this.driver.scene === SCENE_RESULTS ? 0 : engineDuckDb(p.engineGain, p.load));
      if (!this.appScene) m.setScene(this.musicScene(), this.zone ?? undefined);
    }
    if (this.musicScene() !== 'run') silenceGameplay(packed);
    if (this.frontScene()) {
      packed[P_TRANSIENT_COUNT] = 0;
      this.driver.params.transientCount = 0;
    }
    const b = this.backend;
    if (b && this.ctx && this.ctx.state === 'running') {
      const samples = this.samples;
      if (samples) {
        if (!this.appScene) samples.setScene(this.musicScene());
        samples.update(this.driver.params);
        // Compact the already-packed queue only when a recorded voice actually starts.
        // Pending/failed files keep their synth voice, with its original sample-accurate delay.
        let retained = 0;
        const params = this.driver.params;
        for (let i = 0; i < params.transientCount; i++) {
          if (samples.playTransient(params.transients[i]!)) continue;
          const from = P_HEADER + i * P_TRANSIENT_STRIDE;
          const to = P_HEADER + retained++ * P_TRANSIENT_STRIDE;
          if (from !== to) packed.copyWithin(to, from, from + P_TRANSIENT_STRIDE);
        }
        packed[P_TRANSIENT_COUNT] = retained;
      }
      if (b.kind === 'worklet') b.node.port.postMessage(packed);
      else b.graph.setParams(packed);
    }
    this.driver.flush();
  }

  onEvent(event: GameEvent): void {
    const before = this.driver.scene;
    if (event.type === 'restart') this.samples?.restart();
    this.driver.onEvent(event);
    // scene edges from events reach the worklet even when no frame follows (finish → results in the menu-less case)
    if (this.driver.scene !== before) this.postScene();
  }

  setMasterVolume(v: number): void {
    const p = Math.max(0, Math.min(1, v));
    this.master = p * p; // perceptual
    this.music?.setVolume(this.master);
    this.samples?.setVolume(this.master);
    const b = this.backend;
    if (!b) return;
    if (b.kind === 'worklet') b.node.port.postMessage({ master: this.master });
    else b.graph.setMaster(this.master);
  }

  dispose(): void {
    this.disposed = true;
    if (this.onVisibility && typeof document !== 'undefined') document.removeEventListener('visibilitychange', this.onVisibility);
    this.onVisibility = null;
    const b = this.backend;
    if (b?.kind === 'worklet') {
      b.node.port.postMessage({ stop: true });
      b.node.disconnect();
    } else if (b?.kind === 'fallback') b.graph.dispose();
    this.backend = null;
    this.music?.dispose();
    this.music = null;
    this.samples?.dispose();
    this.samples = null;
    this.gameplay?.disconnect();
    this.gameplay = null;
    this.mix?.disconnect();
    this.mix = null;
    if (this.ctx && !this.opts.context) void this.ctx.close().catch(() => undefined);
    if (this.ctx) this.ctx.onstatechange = null;
    this.ctx = null;
  }
}
