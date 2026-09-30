/**
 * Per-biome ambience beds + speed wind. Biome index order matches
 * params.BIOMES: five legacy worlds, then coast, alpine and quarry.
 * Sparse events (creak, bird, clank, crackle) go through the voice pool on
 * the ambient bus with seeded timers.
 */
import { Biquad, NoiseColour, NoiseRng, TWO_PI, clamp, dbToGain, smoothCoef, sineCycle } from './util';
import type { VoicePool } from './voices';

export class Ambience {
  private readonly sr: number;
  private readonly rng: NoiseRng;
  private readonly colour = new NoiseColour();
  private readonly colour2 = new NoiseColour();
  private readonly colourR = new NoiseColour();
  private readonly bedSide: Biquad;
  private readonly bedLp: Biquad;
  private readonly bedLp2: Biquad;
  private readonly hiss: Biquad;
  private readonly neonLp: Biquad;
  private readonly windHp: Biquad;
  private readonly windHpR: Biquad;
  private readonly windBp: Biquad;
  /** 7.3 ms delayed copy of the bandpassed rush for the right ear (decorrelates the 350–900 Hz band at no cost). */
  private readonly windDelay: Float32Array;
  private windPos = 0;
  private readonly windColour = new NoiseColour();
  private windF = 350;
  private windHi = 0.25;
  private biome = -1;
  private gainTarget = 1;
  private requestedGain = 1;
  private bedEnabled = true;
  private gain = 0;
  private readonly kGain: number;
  private windTarget = 0;
  private wind = 0;
  private readonly kWind: number;
  private lfo1 = 0;
  private lfo2 = 0;
  private hum1 = 0;
  private hum2 = 0;
  private neon = 0;
  private cricket = 0;
  private cricketGate = 0;
  private nextEvent = 0;
  private crackleRate = 0;
  private sinceLfo = 0;
  private bedGain = 0;
  private bedGain2 = 0;
  private lfoGain = 1;
  // round 3 extras: industrial press timer + conveyor hum, foundry hiss LFO
  private pressNext = 0;
  private conv1 = 0;
  private conv2 = 0;
  private convAm = 0;
  private readonly hissHp: Biquad;
  private hissLfo = 0;

  constructor(sr: number, seed: number) {
    this.sr = sr;
    this.rng = new NoiseRng(seed);
    this.bedLp = new Biquad(sr);
    this.bedSide = new Biquad(sr);
    this.bedLp2 = new Biquad(sr);
    this.hiss = new Biquad(sr);
    this.neonLp = new Biquad(sr);
    this.neonLp.lowpass(400, 0.7);
    // speed wind (round 3): a dark rush — pink noise through a bandpass that climbs 350 → 900 Hz with speed —
    // plus a little HP 3 kHz hiss 12 dB under it; v1's white HP 1.2 kHz put the landing beat's centroid at 1.6 kHz
    // against the reference's 150–300 Hz
    this.windHp = new Biquad(sr);
    this.windHp.highpass(3000, 0.7);
    this.windHpR = new Biquad(sr);
    this.windHpR.highpass(3400, 0.7);
    this.windBp = new Biquad(sr);
    this.windBp.bandpass(350, 0.8);
    this.windDelay = new Float32Array(Math.max(1, Math.round(0.0073 * sr)));
    this.hissHp = new Biquad(sr);
    this.hissHp.highpass(3000, 0.7);
    this.kGain = smoothCoef(0.05, sr);
    this.kWind = smoothCoef(0.03, sr);
  }

  set(biome: number, ambientGain: number, wind: number, airborne: boolean): void {
    if (biome !== this.biome) {
      this.biome = biome;
      this.configure();
    }
    this.requestedGain = clamp(ambientGain, 0, 1);
    this.gainTarget = this.bedEnabled ? this.requestedGain : 0;
    const w = clamp(wind, 0, 1);
    // round 4: 20 dB of rise over the speed range (was 14) to ≈ −28 dBFS at 14 m/s, so the wind is heard climbing with the launch
    this.windTarget = dbToGain(-36 + 20 * w + (airborne ? 3 : 0)) * (wind > 0.01 ? 1 : 0);
    this.windHi = 0.25 + 0.25 * w;
    const f = 350 + 550 * w;
    if (Math.abs(f - this.windF) > 10) {
      this.windF = f;
      this.windBp.bandpass(f, 0.8);
    }
  }

  /** A loaded environment recording replaces the bed; helmet wind remains reactive. */
  setBedEnabled(on: boolean): void {
    this.bedEnabled = on;
    this.gainTarget = on ? this.requestedGain : 0;
  }

  private configure(): void {
    this.bedLp.reset();
    this.bedSide.reset();
    this.colour.reset();
    this.colourR.reset();
    this.nextEvent = 0;
    this.crackleRate = 0;
    this.bedGain2 = 0;
    switch (this.biome) {
      case 0: // industrial: hum + room tone + HVAC
        this.bedLp.lowpass(1200, 0.7);
        this.bedGain = dbToGain(-33);
        this.bedLp2.lowpass(180, 0.7);
        this.bedGain2 = dbToGain(-36);
        this.bedSide.bandpass(650, 0.7);
        break;
      case 1: // canyon wind
        this.bedLp.lowpass(320, 0.7);
        this.bedGain = dbToGain(-27);
        this.bedSide.bandpass(480, 0.8);
        break;
      case 2: // snow: hush (a quieter, darker bed than the canyon) + hiss; the gusts are events
        this.bedLp.lowpass(420, 0.7);
        this.bedGain = dbToGain(-31);
        this.hiss.highpass(6000, 0.7);
        this.bedSide.bandpass(950, 0.5);
        break;
      case 3: // night city traffic bed
        this.bedLp.lowpass(140, 0.7);
        this.bedGain = dbToGain(-25);
        this.bedSide.bandpass(360, 0.75);
        break;
      case 5: // shore: rolling low surf with a brighter wash of foam
        this.bedLp.lowpass(650, 0.7);
        this.bedGain = dbToGain(-27);
        this.bedLp2.reset();
        this.colour2.reset();
        this.bedLp2.lowpass(2800, 0.6);
        this.bedGain2 = dbToGain(-37);
        this.bedSide.bandpass(1000, 0.6);
        break;
      case 6: // forest canopy: soft air through branches and dry leaves
        this.bedLp.lowpass(700, 0.7);
        this.bedGain = dbToGain(-29);
        this.bedLp2.reset();
        this.colour2.reset();
        this.bedLp2.bandpass(2600, 0.65);
        this.bedGain2 = dbToGain(-36);
        this.bedSide.bandpass(1400, 0.6);
        break;
      case 7: // quarry: distant diesel, loose stone and open air
        this.bedLp.lowpass(260, 0.7);
        this.bedGain = dbToGain(-28);
        this.bedLp2.reset();
        this.colour2.reset();
        this.bedLp2.bandpass(900, 0.8);
        this.bedGain2 = dbToGain(-37);
        this.bedSide.bandpass(600, 0.8);
        break;
      default: // foundry roar
        this.bedLp.lowpass(220, 0.7);
        this.bedGain = dbToGain(-22);
        this.crackleRate = 4 / this.sr;
        this.bedSide.bandpass(780, 0.7);
        break;
    }
  }

  private scheduleEvent(pool: VoicePool): void {
    const b = this.biome;
    if (b === 0) {
      pool.trigger({ kind: 100, gain: 1, pitch: 0, pan: this.rng.range2(-0.5, 0.5), delay: 0 });
      this.nextEvent = this.rng.range2(9, 17) * this.sr;
    } else if (b === 1) {
      pool.trigger({ kind: 101, gain: 1, pitch: 0, pan: this.rng.range2(-0.6, 0.6), delay: 0 });
      this.nextEvent = this.rng.range2(6, 14) * this.sr;
    } else if (b === 2) {
      pool.trigger({ kind: 105, gain: 1, pitch: 0, pan: this.rng.range2(-0.5, 0.5), delay: 0 });
      this.nextEvent = this.rng.range2(5, 9) * this.sr;
    } else if (b === 3) {
      pool.trigger({ kind: 106, gain: 1, pitch: 0, pan: this.rng.u() < 0.5 ? -0.7 : 0.7, delay: 0 });
      this.nextEvent = this.rng.range2(7, 13) * this.sr;
    } else if (b === 4) {
      const steam = this.rng.u() < 0.5;
      pool.trigger({ kind: steam ? 107 : 102, gain: 1, pitch: 0, pan: this.rng.range2(-0.4, 0.4), delay: 0 });
      this.nextEvent = this.rng.range2(5, 11) * this.sr;
    } else if (b === 5) {
      pool.trigger({ kind: 108, gain: 1, pitch: 0, pan: this.rng.range2(-0.8, 0.8), delay: 0 });
      this.nextEvent = this.rng.range2(8, 18) * this.sr;
    } else if (b === 6) {
      pool.trigger({ kind: this.rng.u() < 0.65 ? 101 : 109, gain: 1, pitch: 0, pan: this.rng.range2(-0.8, 0.8), delay: 0 });
      this.nextEvent = this.rng.range2(4, 10) * this.sr;
    } else if (b === 7) {
      pool.trigger({ kind: 110, gain: 1, pitch: 0, pan: this.rng.range2(-0.6, 0.6), delay: 0 });
      this.nextEvent = this.rng.range2(7, 15) * this.sr;
    } else {
      this.nextEvent = 30 * this.sr;
    }
  }

  /** Adds stereo into L/R. */
  process(L: Float32Array, R: Float32Array, off: number, n: number, pool: VoicePool): void {
    // LFO update at block rate (cheap; ~0.1..6 Hz content)
    const blockDt = n / this.sr;
    this.sinceLfo += n;
    const b = this.biome;
    if (b === 1 || b === 2) {
      this.lfo1 += TWO_PI * 0.13 * blockDt;
      this.lfo2 += TWO_PI * 0.31 * blockDt;
      this.lfoGain = dbToGain(6 * Math.sin(this.lfo1) + 3 * Math.sin(this.lfo2));
    } else if (b === 3) {
      this.lfo1 += TWO_PI * 0.05 * blockDt;
      this.lfoGain = dbToGain(4 * Math.sin(this.lfo1));
    } else if (b === 4) {
      this.lfo1 += TWO_PI * 6 * blockDt;
      this.lfoGain = dbToGain(3 * Math.sin(this.lfo1));
    } else if (b >= 5 && b <= 7) {
      this.lfo1 += TWO_PI * (b === 5 ? 0.12 : b === 6 ? 0.19 : 0.07) * blockDt;
      this.lfo2 += TWO_PI * 0.037 * blockDt;
      this.lfoGain = dbToGain((b === 5 ? 5 : 3) * Math.sin(this.lfo1) + 2 * Math.sin(this.lfo2));
    } else {
      this.lfoGain = 1;
    }
    if (this.lfo1 > TWO_PI) this.lfo1 -= TWO_PI;
    if (this.lfo2 > TWO_PI) this.lfo2 -= TWO_PI;

    if (this.bedEnabled && (this.gain > 1e-4 || this.gainTarget > 1e-4)) {
      this.nextEvent -= n;
      if (this.nextEvent <= 0) this.scheduleEvent(pool);
      if (b === 0) {
        // distant machinery: a press every 1.25 s (a little seeded slop), never quite on the beat
        this.pressNext -= n;
        if (this.pressNext <= 0) {
          pool.trigger({ kind: 104, gain: this.rng.range2(0.6, 1), pitch: 0, pan: this.rng.range2(-0.3, 0.3), delay: 0 });
          this.pressNext = this.rng.range2(1.15, 1.35) * this.sr;
        }
      }
    }
    if (b === 4) {
      this.hissLfo += TWO_PI * 0.3 * blockDt;
      if (this.hissLfo > TWO_PI) this.hissLfo -= TWO_PI;
    }

    const sr = this.sr;
    const humG = dbToGain(-40);
    const neonG = dbToGain(-42);
    const cricketG = dbToGain(-40);
    const hissG = dbToGain(-46);
    const convG = dbToGain(-44);
    const furnaceHissG = dbToGain(-38 + 4 * Math.sin(this.hissLfo));
    const crackleRate = this.crackleRate;
    for (let i = 0; i < n; i++) {
      this.gain += (this.gainTarget - this.gain) * this.kGain;
      this.wind += (this.windTarget - this.wind) * this.kWind;
      const wL = this.rng.n();
      const wR = this.rng.n();
      let l = 0;
      let r = 0;
      const g = this.gain;
      if (g > 1e-4) {
        const bed = this.bedLp.process(this.colour.brownian(wL)) * this.bedGain * this.lfoGain;
        const distance = this.bedSide.process(this.colourR.pink(wR)) * this.bedGain * 0.32 * this.lfoGain;
        l += bed + distance;
        r += bed - distance * 0.8;
        if (b === 0) {
          this.hum1 += 60 / sr;
          if (this.hum1 >= 1) this.hum1 -= 1;
          this.hum2 += 120 / sr;
          if (this.hum2 >= 1) this.hum2 -= 1;
          const hum = (sineCycle(this.hum1) + 0.6 * sineCycle(this.hum2)) * humG;
          const hvac = this.bedLp2.process(this.colour2.pink(wR)) * this.bedGain2;
          // conveyor: 90 / 135 Hz partials under a slow 0.4 Hz swell
          this.conv1 += 90 / sr;
          if (this.conv1 >= 1) this.conv1 -= 1;
          this.conv2 += 135 / sr;
          if (this.conv2 >= 1) this.conv2 -= 1;
          this.convAm += 0.4 / sr;
          if (this.convAm >= 1) this.convAm -= 1;
          const conv = (sineCycle(this.conv1) + 0.5 * sineCycle(this.conv2)) * convG * (0.7 + 0.3 * sineCycle(this.convAm));
          l += hum + hvac + conv;
          r += hum + hvac + conv * 0.8;
        } else if (b === 2) {
          const h = this.hiss.process(wR) * hissG;
          l += h;
          r += h * 0.8;
        } else if (b === 3) {
          this.neon += 120 / sr;
          if (this.neon >= 1) this.neon -= 1;
          const nz = this.neonLp.process((2 * this.neon - 1) + sineCycle(this.neon * 2 % 1)) * neonG;
          this.cricket += 4200 / sr;
          if (this.cricket >= 1) this.cricket -= 1;
          this.cricketGate += 18 / sr;
          if (this.cricketGate >= 1) this.cricketGate -= 1;
          const cr = this.cricketGate < 0.6 ? sineCycle(this.cricket) * cricketG : 0;
          l += nz + cr * 0.4;
          r += nz + cr;
        } else if (b === 4) {
          // furnace: the roar bed plus a breathing hiss
          const hs = this.hissHp.process(wR) * furnaceHissG;
          l += hs;
          r += hs * 0.85;
          if (this.bedEnabled && crackleRate > 0 && this.rng.u() < crackleRate) pool.trigger({ kind: 103, gain: 1, pitch: 0, pan: this.rng.range2(-0.7, 0.7), delay: 0 });
        } else if (b >= 5 && b <= 7) {
          const texture = this.bedLp2.process(b === 5 ? wR : this.colour2.pink(wR)) * this.bedGain2 * this.lfoGain;
          l += texture * 0.65;
          r += texture;
          if (b === 7) {
            // Low diesel firing pulses, softened by distance; no mains hum or indoor press.
            this.conv1 += 73 / sr;
            if (this.conv1 >= 1) this.conv1 -= 1;
            this.conv2 += 109.5 / sr;
            if (this.conv2 >= 1) this.conv2 -= 1;
            const motor = (sineCycle(this.conv1) + 0.35 * sineCycle(this.conv2)) * convG * this.lfoGain;
            l += motor;
            r += motor * 0.7;
          }
        }
        l *= g;
        r *= g;
      }
      // speed wind (not gated by ambientGain: it belongs to the bike); round 4: a stereo rush — the left and right
      // ears get their own noise (the rush past a helmet is uncorrelated above a few hundred Hz), the hiss climbs with speed
      const wW = this.rng.n();
      const rush = this.windBp.process(this.windColour.pink(wR));
      const rushR = this.windDelay[this.windPos]!;
      this.windDelay[this.windPos] = rush;
      if (++this.windPos >= this.windDelay.length) this.windPos = 0;
      const windL = (rush * 2.5 + this.windHp.process(wR) * this.windHi) * this.wind;
      const windR = (rushR * 2.5 + this.windHpR.process(wW) * this.windHi) * this.wind;
      l += windL;
      r += windR;
      L[off + i] = L[off + i]! + l;
      R[off + i] = R[off + i]! + r;
    }
  }
}
