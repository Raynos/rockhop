/**
 * Tyre roll noise per surface, rear skid, chain whine.
 * Surface index order matches params.SURFACES:
 *   0 dirt, 1 wood, 2 metal, 3 concrete, 4 rubber, 5 grate, 6 stone, 7 snow
 */
import { Biquad, NoiseColour, NoiseRng, TWO_PI, clamp, dbToGain, smoothCoef, sineCycle } from './util';

/** base gain dB at 10 m/s per surface */
const BASE_DB = [-18, -20, -22, -20, -24, -19, -19, -20];
/** grain rate per second at 0 m/s and per m/s, grain length s, grain centre Hz, Q */
const GRAINS: readonly (readonly [number, number, number, number, number] | null)[] = [
  [18, 7, 0.006, 1600, 1.3], // loose grit, soft grains
  [4, 1.2, 0.012, 460, 2.8], // grain of flexible wood beneath the joint thuds
  [7, 2, 0.004, 2700, 3.5], // hard particles on sheet metal
  [12, 3, 0.002, 3200, 0.8], // fine concrete texture
  [3, 0.7, 0.009, 330, 1], // muffled rubber contact
  null,
  [10, 4, 0.009, 2300, 2.2], // loose stone clatter
  [38, 10, 0.012, 1050, 0.9], // compressed snow crunch
];

const GRATE_MAX = 4096;

export class TyreVoice {
  private readonly sr: number;
  private readonly rng: NoiseRng;
  private readonly colour = new NoiseColour();
  private readonly f1: Biquad;
  private readonly f2: Biquad;
  private readonly grainBp: Biquad;
  private readonly hiss: Biquad;
  private readonly grate = new Float32Array(GRATE_MAX);
  private grateIdx = 0;
  private grateDelay = 100;
  private surface = -1;
  private gainTarget = 0;
  private gain = 0;
  private readonly kGain: number;
  private grainRate = 0;
  private grainEnv = 0;
  private grainDecay = 0;
  private hissGain = 0;
  private noiseKind = 0; // 0 white 1 pink 2 brown
  private whineHz = 0;
  private whinePh = 0;
  private treadPhase = 0;
  private treadHz = 0;

  constructor(sr: number, seed: number) {
    this.sr = sr;
    this.rng = new NoiseRng(seed);
    this.f1 = new Biquad(sr);
    this.f2 = new Biquad(sr);
    this.grainBp = new Biquad(sr);
    this.hiss = new Biquad(sr);
    this.hiss.highpass(6000, 0.7);
    this.kGain = smoothCoef(0.01, sr);
  }

  set(speed: number, surface: number): void {
    if (surface !== this.surface) {
      this.surface = surface;
      this.f1.reset();
      this.f2.reset();
      this.grainBp.reset();
      this.colour.reset();
      this.grainEnv = 0;
      this.grate.fill(0);
    }
    if (surface < 0 || speed <= 0) {
      this.gainTarget = 0;
      return;
    }
    const v = speed;
    this.treadHz = v / (TWO_PI * 0.34);
    this.gainTarget = dbToGain(BASE_DB[surface] ?? -20) * Math.pow(v / 10, 0.7);
    this.hissGain = 0;
    this.noiseKind = 0;
    this.whineHz = 0;
    switch (surface) {
      case 0: // dirt
        this.noiseKind = 2;
        this.f1.lowpass(900 + 60 * v, 0.6);
        this.f2.bypass();
        break;
      case 1: // wood
        this.noiseKind = 1;
        this.f1.bandpass(300 + 25 * v, 1.2);
        this.f2.peaking(220, 6, 8);
        break;
      case 2: // metal
        this.noiseKind = 1;
        this.f1.highpass(500, 0.7);
        this.f2.peaking(1450, 4, 5);
        break;
      case 3: // concrete
        this.noiseKind = 1;
        this.f1.highpass(250, 0.7);
        this.f2.lowpass(4000, 0.7);
        break;
      case 4: // rubber
        this.noiseKind = 2;
        this.f1.lowpass(500, 0.7);
        this.f2.peaking(180, 2, 5);
        break;
      case 5: // grate: comb buzz at v / 0.05 m
        this.f1.peaking(2400, 8, 6);
        this.f2.bypass();
        this.grateDelay = clamp(Math.round((0.05 / Math.max(v, 0.5)) * this.sr), 8, GRATE_MAX - 1);
        this.whineHz = v / 0.05; // bar-crossing rate → the grate whine
        break;
      case 6: // stone
        this.noiseKind = 1;
        this.f1.highpass(200, 0.7);
        this.f2.lowpass(3000, 0.7);
        break;
      default: // snow
        this.noiseKind = 2;
        this.f1.lowpass(700, 0.7);
        this.f2.bypass();
        this.hissGain = dbToGain(-20);
        break;
    }
    const g = GRAINS[surface] ?? null;
    if (g) {
      this.grainRate = (g[0] + g[1] * v) / this.sr;
      this.grainDecay = Math.pow(0.01, 1 / (g[2] * this.sr));
      this.grainBp.bandpass(g[3], g[4]);
    } else {
      this.grainRate = 0;
    }
  }

  process(out: Float32Array, off: number, n: number): void {
    if (this.gain < 1e-5 && this.gainTarget < 1e-5) {
      this.gain = this.gainTarget;
      return;
    }
    const isGrate = this.surface === 5;
    const grainRate = this.grainRate;
    for (let i = 0; i < n; i++) {
      this.gain += (this.gainTarget - this.gain) * this.kGain;
      const w = this.rng.n();
      let x = this.noiseKind === 1 ? this.colour.pink(w) : this.noiseKind === 2 ? this.colour.brownian(w) : w;
      if (isGrate) {
        const rd = (this.grateIdx - this.grateDelay + GRATE_MAX) % GRATE_MAX;
        const d = this.grate[rd]!;
        const y = x + d * 0.6;
        this.grate[this.grateIdx] = y;
        this.grateIdx = (this.grateIdx + 1) % GRATE_MAX;
        x = y * 0.6;
      }
      x = this.f2.process(this.f1.process(x));
      if (grainRate > 0) {
        if (this.rng.u() < grainRate) this.grainEnv = 0.8 + 0.4 * this.rng.u();
        let g = 0;
        if (this.grainEnv > 1e-3) {
          g = this.grainEnv * this.rng.n();
          this.grainEnv *= this.grainDecay;
        }
        x += this.grainBp.process(g) * 1.5;
      }
      if (this.hissGain > 0) x += this.hiss.process(w) * this.hissGain;
      if (this.whineHz > 0) {
        this.whinePh += this.whineHz / this.sr;
        if (this.whinePh >= 1) this.whinePh -= 1;
        x += (sineCycle(this.whinePh) + 0.5 * sineCycle(this.whinePh * 2 % 1)) * 0.35;
      }
      this.treadPhase += this.treadHz / this.sr;
      if (this.treadPhase >= 1) this.treadPhase -= 1;
      // Wheel-revolution contact flutter keeps a surface moving rather than a static noise bed.
      const contact = 0.78 + 0.22 * Math.abs(2 * this.treadPhase - 1);
      out[off + i] = out[off + i]! + x * this.gain * contact;
    }
  }
}

export class SkidVoice {
  private readonly rng: NoiseRng;
  private readonly bp: Biquad;
  private readonly bp2: Biquad;
  private gainTarget = 0;
  private gain = 0;
  private readonly kGain: number;
  private readonly sr: number;
  private phase = 0;
  private chatterPhase = 0;
  private hz = 1700;
  private scrape = false;

  constructor(sr: number, seed: number) {
    this.sr = sr;
    this.rng = new NoiseRng(seed);
    this.bp = new Biquad(sr);
    this.bp2 = new Biquad(sr);
    this.bp2.bypass();
    this.kGain = smoothCoef(0.01, sr);
  }

  /** Rear tyre skid: white → BP 1200 + 1400·slip Hz Q 3, −30 + 22·slip dB above slip 0.25. */
  set(slip: number): void {
    this.scrape = false;
    this.bp2.bypass();
    if (slip < 0.25) {
      this.gainTarget = 0;
      return;
    }
    this.hz = 950 + 1400 * slip;
    this.bp.bandpass(1200 + 1400 * slip, 1.5);
    this.gainTarget = dbToGain(-30 + 22 * slip);
  }

  /** Crashed frame scrubbing the ground: gritty 400 Hz–3 kHz noise, −24 + 10·scrape dB. */
  setScrape(scrape: number): void {
    this.scrape = true;
    if (scrape < 0.02) {
      this.gainTarget = 0;
      return;
    }
    this.bp.highpass(400, 0.7);
    this.bp2.lowpass(3000 + 2000 * scrape, 0.7);
    this.gainTarget = dbToGain(-24 + 10 * scrape);
  }

  process(out: Float32Array, off: number, n: number): void {
    if (this.gain < 1e-5 && this.gainTarget < 1e-5) return;
    for (let i = 0; i < n; i++) {
      this.gain += (this.gainTarget - this.gain) * this.kGain;
      this.chatterPhase += (this.scrape ? 86 : 61) / this.sr;
      if (this.chatterPhase >= 1) this.chatterPhase -= 1;
      const flutter = 0.72 + 0.28 * sineCycle(this.chatterPhase);
      let friction = this.bp2.process(this.bp.process(this.rng.n()));
      if (!this.scrape) {
        this.phase += this.hz / this.sr;
        if (this.phase >= 1) this.phase -= 1;
        friction += 0.16 * sineCycle(this.phase) * flutter;
      }
      out[off + i] = out[off + i]! + friction * flutter * this.gain;
    }
  }
}

/** Two sines at the sprocket tooth frequency through a soft cubic + mesh peak. */
export class ChainVoice {
  private readonly sr: number;
  private readonly rng: NoiseRng;
  private readonly mesh: Biquad;
  private readonly rattle: Biquad;
  private ph1 = 0;
  private ph2 = 0;
  private hz = 0;
  private jitter = 1;
  private gainTarget = 0;
  private gain = 0;
  private readonly kGain: number;
  private sinceJitter = 0;

  constructor(sr: number, seed: number) {
    this.sr = sr;
    this.rng = new NoiseRng(seed);
    this.mesh = new Biquad(sr);
    this.mesh.peaking(1600, 2, 4);
    this.rattle = new Biquad(sr);
    this.rattle.bandpass(2400, 1.4);
    this.kGain = smoothCoef(0.02, sr);
  }

  set(chainHz: number, airborne: boolean): void {
    this.hz = chainHz;
    if (chainHz <= 0) {
      this.gainTarget = 0;
      return;
    }
    // v = chainHz / 42 teeth * 2πR
    const v = (chainHz / 42) * TWO_PI * 0.34;
    if (v < 1.5) {
      this.gainTarget = 0;
      return;
    }
    let g = dbToGain(-34 + 20 * Math.log10(v / 10));
    if (airborne) g *= 0.5;
    this.gainTarget = g;
  }

  process(out: Float32Array, off: number, n: number): void {
    if (this.gain < 1e-5 && this.gainTarget < 1e-5) return;
    this.sinceJitter += n;
    if (this.sinceJitter >= this.sr / 4) {
      this.sinceJitter = 0;
      this.jitter = clamp(this.jitter + 0.003 * this.rng.n(), 0.99, 1.01);
    }
    const d1 = (this.hz * this.jitter) / this.sr;
    const d2 = d1 * 2;
    const g2 = dbToGain(-8);
    for (let i = 0; i < n; i++) {
      this.gain += (this.gainTarget - this.gain) * this.kGain;
      this.ph1 += d1;
      if (this.ph1 >= 1) this.ph1 -= 1;
      this.ph2 += d2;
      if (this.ph2 >= 1) this.ph2 -= 1;
      let x = sineCycle(this.ph1) + g2 * sineCycle(this.ph2);
      x = x + 0.3 * x * x * x;
      const lash = this.ph1 < 0.13 ? 1 - this.ph1 / 0.13 : 0;
      const rattle = this.rattle.process(this.rng.n() * lash) * 0.6;
      out[off + i] = out[off + i]! + (this.mesh.process(x) * 0.82 + rattle) * this.gain;
    }
  }
}
