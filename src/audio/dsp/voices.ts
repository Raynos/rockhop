/**
 * One-shot voice pool and recipes. A voice = up to 4 gliding partials + one
 * filtered noise layer (+ optional grunt formants) under an A/H/D envelope,
 * with a start delay, a bus (0 chassis / 1 ui / 2 ambient) and a reverb send.
 * Recipes are pure functions of (kind, gain, pitch, pan).
 * Each event has its own noise seed and resets pooled filter/color state;
 * physical contact modes follow eight materials and all cue tails fade out.
 */
import { Biquad, NoiseColour, NoiseRng, bandLimitedSaw, clamp, dbToGain, decayCoef, glottalPulse, panGains, sineCycle } from './util';

export const BUS_CHASSIS = 0;
export const BUS_UI = 1;
export const BUS_AMBIENT = 2;

const MAX_PARTIALS = 4;
const KILL_S = 0.005;
// the stinger family's key (D): D5 / A5 / D6
const D5 = 587.33;
const A5 = 880;
const D6 = 1174.66;

class Voice {
  active = false;
  bus = 0;
  send = 0;
  delay = 0; // samples until onset
  t = 0; // samples since onset
  gl = 1;
  gr = 0;
  gain = 1;
  att = 1;
  hold = 0;
  dec = 1;
  env = 0;
  life = 0;
  fadeFrom = 0;
  fadeStep = 1;
  killing = false;
  killStep = 0;
  killGain = 1;
  // partials
  np = 0;
  readonly pAmp = new Float64Array(MAX_PARTIALS);
  readonly pDecay = new Float64Array(MAX_PARTIALS);
  readonly pF = new Float64Array(MAX_PARTIALS);
  readonly pFEnd = new Float64Array(MAX_PARTIALS);
  readonly pGlide = new Float64Array(MAX_PARTIALS);
  readonly pPhase = new Float64Array(MAX_PARTIALS);
  readonly pWave = new Uint8Array(MAX_PARTIALS); // 0 sine 1 band-limited saw 2 triangle 3 glottal
  readonly pDelay = new Float64Array(MAX_PARTIALS); // onset offset samples (for arpeggios)
  // noise
  nAmp = 0;
  nDecay = 1;
  nColour = 0; // 0 white 1 pink 2 brown
  nFilter = 0; // 0 none 1 lp 2 bp 3 hp
  nF = 1000;
  nFEnd = 1000;
  nGlide = 0;
  nQ = 1;
  nAtt = 1; // samples of noise-only attack (whooshes)
  readonly nBq: Biquad;
  readonly colour = new NoiseColour();
  readonly rng = new NoiseRng(1);
  glottalJitter = 1;
  glottalShimmer = 1;
  // grunt formants
  formant = false;
  readonly f1: Biquad;
  readonly f2: Biquad;
  readonly f3: Biquad;
  readonly flp: Biquad;
  // amplitude modulation (creak) — Hz, depth
  amHz = 0;
  amDepth = 0;
  amPhase = 0;
  // gating (cricket)
  gateHz = 0;
  gateDuty = 1;
  gatePhase = 0;

  constructor(sr: number) {
    this.nBq = new Biquad(sr);
    this.f1 = new Biquad(sr);
    this.f2 = new Biquad(sr);
    this.f3 = new Biquad(sr);
    this.flp = new Biquad(sr);
    this.flp.lowpass(1200, 0.7);
  }
}

export interface Trigger {
  kind: number;
  gain: number;
  pitch: number;
  pan: number;
  delay: number;
}

export class VoicePool {
  private readonly sr: number;
  /**
   * Per-event variation (round 4): reseeded on every trigger from (seed, kind, occurrence index), so the second
   * crash / landing / respawn of a run never replays the first (the critics heard the identical impact sequence
   * twice, r = 0.67) while a recording still renders byte-identically.
   */
  private readonly vary: NoiseRng;
  private readonly varySeed: number;
  private readonly counts = new Uint32Array(128);
  private phased = false;
  private eventNoiseSeed = 1;
  private eventNoiseLayer = 0;
  private readonly voices: Voice[] = [];
  private readonly pg: [number, number] = [1, 0];
  /** Ordered onset log (sample index of first non-delayed sample), for tests. */
  readonly onsetLog: { kind: number; sample: number }[] = [];
  logOnsets = false;
  private sampleClock = 0;

  constructor(sr: number, seed: number, size = 16) {
    this.sr = sr;
    this.vary = new NoiseRng(seed ^ 0x51ed);
    this.varySeed = seed;
    for (let i = 0; i < size; i++) this.voices.push(new Voice(sr));
  }

  get activeCount(): number {
    let n = 0;
    for (const v of this.voices) if (v.active) n++;
    return n;
  }

  /** Hard-stop every voice on the given buses within 5 ms and drop pending ones. */
  killBuses(chassis: boolean, ui: boolean, ambient = false): void {
    for (const v of this.voices) {
      if (!v.active) continue;
      if ((v.bus === BUS_CHASSIS && chassis) || (v.bus === BUS_UI && ui) || (v.bus === BUS_AMBIENT && ambient)) {
        if (v.t === 0 && v.delay > 0) {
          v.active = false;
          continue;
        }
        v.killing = true;
        v.killStep = 1 / Math.max(1, KILL_S * this.sr);
      }
    }
  }

  private alloc(): Voice {
    let best: Voice | null = null;
    let oldest = -1;
    for (const v of this.voices) {
      if (!v.active) return this.blank(v);
      if (v.t > oldest) {
        oldest = v.t;
        best = v;
      }
    }
    return this.blank(best!);
  }

  private blank(v: Voice): Voice {
    v.active = true;
    v.bus = BUS_CHASSIS;
    v.send = 0;
    v.delay = 0;
    v.t = 0;
    v.gain = 1;
    v.att = 1;
    v.hold = 0;
    v.dec = 1;
    v.env = 0;
    v.life = this.sr * 2;
    v.killing = false;
    v.killGain = 1;
    v.np = 0;
    v.pDelay.fill(0);
    v.rng.reseed(this.eventNoiseSeed ^ Math.imul(++this.eventNoiseLayer, 0x27d4eb2d));
    v.colour.reset();
    v.nAmp = 0;
    v.nDecay = 1;
    v.nColour = 0;
    v.nFilter = 0;
    v.nGlide = 0;
    v.nAtt = 1;
    v.nQ = 1;
    v.nBq.reset();
    v.f1.reset();
    v.f2.reset();
    v.f3.reset();
    v.flp.reset();
    v.glottalJitter = v.glottalShimmer = 1;
    v.formant = false;
    v.amHz = 0;
    v.amDepth = 0;
    v.amPhase = 0;
    v.gateHz = 0;
    v.gateDuty = 1;
    v.gatePhase = 0;
    return v;
  }

  private partial(v: Voice, amp: number, f: number, fEnd: number, glideS: number, decayS: number, wave = 0, delayS = 0): void {
    if (v.np >= MAX_PARTIALS) return;
    const i = v.np++;
    v.pAmp[i] = amp;
    v.pF[i] = clamp(f, 10, this.sr * 0.44);
    v.pFEnd[i] = clamp(fEnd, 10, this.sr * 0.44);
    v.pGlide[i] = glideS > 0 ? 1 - Math.exp(-1 / (glideS * this.sr * 0.3)) : 1;
    v.pDecay[i] = decayCoef(decayS, this.sr);
    // round 4: a per-event start phase for the physical one-shots — two hits of the same recipe never line up
    // sample for sample; the UI stinger family keeps phase 0 (a synth stab is phase-coherent by design)
    v.pPhase[i] = this.phased ? this.vary.u() : 0;
    v.pWave[i] = wave;
    v.pDelay[i] = Math.round(delayS * this.sr);
  }

  private noise(v: Voice, amp: number, decayS: number, colour: number, filter: number, f: number, q: number, fEnd = f, glideS = 0, attS = 0): void {
    v.nAmp = amp;
    v.nDecay = decayCoef(decayS, this.sr);
    v.nColour = colour;
    v.nFilter = filter;
    v.nF = f;
    v.nFEnd = fEnd;
    v.nQ = q;
    v.nGlide = glideS > 0 ? 1 - Math.exp(-1 / (glideS * this.sr * 0.3)) : 1;
    v.nAtt = Math.max(1, Math.round(attS * this.sr));
  }

  private env(v: Voice, attS: number, holdS: number, decayS: number, lifeS: number): void {
    v.att = Math.max(1, Math.round(attS * this.sr));
    v.hold = Math.round(holdS * this.sr);
    v.dec = decayCoef(decayS, this.sr);
    v.life = Math.round(lifeS * this.sr);
    v.fadeFrom = Math.max(0, v.life - Math.round(0.008 * this.sr));
    v.fadeStep = 1 / Math.max(1, v.life - v.fadeFrom);
  }

  private finish(v: Voice, gainDb: number, gain: number, pan: number, delayS: number, bus: number, send = 0): void {
    v.gain = dbToGain(gainDb) * gain;
    panGains(pan, this.pg);
    v.gl = this.pg[0];
    v.gr = this.pg[1];
    v.delay = Math.max(0, Math.round(delayS * this.sr));
    v.bus = bus;
    v.send = send;
  }

  // ---------------------------------------------------------------------------
  // Recipes (kind indices match params.TRANSIENT_KINDS)
  // ---------------------------------------------------------------------------

  /** 1 ± amt, from the per-event stream. */
  private v(amt: number): number {
    return 1 + amt * this.vary.n();
  }

  trigger(tr: Trigger): void {
    const { kind, gain, pitch, pan, delay } = tr;
    const surf = Math.round(pitch * 8);
    const k = kind & 127;
    const occurrence = this.counts[k]!;
    this.counts[k] = occurrence + 1;
    this.eventNoiseSeed = this.varySeed ^ Math.imul(kind + 1, 0x9e3779b1) ^ Math.imul(occurrence + 1, 0x85ebca77);
    this.eventNoiseLayer = 0;
    this.vary.reseed(this.eventNoiseSeed);
    this.phased = kind <= 8 || kind === 19 || kind === 20 || (kind >= 25 && kind <= 27) || kind >= 100;
    switch (kind) {
      case 0: // landing
        this.landing(gain, surf, pan, delay);
        break;
      case 1: // thunk
        this.landing(gain * 0.5, 0, pan, delay);
        break;
      case 27: {
        // tyre scrub after a touchdown (round 4): 1–4 kHz rubber scrubbing that rises with speed, a 40–55 Hz chatter
        const v = this.alloc();
        this.noise(v, 1, 0.16 + 0.16 * pitch, 0, 2, (1400 + 1800 * pitch) * this.v(0.12), 0.8);
        v.amHz = 48 * this.v(0.2);
        v.amDepth = 0.45;
        this.env(v, 0.008, 0.04, 0.2 + 0.1 * pitch, 0.6);
        this.finish(v, -21 + 7 * pitch, gain, pan, delay, BUS_CHASSIS, 0.05);
        break;
      }
      case 2: {
        // bottomOut (v2): the rear on its bump stop — a deep, dull stop knock (every drop >= 1 m does this and
        // rides away, so it must not read as a failure clang); the ring only on metal / grate
        const v = this.alloc();
        this.partial(v, 1, 160, 70, 0.04, 0.12);
        this.partial(v, 0.35, 1100, 1100, 0, 0.04);
        this.noise(v, 0.6, 0.02, 0, 2, 700, 1);
        this.env(v, 0.001, 0.005, 0.14, 0.3);
        this.finish(v, -3, gain, pan, delay, BUS_CHASSIS, 0.12);
        if (surf === 2 || surf === 5) {
          const r = this.alloc();
          this.partial(r, 1, 2200, 2200, 0, 0.14);
          this.partial(r, 0.6, 3100, 3100, 0, 0.1);
          this.env(r, 0.001, 0, 0.16, 0.3);
          this.finish(r, -22, gain, pan, delay, BUS_CHASSIS, 0.15);
        }
        this.landing(gain, surf, pan, delay);
        break;
      }
      case 3: {
        // impact (round 4: every partial, decay and ring detuned per event)
        const v = this.alloc();
        this.partial(v, 0.8, 95 * this.v(0.32), 40 * this.v(0.35), 0.12 * this.v(0.4), 0.25 * this.v(0.3));
        this.noise(v, 1.1, 0.1 * this.v(0.3), 0, 2, 800 * this.v(0.35), 0.7);
        this.env(v, 0.001, 0, 0.3 * this.v(0.2), 0.6);
        this.finish(v, -10, gain, pan, delay, BUS_CHASSIS, 0.2);
        const r = this.alloc();
        const det = (1 + (pitch - 0.5) * 0.008) * this.v(0.05);
        this.partial(r, 1, 1320 * det, 1320 * det, 0, 0.42 * this.v(0.3));
        this.partial(r, 0.7, 2070 * det * this.v(0.03), 2070 * det, 0, 0.3 * this.v(0.3));
        this.partial(r, 0.5, 3410 * det * this.v(0.04), 3410 * det, 0, 0.2 * this.v(0.3));
        this.env(r, 0.001, 0, 0.45, 0.8);
        this.finish(r, -22, gain, pan, delay + 0.004 * this.vary.u(), BUS_CHASSIS, 0.3);
        break;
      }
      case 4: {
        // debris grain
        const v = this.alloc();
        this.noise(v, 1, 0.012 * this.v(0.4), 0, 2, (1000 + 3000 * pitch) * this.v(0.2), 2);
        this.env(v, 0.0005, 0.004, 0.012, 0.05);
        this.finish(v, -24, gain, pan, delay, BUS_CHASSIS, 0.1);
        break;
      }
      case 5: {
        // grunt: glottal saw → formants
        const v = this.alloc();
        const second = pitch > 0.2;
        const f0 = (second ? 115 : 130) * this.v(0.08);
        const f1 = (second ? 90 : 95) * this.v(0.06);
        const len = (second ? 0.12 : 0.18) * this.v(0.2);
        this.partial(v, 2.2, f0, f1, len, 1, 3);
        v.formant = true;
        v.f1.bandpass(530 * this.v(0.08), 4);
        v.f2.bandpass(1080 * this.v(0.08), 5);
        v.f3.bandpass(2350 * this.v(0.04), 7);
        v.flp.lowpass(3800, 0.7);
        this.noise(v, 0.17, 0.18, 0, 2, 1100, 0.7);
        this.env(v, 0.008, 0.06, 0.14, len + 0.25);
        this.finish(v, -14, gain, pan, delay, BUS_CHASSIS, 0.1);
        break;
      }
      case 6: {
        // fault stamp: slap + sub tap (round 4: the sub's pitch, the slap's centre and decay vary per fault)
        const v = this.alloc();
        this.noise(v, 1, 0.03 * this.v(0.25), 0, 2, 2200 * this.v(0.15), 0.8);
        this.partial(v, 0.8, 60 * this.v(0.2), 60 * this.v(0.2), 0, 0.09 * this.v(0.3));
        this.env(v, 0.001, 0.01, 0.09, 0.25);
        this.finish(v, -10, gain, pan, delay, BUS_UI, 0.1);
        break;
      }
      case 7: {
        // tick: wood joint (surf 1) / drum ridge (surf 2)
        const v = this.alloc();
        if (surf === 2) {
          this.partial(v, 1, 1850 * this.v(0.06), 1850, 0, 0.06 * this.v(0.3));
          this.noise(v, 0.5, 0.003, 0, 3, 3000 * this.v(0.15), 0.7);
          this.env(v, 0.0005, 0, 0.06, 0.12);
          this.finish(v, -24, gain, pan, delay, BUS_CHASSIS);
        } else {
          this.noise(v, 1, 0.004 * this.v(0.3), 0, 2, 1500 * this.v(0.2), 2);
          this.partial(v, 0.5, 220 * this.v(0.15), 220, 0, 0.03 * this.v(0.3));
          this.env(v, 0.0005, 0, 0.03, 0.08);
          this.finish(v, -22, gain, pan, delay, BUS_CHASSIS);
        }
        break;
      }
      case 8: {
        // Rubber stick-slip: narrow resonant squeak over a short contact rasp.
        const v = this.alloc();
        this.partial(v, 0.55, 1700 * this.v(0.08), 930, 0.09, 0.2);
        this.partial(v, 0.18, 2350 * this.v(0.08), 1550, 0.06, 0.1);
        this.noise(v, 0.8, 0.07, 0, 2, 1800, 1.2);
        v.amHz = 72 * this.v(0.15);
        v.amDepth = 0.35;
        this.env(v, 0.005, 0, 0.08, 0.2);
        this.finish(v, -20, gain, pan, delay, BUS_CHASSIS);
        break;
      }
      case 9: {
        // countdown: one D5 stab of the family (the same brass as GO, the checkpoint and the fanfare)
        this.stab([D5], -14, 0.003, 0.04, 0.09, gain, pan, delay, 0.1);
        break;
      }
      case 10: // go
        this.goChord(-10, gain, pan, delay, true);
        break;
      case 11: {
        // checkpoint: A5 → D6 of the family (+90 ms) + flame-jet whoosh
        this.stab([A5], -15, 0.003, 0.03, 0.3, gain, pan, delay, 0.3);
        this.stab([D6, A5 * 0.5], -14, 0.003, 0.05, 0.35, gain, pan, delay + 0.09, 0.3);
        const w = this.alloc();
        this.noise(w, 1, 0.35, 0, 2, 400, 0.8, 1500, 0.3, 0.03);
        this.env(w, 0.03, 0.05, 0.35, 0.6);
        this.finish(w, -18, gain, pan, delay, BUS_UI, 0.2);
        break;
      }
      case 12: {
        // restart: hard stop + click + whoosh
        this.killBuses(true, true);
        const c = this.alloc();
        this.noise(c, 1, 0.002, 0, 2, 3000, 2);
        this.env(c, 0.0003, 0.001, 0.002, 0.02);
        this.finish(c, -20, gain, pan, delay + 0.001, BUS_UI);
        const w = this.alloc();
        this.noise(w, 1, 0.14, 0, 2, 400, 1, 4000, 0.18, 0.04);
        this.env(w, 0.04, 0, 0.14, 0.3);
        this.finish(w, -16, gain, pan, delay + 0.001, BUS_UI);
        break;
      }
      case 13: // finish tick
        this.goChord(-16, gain, pan, delay, false);
        break;
      case 14: {
        // fanfare note: D5 F#5 A5 D6 — the family in D, resolving into the results bed's key
        const notes = [D5, 739.99, A5, D6];
        const i = clamp(Math.round(pitch * 4), 0, 3);
        this.stab([notes[i]!, notes[i]! * 0.5], -12, 0.004, i === 3 ? 0.2 : 0.05, i === 3 ? 0.7 : 0.5, gain, pan, delay, 0.4);
        break;
      }
      case 15: {
        // firework pop
        const v = this.alloc();
        this.partial(v, 0.7, (240 + 100 * pitch) * this.v(0.1), 65, 0.035, 0.12);
        this.noise(v, 0.8, 0.35, 0, 1, 3400, 0.7);
        v.amHz = 43;
        v.amDepth = 0.65;
        this.env(v, 0.001, 0, 0.4, 0.7);
        this.finish(v, -18, gain, pan, delay, BUS_UI, 0.35);
        break;
      }
      case 16: {
        // crowd swell
        const v = this.alloc();
        this.noise(v, 1, 0.7, 1, 2, 1100, 0.5);
        this.env(v, 0.3, 0.5, 0.7, 1.8);
        this.finish(v, -24, gain, pan, delay, BUS_UI, 0.4);
        break;
      }
      case 17: {
        // hazard whoosh (fire / water)
        const v = this.alloc();
        this.noise(v, 1.3, 0.6, 1, 2, 480, 0.7, 2600, 0.4, 0.02);
        this.partial(v, 0.6, 50, 35, 0.3, 0.5);
        v.amHz = 19;
        v.amDepth = 0.45;
        this.env(v, 0.02, 0.1, 0.6, 1.0);
        this.finish(v, -12, gain, pan, delay, BUS_CHASSIS, 0.3);
        break;
      }
      case 18: // kill
        this.killBuses(true, true, true);
        break;
      case 19: {
        // starter: whir (chattering 90 Hz saw → LP) then the catch (a low thump); round 4: the whir's length,
        // pitch and chatter rate and the catch's moment vary per respawn
        const whirS = 0.22 * this.v(0.2);
        const v = this.alloc();
        this.partial(v, 1, 95 * this.v(0.08), 140 * this.v(0.08), 0.25, 0.3, 1);
        v.gateHz = 14 * this.v(0.12);
        v.gateDuty = 0.55;
        v.formant = true;
        v.f1.peaking(300 * this.v(0.1), 2, 4);
        v.f2.peaking(900 * this.v(0.1), 2, 2);
        v.f3.bypass();
        v.flp.lowpass(1600, 0.7);
        this.env(v, 0.02, whirS, 0.06, whirS + 0.2);
        this.finish(v, -22, gain, pan, delay, BUS_CHASSIS, 0.1);
        const c = this.alloc();
        this.partial(c, 1, 140 * this.v(0.1), 60, 0.08, 0.16 * this.v(0.2));
        this.noise(c, 0.5, 0.04, 2, 1, 500 * this.v(0.2), 0.7);
        this.env(c, 0.002, 0, 0.18, 0.35);
        this.finish(c, -16, gain, pan, delay + whirS + 0.04, BUS_CHASSIS, 0.1);
        break;
      }
      case 20: {
        // plank: board-joint thud — low knock + short click; brighter/harder with speed (pitch)
        const v = this.alloc();
        this.partial(v, 0.8, (210 + 40 * pitch) * this.v(0.08), 150, 0.03, 0.06);
        this.partial(v, 0.35, 440 * this.v(0.1), 430, 0.02, 0.035);
        this.noise(v, 0.5 + 0.5 * pitch, 0.006, 0, 2, 1200 + 1500 * pitch, 1.5);
        this.env(v, 0.0005, 0, 0.05, 0.1);
        this.finish(v, -21, gain, pan, delay, BUS_CHASSIS, 0.05);
        break;
      }
      case 25: {
        // the hop: pitch 0 = preload creak (rider + suspension loading), pitch 1 = the snap (spring release)
        if (pitch < 0.5) {
          const v = this.alloc();
          this.partial(v, 0.7, 190 * this.v(0.08), 150, 0.2, 0.25, 1);
          this.noise(v, 0.35, 0.18, 1, 2, 520, 2, 360, 0.2);
          v.amHz = 11;
          v.amDepth = 0.5;
          v.formant = true;
          v.f1.bypass();
          v.f2.bypass();
          v.f3.bypass();
          v.flp.lowpass(900, 0.7);
          this.env(v, 0.03, 0.12, 0.1, 0.35);
          this.finish(v, -28, gain, pan, delay, BUS_CHASSIS, 0.1);
        } else {
          const v = this.alloc();
          this.noise(v, 1, 0.014, 0, 2, 1100, 1.1);
          this.partial(v, 0.8, 140, 90, 0.03, 0.06);
          this.partial(v, 0.4, 480, 420, 0.06, 0.08);
          this.env(v, 0.001, 0.004, 0.07, 0.2);
          this.finish(v, -22, gain, pan, delay, BUS_CHASSIS, 0.1);
        }
        break;
      }
      case 26: {
        // ragdoll body thud: torso / pelvis (pitch 0) heavy and low, a limb (pitch 0.6) lighter and shorter
        const limb = pitch > 0.3;
        const v = this.alloc();
        this.partial(v, 1, (limb ? 140 : 90) * this.v(0.12), (limb ? 80 : 50) * this.v(0.1), 0.04, (limb ? 0.07 : 0.12) * this.v(0.25));
        this.noise(v, limb ? 0.5 : 0.8, (limb ? 0.02 : 0.03) * this.v(0.3), 2, 1, 400 * this.v(0.2), 0.7);
        this.env(v, 0.002, 0, limb ? 0.08 : 0.14, 0.3);
        this.finish(v, limb ? -18 : -14, gain, pan, delay, BUS_CHASSIS, 0.12);
        break;
      }
      case 28: {
        const v = this.alloc();
        this.partial(v, 0.7, 1260, 1180, 0.015, 0.03);
        this.noise(v, 0.3, 0.008, 0, 2, 2100, 0.8);
        this.env(v, 0.001, 0, 0.035, 0.055);
        this.finish(v, -22, gain, pan, delay, BUS_UI);
        break;
      }
      case 29:
        this.stab([D5, A5], -20, 0.002, 0.008, 0.15, gain, pan, delay, 0);
        break;
      case 30: {
        const v = this.alloc();
        this.partial(v, 0.8, D5, D5 * 0.75, 0.065, 0.12);
        this.partial(v, 0.2, D5 * 2, D5 * 1.5, 0.065, 0.06);
        this.noise(v, 0.12, 0.01, 0, 2, 1600, 1);
        this.env(v, 0.002, 0, 0.12, 0.24);
        this.finish(v, -22, gain, pan, delay, BUS_UI);
        break;
      }
      case 31: {
        this.stab([D5 * 0.5, D5], -20, 0.004, 0.025, 0.18, gain, pan, delay, 0);
        this.stab([A5, D6], -23, 0.004, 0.02, 0.2, gain, pan, delay + 0.055, 0);
        const v = this.alloc();
        this.noise(v, 0.6, 0.17, 1, 2, 450, 0.8, 2100, 0.15, 0.025);
        this.env(v, 0.025, 0.025, 0.17, 0.35);
        this.finish(v, -24, gain, pan, delay, BUS_UI);
        break;
      }
      // -- internal ambience events (>= 100) ------------------------------------
      case 100: {
        // metal creak
        const v = this.alloc();
        this.partial(v, 1, 680, 540, 0.3, 0.3);
        this.partial(v, 0.3, 1190, 1040, 0.3, 0.24);
        this.noise(v, 0.25, 0.25, 1, 2, 700, 3);
        v.amHz = 7;
        v.amDepth = 0.6;
        this.env(v, 0.03, 0.2, 0.15, 0.5);
        this.finish(v, -34, gain, pan, delay, BUS_AMBIENT, 0.3);
        break;
      }
      case 101: {
        // Two distant chirps with a softer breath edge, away from the UI octave.
        const v = this.alloc();
        this.partial(v, 0.8, 2300 * this.v(0.1), 3300, 0.045, 0.1);
        this.partial(v, 0.65, 3100, 2450, 0.06, 0.12, 0, 0.13);
        this.noise(v, 0.12, 0.2, 0, 2, 3200, 2);
        this.env(v, 0.004, 0.18, 0.06, 0.35);
        this.finish(v, -36, gain, pan, delay, BUS_AMBIENT, 0.25);
        break;
      }
      case 102: {
        // foundry clank (bottom-out at -20)
        const v = this.alloc();
        this.partial(v, 0.8, 1260, 1260, 0, 0.28);
        this.partial(v, 0.55, 2110, 2110, 0, 0.16);
        this.partial(v, 0.25, 3370, 3370, 0, 0.09);
        this.noise(v, 0.4, 0.012, 0, 2, 1800, 1);
        this.partial(v, 0.4, 180, 55, 0.06, 0.14);
        this.env(v, 0.001, 0, 0.2, 0.4);
        this.finish(v, -36, gain, pan, delay, BUS_AMBIENT, 0.4);
        break;
      }
      case 103: {
        // fire crackle grain
        const v = this.alloc();
        this.noise(v, 1, 0.005, 0, 2, 3000, 2);
        this.partial(v, 0.35, 160, 90, 0.01, 0.025);
        this.env(v, 0.0005, 0, 0.005, 0.02);
        this.finish(v, -32, gain, pan, delay, BUS_AMBIENT);
        break;
      }
      case 104: {
        // industrial: a distant press — one soft thump through the hall
        const v = this.alloc();
        this.partial(v, 1, 70, 45, 0.08, 0.25);
        this.partial(v, 0.3, 310, 300, 0, 0.14);
        this.noise(v, 0.4, 0.06, 2, 1, 300, 0.7);
        this.env(v, 0.004, 0, 0.3, 0.6);
        this.finish(v, -34, gain, pan, delay, BUS_AMBIENT, 0.6);
        break;
      }
      case 105: {
        // snow: a wind gust, rising then falling over ~2.5 s
        const v = this.alloc();
        this.noise(v, 1, 1.2, 1, 2, 500, 0.8, 900, 1.0, 0.9);
        v.amHz = 0.9;
        v.amDepth = 0.25;
        this.env(v, 0.9, 0.4, 1.2, 3.0);
        this.finish(v, -30, gain, pan, delay, BUS_AMBIENT, 0.1);
        break;
      }
      case 106: {
        // night city: a car passing on a street below (low rumble swell, one side)
        const v = this.alloc();
        this.noise(v, 1, 1.2, 2, 1, 700, 0.7, 400, 1.5, 1.0);
        this.partial(v, 0.18, 110, 72, 1.2, 2.5);
        this.env(v, 1.0, 0.3, 1.2, 3.0);
        this.finish(v, -28, gain, pan, delay, BUS_AMBIENT, 0.15);
        break;
      }
      case 107: {
        // foundry: a steam vent
        const v = this.alloc();
        this.noise(v, 1, 0.6, 0, 3, 2000, 0.7);
        v.amHz = 23;
        v.amDepth = 0.3;
        this.env(v, 0.15, 0.5, 0.6, 1.6);
        this.finish(v, -31, gain, pan, delay, BUS_AMBIENT, 0.3);
        break;
      }
      case 108: {
        // A distant gull: breathy descending cry with a rough, slow flutter.
        const v = this.alloc();
        const f = 1350 * this.v(0.12);
        this.partial(v, 0.8, f, f * 0.65, 0.38, 0.55);
        this.partial(v, 0.25, f * 2.03, f * 1.35, 0.38, 0.4);
        this.noise(v, 0.35, 0.6, 1, 2, 1600, 1.4, 1050, 0.4, 0.06);
        v.amHz = 6.5;
        v.amDepth = 0.35;
        this.env(v, 0.07, 0.2, 0.45, 1.0);
        this.finish(v, -34, gain, pan, delay, BUS_AMBIENT, 0.1);
        break;
      }
      case 109: {
        // A canopy gust shaking leaves, with irregular branch chatter.
        const v = this.alloc();
        this.noise(v, 1, 0.65, 1, 2, 2600, 0.7, 1800, 0.7, 0.2);
        v.amHz = 17 * this.v(0.3);
        v.amDepth = 0.65;
        this.env(v, 0.2, 0.25, 0.65, 1.4);
        this.finish(v, -35, gain, pan, delay, BUS_AMBIENT, 0.08);
        break;
      }
      case 110: {
        // Gravel settling on a distant quarry slope, rather than a hall's metal press.
        const v = this.alloc();
        this.noise(v, 0.9, 0.45, 1, 2, 1100, 0.8, 650, 0.5, 0.04);
        this.partial(v, 0.25, 320 * this.v(0.2), 240, 0.12, 0.25);
        this.partial(v, 0.18, 870 * this.v(0.2), 600, 0.2, 0.18);
        v.amHz = 26 * this.v(0.3);
        v.amDepth = 0.7;
        this.env(v, 0.04, 0.15, 0.45, 1.0);
        this.finish(v, -34, gain, pan, delay, BUS_AMBIENT, 0.15);
        break;
      }
    }
  }

  /**
   * Landing = a suspension thump and settle (round 4), not a click: a 60–120 Hz body thump (110 → 62 Hz over
   * 70 ms, 0.25 s decay, scaled by the compression through `gain`), the compression's brown whump under it, a
   * 2–3.5 kHz chassis rattle transient 4 ms after; every centre and decay drawn per event. The tyre scrub is its
   * own transient (kind 27) so it can carry the speed.
   */
  private landing(gain: number, surf: number, pan: number, delay: number): void {
    const dirt = surf === 0 || surf === 7;
    const metal = surf === 2 || surf === 5;
    const v = this.alloc();
    this.partial(v, 1, 110 * this.v(0.22), 62 * this.v(0.15), 0.07 * this.v(0.4), 0.4 * this.v(0.35));
    this.partial(v, 0.55, 78 * this.v(0.16), 74 * this.v(0.12), 0.2, 0.5 * this.v(0.35));
    this.noise(v, dirt ? 1.1 : 0.7, 0.22, 2, 1, 220, 0.7);
    this.env(v, 0.003, 0.07, 0.55, 0.9);
    this.finish(v, -3, gain, pan, delay, BUS_CHASSIS, 0.1);
    const r = this.alloc();
    this.partial(r, 0.8, 1900 * this.v(0.1), 1900, 0, 0.03);
    this.partial(r, 0.6, 3300 * this.v(0.1), 3300, 0, 0.02);
    this.noise(r, 1, 0.035 * this.v(0.3), 0, 2, 2600 * this.v(0.15), 1.2);
    this.env(r, 0.0005, 0.003, 0.04, 0.1);
    this.finish(r, -26 + 5 * gain, gain, pan, delay + 0.004, BUS_CHASSIS, 0.15);
    // The suspension is the shared body; contact with the course has its own
    // modes and grain. Wood flexes, loose rock rattles, snow compresses, metal rings.
    const contact = this.alloc();
    if (metal) {
      const grate = surf === 5;
      const mode1 = grate ? 740 : 1280;
      const mode2 = grate ? 1850 : 2130;
      const mode3 = grate ? 2870 : 3460;
      this.partial(contact, 0.75, mode1 * this.v(0.025), mode1, 0, grate ? 0.14 : 0.22);
      this.partial(contact, 0.55, mode2 * this.v(0.025), mode2, 0, 0.14);
      this.partial(contact, 0.3, mode3 * this.v(0.025), mode3, 0, 0.08);
      this.noise(contact, 0.4, 0.015, 0, 2, 2800, 1.4);
    } else if (surf === 1) {
      this.partial(contact, 0.9, 185 * this.v(0.08), 180, 0.02, 0.2);
      this.partial(contact, 0.85, 423 * this.v(0.06), 420, 0, 0.14);
      this.partial(contact, 0.3, 790 * this.v(0.04), 790, 0, 0.07);
      this.noise(contact, 0.8, 0.025, 1, 2, 1100, 1.1);
    } else if (surf === 4) {
      this.partial(contact, 0.8, 155, 80, 0.04, 0.13);
      this.noise(contact, 0.45, 0.04, 2, 1, 600, 0.7);
    } else if (surf === 7) {
      this.noise(contact, 1.6, 0.17, 1, 2, 1150, 0.65);
      contact.amHz = 93;
      contact.amDepth = 0.6;
    } else if (surf === 6) {
      this.partial(contact, 0.35, 1720 * this.v(0.08), 1700, 0, 0.08);
      this.partial(contact, 0.2, 2910 * this.v(0.08), 2900, 0, 0.05);
      this.noise(contact, 1.2, 0.065, 0, 2, 2400, 0.85);
      contact.amHz = 115;
      contact.amDepth = 0.55;
    } else if (surf === 3) {
      this.partial(contact, 0.55, 350, 310, 0.025, 0.085);
      this.noise(contact, 1, 0.025, 0, 2, 1850, 0.7);
    } else {
      this.noise(contact, 1.5, 0.11, 1, 2, 1400, 0.6);
      contact.amHz = 65;
      contact.amDepth = 0.5;
    }
    this.env(contact, 0.001, 0.008, 0.22, 0.42);
    this.finish(contact, -20, gain, pan, delay + 0.002, BUS_CHASSIS, metal ? 0.2 : 0.05);
  }

  /**
   * The D-key stinger family: a tuned mallet body, a short upper strike and a
   * restrained band-limited brass edge. High modes fall away before the body.
   */
  private stab(freqs: readonly number[], db: number, attS: number, holdS: number, decS: number, gain: number, pan: number, delay: number, send: number): void {
    const v = this.alloc();
    const f = freqs[0]!;
    this.partial(v, 0.95, f, f, 0, decS);
    this.partial(v, 0.22, f * 2, f * 2, 0, Math.min(0.085, decS));
    this.partial(v, 0.4, freqs[1] ?? f * 0.5, freqs[1] ?? f * 0.5, 0, decS, 2);
    this.partial(v, 0.3, freqs[2] ?? f, freqs[2] ?? f, 0, decS, 1);
    this.noise(v, 0.1, 0.012, 0, 2, 2400, 0.7);
    v.formant = true;
    v.f1.bypass();
    v.f2.bypass();
    v.f3.bypass();
    v.flp.lowpass(4200, 0.7);
    this.env(v, attS, holdS, decS, attS + holdS + decS * 3);
    this.finish(v, db, gain, pan, delay, BUS_UI, send);
  }

  private goChord(db: number, gain: number, pan: number, delay: number, whoosh: boolean): void {
    // GO / finish tick: D6 over A5 over D5
    this.stab([D6, A5, D5], db, 0.002, whoosh ? 0.12 : 0.06, whoosh ? 0.3 : 0.22, gain, pan, delay, 0.2);
    if (whoosh) {
      const w = this.alloc();
      this.noise(w, 1, 0.2, 0, 2, 600, 1, 5000, 0.25, 0.02);
      this.env(w, 0.02, 0.05, 0.2, 0.4);
      this.finish(w, -20, gain, pan, delay, BUS_UI, 0.2);
    }
  }

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------

  /** Adds into per-bus stereo buffers: bus[b] = [L, R]. */
  process(bus: readonly [Float32Array, Float32Array][], off: number, n: number): void {
    for (const v of this.voices) {
      if (!v.active) continue;
      this.renderVoice(v, bus[v.bus]!, off, n);
    }
    this.sampleClock += n;
  }

  private renderVoice(v: Voice, out: [Float32Array, Float32Array], off: number, n: number): void {
    const L = out[0];
    const R = out[1];
    let i = 0;
    if (v.delay > 0) {
      const skip = Math.min(v.delay, n);
      v.delay -= skip;
      i = skip;
      if (v.delay > 0) return;
    }
    if (i < n && v.t === 0 && this.logOnsets) this.onsetLog.push({ kind: v.bus, sample: this.sampleClock + i });
    if (v.nFilter !== 0) this.setNoiseFilter(v);
    const sr = this.sr;
    for (; i < n; i++) {
      if (v.t >= v.life) {
        v.active = false;
        return;
      }
      // envelope
      if (v.t < v.att) v.env = v.t / v.att;
      else if (v.t < v.att + v.hold) v.env = 1;
      else v.env *= v.dec;
      let x = 0;
      for (let k = 0; k < v.np; k++) {
        if (v.pDelay[k]! > v.t) continue;
        const f = v.pF[k]!;
        v.pF[k] = f + (v.pFEnd[k]! - f) * v.pGlide[k]!;
        const w = v.pWave[k];
        const step = f / sr * (w === 3 ? v.glottalJitter : 1);
        let ph = v.pPhase[k]! + step;
        if (ph >= 1) {
          ph -= 1;
          if (w === 3) {
            v.glottalJitter = 1 + 0.016 * v.rng.n();
            v.glottalShimmer = 1 + 0.07 * v.rng.n();
          }
        }
        v.pPhase[k] = ph;
        const s = w === 0 ? sineCycle(ph) : w === 1 ? bandLimitedSaw(ph, step) : w === 3 ? glottalPulse(ph, 0.65) * v.glottalShimmer : 4 * Math.abs(ph - 0.5) - 1;
        x += s * v.pAmp[k]!;
        v.pAmp[k] = v.pAmp[k]! * v.pDecay[k]!;
      }
      if (v.formant) {
        x = v.flp.process(v.f1.process(x) * 0.5 + v.f2.process(x) * 0.35 + v.f3.process(x) * 0.25);
      }
      if (v.nAmp > 1e-5) {
        const w = v.rng.n();
        let nz = v.nColour === 1 ? v.colour.pink(w) : v.nColour === 2 ? v.colour.brownian(w) : w;
        if (v.nGlide > 0 && v.nGlide < 1 && (v.t & 63) === 63) {
          v.nF += (v.nFEnd - v.nF) * (1 - Math.pow(1 - v.nGlide, 64));
          this.setNoiseFilter(v);
        }
        if (v.nFilter !== 0) nz = v.nBq.process(nz);
        const nAtt = v.t < v.nAtt ? v.t / v.nAtt : 1;
        x += nz * v.nAmp * nAtt;
        if (v.t >= v.att + v.hold) v.nAmp *= v.nDecay;
      }
      if (v.amHz > 0) {
        v.amPhase += v.amHz / sr;
        if (v.amPhase >= 1) v.amPhase -= 1;
        x *= 1 - v.amDepth * 0.5 * (1 + sineCycle(v.amPhase));
      }
      if (v.gateHz > 0) {
        v.gatePhase += v.gateHz / sr;
        if (v.gatePhase >= 1) v.gatePhase -= 1;
        if (v.gatePhase > v.gateDuty) x = 0;
      }
      // The voice lifetime must not cut a ring at an arbitrary sample value.
      const tail = v.t > v.fadeFrom ? (v.life - v.t) * v.fadeStep : 1;
      let g = v.env * v.gain * tail;
      if (v.killing) {
        v.killGain -= v.killStep;
        if (v.killGain <= 0) {
          v.active = false;
          return;
        }
        g *= v.killGain;
      }
      x *= g;
      L[off + i] = L[off + i]! + x * v.gl;
      R[off + i] = R[off + i]! + x * v.gr;
      v.t++;
    }
    if (v.t >= v.life) v.active = false;
  }

  private setNoiseFilter(v: Voice): void {
    const f = clamp(v.nF, 20, this.sr * 0.45);
    if (v.nFilter === 1) v.nBq.lowpass(f, v.nQ);
    else if (v.nFilter === 2) v.nBq.bandpass(f, v.nQ);
    else if (v.nFilter === 3) v.nBq.highpass(f, v.nQ);
  }

  /** Reverb send mix of currently active voices is applied by the synth via sendGain(). */
  sendGainOf(bus: number): number {
    let s = 0;
    for (const v of this.voices) if (v.active && v.bus === bus && v.send > s) s = v.send;
    return s;
  }
}
