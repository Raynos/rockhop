/// <reference types="vite/client" />
/** Twelve-course 3D island level select. */
import type { BikeClass, Medal, TrackDef } from '../core/types';
import type { ArtManifest } from './art';
import type { BestEntry, BoardEntry } from './best';
import { formatTime } from './format';
import { BUILD_STAMP_SHORT, escapeHtml, Screen, type FrontCallbacks, type FrontState } from './front';
import { DEV_SURFACES } from '../core/release';
import { MEDAL_NAME, medalSvg, wordmarkSvg } from './brand';
import { medalTotals, nextTrack, shipTracks, stageLabel, type MedalOf } from './progress';
import type { UiSfx } from './sfx';
import { buildCampaignMarkers, type Marker, type RegionId } from './campaignMap';
import { injectWorldMapStyles } from './worldMapStyles';
import type { MountedWorldMap3DShell } from './worldMap3dScene';

function el<K extends keyof HTMLElementTagNameMap>(tag: K, cls?: string, html?: string): HTMLElementTagNameMap[K] {
  const node = document.createElement(tag);
  if (cls) node.className = cls;
  if (html !== undefined) node.innerHTML = html;
  return node;
}

export interface WorldMapGpuHooks {
  before3d(): Promise<boolean>;
  after3d(): Promise<boolean> | boolean;
}

export class WorldMapScreen extends Screen {
  private readonly progress: HTMLDivElement;
  private readonly detail: HTMLDivElement;
  private readonly ride: HTMLButtonElement;
  private readonly ghost: HTMLButtonElement;
  private readonly failure: HTMLDivElement;
  private readonly loadingView: HTMLDivElement;
  private readonly rotate: HTMLDivElement;
  private markers: Marker[] = [];
  private focus = 0;
  private action = -1;
  private launching = false;
  private map: MountedWorldMap3DShell | null = null;
  private loading = false;
  private token = 0;
  private gpuOwned = false;
  private restorePromise: Promise<boolean> = Promise.resolve(true);

  constructor(
    parent: HTMLElement,
    private readonly sfx: UiSfx,
    _art: ArtManifest,
    private readonly cb: FrontCallbacks,
    private readonly bestOf: (id: string) => BestEntry | null,
    private readonly state: () => FrontState,
    private readonly boardOf?: (id: string, bike: BikeClass) => BoardEntry[],
    private readonly gpu?: WorldMapGpuHooks,
  ) {
    super(parent, 'tracks-screen worldmap-screen wm3d-enabled');
    injectWorldMapStyles();
    const brand = el('div', 'wm-brand', `<div class="plate"><b class="wordmark">${wordmarkSvg()}</b><span>World map</span></div>${DEV_SURFACES ? `<div class="stamp">${escapeHtml(BUILD_STAMP_SHORT)}</div>` : ''}`);
    this.progress = el('div', 'wm-progress');
    this.detail = el('div', 'wm3d-detail');
    const actions = el('div', 'wm-actions');
    this.ride = el('button', 'wm-ride');
    this.ride.type = 'button';
    this.ghost = el('button', 'wm-ghost');
    this.ghost.type = 'button';
    actions.append(this.ride, this.ghost);
    this.failure = el('div', 'wm3d-failure', '<strong>Map unavailable</strong><p>The 3D map could not start. Try again.</p>');
    const retry = el('button', '', 'Retry map');
    retry.type = 'button';
    retry.addEventListener('click', () => void this.start3d());
    const menu = el('button', '', 'Menu');
    menu.type = 'button';
    menu.addEventListener('click', () => this.back());
    this.failure.append(retry, menu);
    this.loadingView = el('div', 'wm3d-loading', '<span class="spinner"></span><strong>Opening world map</strong>');
    const loadingMenu = el('button', '', 'Menu');
    loadingMenu.type = 'button';
    loadingMenu.addEventListener('click', () => this.back());
    this.loadingView.append(loadingMenu);
    this.rotate = el('div', 'wm3d-rotate', '<span>↻</span><strong>Rotate your phone</strong><small>ROCKHOP plays in landscape</small>');
    this.legend = el('div', 'legend');
    this.root.append(brand, this.progress, this.detail, actions, this.loadingView, this.failure, this.rotate, this.legend);
    this.addBackButton('Menu');
    this.ride.addEventListener('click', () => { this.action = -1; this.confirm(); });
    this.ghost.addEventListener('click', () => this.alt());
    window.addEventListener('resize', () => {
      if (!this.visible) return;
      if (window.innerHeight > window.innerWidth) this.stop3d();
      else { this.map?.resize(); void this.start3d(); }
      this.rotate.classList.toggle('show', window.innerHeight > window.innerWidth);
    });
  }

  build(tracks: TrackDef[]): void {
    const state = this.state();
    const medalOf: MedalOf = (id) => this.bestOf(id)?.medal ?? null;
    const ship = shipTracks(tracks, false);
    this.markers = buildCampaignMarkers(ship, medalOf);
    if (this.markers.length !== 12) throw new Error(`3D map expected twelve campaign courses; got ${this.markers.length}`);
    const totals = medalTotals(ship, medalOf);
    const dot = (m: Medal, n: number): string => `<span class="${m}" title="${MEDAL_NAME[m]}">${medalSvg(m, MEDAL_NAME[m])}${n}</span>`;
    this.progress.innerHTML = `<span class="n"><b>${totals.cleared}</b> / ${totals.total} cleared</span><span class="dots">${dot('platinum', totals.platinum)}${dot('gold', totals.gold)}${dot('silver', totals.silver)}${dot('bronze', totals.bronze)}</span>`;
    const target = nextTrack(ship, medalOf, false, state.lastPlayed);
    this.focus = Math.max(0, this.markers.findIndex((marker) => marker.track.id === target?.id));
    this.action = -1;
    this.renderFocus(false);
    this.map?.setProgress(this.markers.map((marker) => marker.locked), this.markers.map((marker) => marker.medal));
  }

  private async start3d(): Promise<void> {
    if (!this.visible || this.map || this.loading) return;
    if (window.innerHeight > window.innerWidth) { this.rotate.classList.add('show'); return; }
    this.rotate.classList.remove('show');
    const token = ++this.token;
    this.loading = true;
    this.failure.classList.remove('show');
    this.loadingView.classList.add('show');
    try {
      await this.restorePromise;
      if (token !== this.token || !this.visible) return;
      if (this.gpu && !this.gpuOwned) {
        if (!(await this.gpu.before3d())) throw new Error('Game renderer could not release the GPU context');
        if (token !== this.token || !this.visible) { this.restorePromise = Promise.resolve(this.gpu.after3d()); return; }
        this.gpuOwned = true;
      }
      const { mountWorldMap3DShell } = await import('./worldMap3dScene');
      if (token !== this.token || !this.visible) return;
      this.map = mountWorldMap3DShell(this.root, (index) => this.focusMarker(index, true), this.focus,
        this.markers.map((marker) => marker.locked), this.markers.map((marker) => marker.medal), (error) => this.mapFailed(error));
      this.renderFocus(false);
      this.loadingView.classList.remove('show');
    } catch (error) {
      if (token === this.token) this.mapFailed(error);
    } finally {
      if (token === this.token) this.loading = false;
    }
  }

  private mapFailed(error: unknown): void {
    console.error('3D world map unavailable', error);
    this.map?.dispose();
    this.map = null;
    this.loadingView.classList.remove('show');
    this.restoreGpu();
    this.failure.classList.add('show');
  }

  private stop3d(): void {
    this.token++;
    this.loading = false;
    this.map?.dispose();
    this.map = null;
    this.loadingView.classList.remove('show');
    this.restoreGpu();
  }

  private restoreGpu(): void {
    if (!this.gpuOwned) return;
    this.restorePromise = Promise.resolve(this.gpu!.after3d());
    this.gpuOwned = false;
  }

  override show(): void {
    this.launching = false;
    super.show();
    this.rotate.classList.toggle('show', window.innerHeight > window.innerWidth);
    void this.start3d();
  }

  override hide(): void {
    this.stop3d();
    super.hide();
  }

  private boardHtml(id: string): string {
    const bike = this.state().bikeClass;
    const rows = this.boardOf?.(id, bike) ?? [];
    return rows.length ? `<div class="board" data-bike="${bike}" data-rows="${rows.length}">${rows.map((entry, i) => `<span class="${entry.medal}" title="#${i + 1} ${bike} · ${formatTime(entry.time)} · ${entry.faults} bails">${formatTime(entry.time)}</span>`).join('')}</div>` : '';
  }

  private renderFocus(animate: boolean): void {
    const marker = this.markers[this.focus];
    if (!marker) return;
    const track = marker.track;
    const best = this.bestOf(track.id);
    const target = track.meta?.targetTimeS;
    const times = marker.locked ? `<div class="rule">Locked · ${escapeHtml(marker.rule ?? '')}</div>`
      : `<div class="times"><b class="${best ? '' : 'none'}">${best ? formatTime(best.time) : '—'}</b> / ${target ? formatTime(target) : '—'}</div>`;
    this.detail.innerHTML = `<div class="head"><b>${escapeHtml(marker.code)}</b> · ${escapeHtml(stageLabel(marker.region))}</div><div class="name">${escapeHtml(track.name)}</div>${times}${marker.locked ? '' : this.boardHtml(track.id)}${marker.medal && !marker.locked ? `<div class="wm3d-medal ${marker.medal}">${escapeHtml(MEDAL_NAME[marker.medal])} cleared</div>` : ''}`;
    this.detail.dataset['track'] = track.id;
    this.detail.classList.toggle('locked', marker.locked);
    this.ride.disabled = marker.locked;
    this.ride.innerHTML = marker.locked ? `Locked <small>${escapeHtml(marker.rule ?? '')}</small>` : `Ride <small>${escapeHtml(track.name)}</small><span class="arrow">›</span>`;
    this.ghost.hidden = !best?.recording || marker.locked;
    this.ghost.innerHTML = `<span>▶</span> ${this.state().ghost ? 'Ghost' : 'Watch PB'}`;
    this.map?.selectStage(this.focus, animate);
    this.applyAction();
  }

  private applyAction(): void {
    this.ride.classList.toggle('on', this.action === 0);
    this.ghost.classList.toggle('on', this.action === 1);
  }

  private focusMarker(index: number, tick: boolean): void {
    if (this.launching || !this.markers[index]) return;
    const moved = index !== this.focus || this.action >= 0;
    this.focus = index;
    this.action = -1;
    if (tick && moved) this.sfx.tick();
    this.renderFocus(moved);
  }

  current(): { marker: Marker } | null {
    return this.markers[this.focus] ? { marker: this.markers[this.focus]! } : null;
  }

  currentRegion(): RegionId | null {
    return this.markers[this.focus]?.region ?? null;
  }

  override setDevice(device: 'keyboard' | 'gamepad' | 'touch' | null): void {
    if (!this.legend) return;
    this.legend.innerHTML = device === 'touch' ? '<span>Tap a tower</span><span>Drag to orbit · pinch to zoom</span>'
      : device === 'gamepad' ? '<span><i class="pad">✚</i>Tracks</span><span><i class="pad a">A</i>Ride</span><span><i class="pad b">B</i>Back</span>'
        : '<span><kbd>←→</kbd>Tracks</span><span><kbd>Enter</kbd>Ride</span><span><kbd>V</kbd>Ghost</span><span>Drag to orbit</span><span><kbd>Esc</kbd>Back</span>';
  }

  nav(dx: number, dy: number): void {
    if (this.launching || this.markers.length === 0) return;
    if (this.action >= 0) {
      if (dy < 0) this.action = -1;
      else if (dx) this.action = Math.max(0, Math.min(this.ghost.hidden ? 0 : 1, this.action + dx));
      this.sfx.tick();
      this.applyAction();
      return;
    }
    if (dx) this.focusMarker((this.focus + dx + this.markers.length) % this.markers.length, true);
    else if (dy > 0) { this.action = 0; this.sfx.tick(); this.applyAction(); }
    else if (dy < 0) this.focusMarker((this.focus - 1 + this.markers.length) % this.markers.length, true);
  }

  confirm(): void {
    const marker = this.markers[this.focus];
    if (!marker || this.launching) return;
    if (this.action === 1) return this.alt();
    if (marker.locked) {
      this.sfx.back();
      this.ride.animate?.([{ translate: '0 0' }, { translate: '-6px 0' }, { translate: '6px 0' }, { translate: '0 0' }], { duration: 240 });
      return;
    }
    this.launching = true;
    this.sfx.launch();
    setTimeout(() => this.cb.play(marker.track.id), 180);
    setTimeout(() => this.root.classList.add('leave'), 200);
    setTimeout(() => { this.hide(); this.launching = false; }, 420);
  }

  back(): void {
    if (this.launching) return;
    this.sfx.back();
    this.cb.goto('menu');
  }

  override alt(): void {
    const marker = this.markers[this.focus];
    if (!marker || marker.locked || this.launching || !this.bestOf(marker.track.id)?.recording) return;
    this.sfx.confirm();
    this.cb.watchPb(marker.track.id);
  }
}
