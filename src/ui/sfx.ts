/** Cached PCM from the game's D-key cue family, unlocked by a user gesture. */
import { silentAutomation } from '../audio/automation';
import { renderMenuCue, type MenuCue } from '../audio/dsp/ui';

interface ContextSource {
  context?: AudioContext | null;
}

export class UiSfx {
  private ctx: AudioContext | null = null;
  private gain: GainNode | null = null;
  private readonly buffers = new Map<MenuCue, AudioBuffer>();
  private volume = 1;
  private enabled = true;
  private lastTick = -Infinity;

  constructor(private readonly source?: ContextSource) {}

  setVolume(v: number): void {
    this.volume = Math.max(0, Math.min(1, v));
    if (this.gain) this.gain.gain.value = this.enabled ? this.volume * this.volume : 0;
  }

  setEnabled(on: boolean): void {
    this.enabled = on;
    if (this.gain) this.gain.gain.value = on ? this.volume * this.volume : 0;
  }

  private context(): AudioContext | null {
    if (!this.enabled || this.volume <= 0 || silentAutomation()) return null;
    const shared = this.source?.context ?? null;
    if (shared && this.ctx && this.ctx !== shared) {
      const previous = this.ctx;
      this.ctx = null;
      void previous.close().catch(() => undefined);
    }
    if (!(shared ?? this.ctx)) {
      if (typeof AudioContext === 'undefined') return null;
      try {
        this.ctx = new AudioContext({ latencyHint: 'interactive' });
      } catch {
        return null;
      }
    }
    const c = (shared ?? this.ctx)!;
    if (c.state === 'suspended') void c.resume().catch(() => undefined);
    if (!this.gain || this.gain.context !== c) {
      this.gain?.disconnect();
      this.buffers.clear();
      this.gain = c.createGain();
      this.gain.gain.value = this.volume * this.volume;
      this.gain.connect(c.destination);
    }
    return c;
  }

  private play(cue: MenuCue): void {
    const c = this.context();
    if (!c || !this.gain) return;
    let buffer = this.buffers.get(cue);
    if (!buffer) {
      const pcm = renderMenuCue(cue, c.sampleRate);
      buffer = c.createBuffer(2, pcm[0].length, c.sampleRate);
      buffer.getChannelData(0).set(pcm[0]);
      buffer.getChannelData(1).set(pcm[1]);
      this.buffers.set(cue, buffer);
    }
    const voice = c.createBufferSource();
    voice.buffer = buffer;
    voice.connect(this.gain);
    voice.onended = () => voice.disconnect();
    voice.start();
  }

  /** Focus moved. A held stick gets at most one quiet click every 40 ms. */
  tick(): void {
    const now = performance.now();
    if (now - this.lastTick < 40) return;
    this.lastTick = now;
    this.play('menuFocus');
  }

  confirm(): void { this.play('menuConfirm'); }
  back(): void { this.play('menuBack'); }
  launch(): void { this.play('menuLaunch'); }
}
