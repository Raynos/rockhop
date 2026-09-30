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
import { PRO_PRICE, type EconomySnapshot } from './economy';
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
  private readonly quick: HTMLButtonElement;
  private readonly previous: HTMLButtonElement;
  private readonly next: HTMLButtonElement;
  private readonly levels: HTMLButtonElement;
  private readonly levelTray: HTMLDivElement;
  private readonly levelSummary: HTMLDivElement;
  private readonly ghost: HTMLButtonElement;
  private readonly orbit: HTMLButtonElement;
  private readonly failure: HTMLDivElement;
  private readonly loadingView: HTMLDivElement;
  private readonly rotate: HTMLDivElement;
  private markers: Marker[] = [];
  private focus = 0;
  private quickIndex = 0;
  private preferredTrack: string | null = null;
  private campaignComplete = false;
  private action = -1;
  private launching = false;
  private map: MountedWorldMap3DShell | null = null;
  private dragMode: 'pan' | 'orbit' = 'pan';
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
    private readonly career?: () => EconomySnapshot,
  ) {
    super(parent, 'tracks-screen worldmap-screen wm3d-enabled');
    injectWorldMapStyles();
    const brand = el('div', 'wm-brand', `<div class="plate"><b class="wordmark">${wordmarkSvg()}</b><span>World map</span></div>${DEV_SURFACES ? `<div class="stamp">${escapeHtml(BUILD_STAMP_SHORT)}</div>` : ''}`);
    this.progress = el('div', 'wm-progress');
    this.detail = el('div', 'wm3d-detail');
    const dock = el('div', 'wm-dock');
    this.previous = el('button', 'wm-step wm-previous', '<span aria-hidden="true">‹</span>');
    this.previous.type = 'button';
    this.previous.setAttribute('aria-label', 'Previous level');
    this.ride = el('button', 'wm-ride');
    this.ride.type = 'button';
    this.next = el('button', 'wm-step wm-next', '<span aria-hidden="true">›</span>');
    this.next.type = 'button';
    this.next.setAttribute('aria-label', 'Next level');
    this.levels = el('button', 'wm-levels', '<span aria-hidden="true">☷</span> Levels');
    this.levels.type = 'button';
    this.levels.setAttribute('aria-expanded', 'false');
    this.levels.setAttribute('aria-controls', 'wm-level-tray');
    this.quick = el('button', 'wm-quick');
    this.quick.type = 'button';
    this.levelTray = el('div', 'wm-level-tray');
    this.levelTray.id = 'wm-level-tray';
    this.levelTray.hidden = true;
    this.levelSummary = el('div', 'wm-level-summary');
    this.ghost = el('button', 'wm-ghost');
    this.ghost.type = 'button';
    this.orbit = el('button', 'wm-orbit', 'Rotate <small>map view</small>');
    this.orbit.type = 'button';
    this.orbit.setAttribute('aria-label', 'Switch map drag to rotate');
    this.orbit.setAttribute('aria-pressed', 'false');
    dock.append(this.progress, this.previous, this.ride, this.next, this.levels, this.quick);
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
    this.root.append(brand, this.detail, this.orbit, this.ghost, this.levelTray, dock, this.loadingView, this.failure, this.rotate, this.legend);
    this.addBackButton('Menu');
    this.ride.addEventListener('click', () => { this.action = -1; this.confirm(); });
    this.quick.addEventListener('click', () => this.launch(this.quickIndex));
    this.previous.addEventListener('click', () => this.step(-1));
    this.next.addEventListener('click', () => this.step(1));
    this.levels.addEventListener('click', () => this.toggleLevels());
    this.ghost.addEventListener('click', () => this.alt());
    this.orbit.addEventListener('click', () => {
      this.dragMode = this.dragMode === 'pan' ? 'orbit' : 'pan';
      this.map?.setDragMode(this.dragMode);
      this.orbit.innerHTML = this.dragMode === 'pan' ? 'Rotate <small>map view</small>' : 'Move <small>map view</small>';
      this.orbit.setAttribute('aria-label', this.dragMode === 'pan' ? 'Switch map drag to rotate' : 'Switch map drag to move');
      this.orbit.setAttribute('aria-pressed', String(this.dragMode === 'orbit'));
    });
    window.addEventListener('resize', () => {
      if (!this.visible) return;
      if (window.innerHeight > window.innerWidth) { this.toggleLevels(false); this.stop3d(); }
      else { this.map?.resize(); void this.start3d(); }
      this.rotate.classList.toggle('show', window.innerHeight > window.innerWidth);
    });
  }

  build(tracks: TrackDef[]): void {
    const state = this.state();
    const medalOf: MedalOf = (id) => this.bestOf(id)?.medal ?? null;
    const ship = shipTracks(tracks, false);
    const economy = this.career?.();
    this.markers = buildCampaignMarkers(ship, medalOf, {
      proOwned: economy?.proOwned ?? state.bikeClass === 'pro', equipped: state.bikeClass,
    }, state.dev);
    if (this.markers.length !== 12) throw new Error(`3D map expected twelve campaign courses; got ${this.markers.length}`);
    const totals = medalTotals(ship, medalOf);
    const dot = (m: Medal, n: number): string => `<span class="${m}" title="${MEDAL_NAME[m]}">${medalSvg(m, MEDAL_NAME[m])}${n}</span>`;
    this.progress.innerHTML = `<span class="n"><b>${totals.cleared}</b> / ${totals.total} cleared</span><span class="dots">${dot('platinum', totals.platinum)}${dot('gold', totals.gold)}${dot('silver', totals.silver)}${dot('bronze', totals.bronze)}</span>${economy ? `<span class="scrap">${economy.wallet} Scrap</span>` : ''}`;
    const target = nextTrack(ship, medalOf, false, state.lastPlayed);
    const quickTarget = nextTrack(ship, medalOf, false, totals.cleared === totals.total ? state.lastPlayed : null);
    this.focus = Math.max(0, this.markers.findIndex((marker) => marker.track.id === (this.preferredTrack ?? target?.id)));
    this.preferredTrack = null;
    this.quickIndex = Math.max(0, this.markers.findIndex((marker) => marker.track.id === quickTarget?.id));
    this.campaignComplete = totals.cleared === totals.total;
    this.action = -1;
    this.renderLevels();
    const nextMarker = this.markers[this.quickIndex]!;
    const quickLabel = nextMarker.garage ? economy?.proOwned ? 'Equip Pro' : (economy?.wallet ?? 0) >= PRO_PRICE ? 'Buy Pro' : 'Earn Scrap' : nextMarker.locked ? 'Locked' : this.campaignComplete ? 'Play again' : 'Play next';
    const quickDetail = nextMarker.garage && !economy?.proOwned && (economy?.wallet ?? 0) < PRO_PRICE
      ? `${PRO_PRICE - (economy?.wallet ?? 0)} more Scrap · improve medals`
      : nextMarker.garage ? nextMarker.rule ?? '' : `${nextMarker.code} · ${nextMarker.track.name}`;
    this.quick.innerHTML = `<span class="play" aria-hidden="true">${nextMarker.garage ? '◆' : '▶'}</span><span>${quickLabel}<small>${escapeHtml(quickDetail)}</small></span>`;
    this.quick.disabled = nextMarker.locked && !nextMarker.garage;
    this.quick.setAttribute('aria-label', nextMarker.locked ? `${quickLabel}: ${nextMarker.code} ${nextMarker.track.name}. ${nextMarker.rule ?? ''}` : `${quickLabel}: ${nextMarker.code} ${nextMarker.track.name}`);
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
      this.map.setDragMode(this.dragMode);
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
    // Each fresh map visit starts with the level-finding gesture.
    this.dragMode = 'pan';
    this.orbit.innerHTML = 'Rotate <small>map view</small>';
    this.orbit.setAttribute('aria-label', 'Switch map drag to rotate');
    this.orbit.setAttribute('aria-pressed', 'false');
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
    this.toggleLevels(false);
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
    const stateLabel = marker.locked ? 'Locked' : marker.medal ? `${MEDAL_NAME[marker.medal]} cleared` : 'Ready to ride';
    const dockState = marker.locked ? 'Locked' : marker.medal ? MEDAL_NAME[marker.medal] : 'Ready';
    const medalRank = marker.medal ? ['bronze', 'silver', 'gold', 'platinum'].indexOf(marker.medal) + 1 : 0;
    const medalLadder = marker.locked ? '' : `<span class="wm-medal-ladder" aria-hidden="true">${(['bronze', 'silver', 'gold', 'platinum'] as const).map((medal, index) => `<i class="${index < medalRank ? medal : 'unearned'}"></i>`).join('')}</span>`;
    const number = String(this.focus + 1).padStart(2, '0');
    this.detail.innerHTML = `<div class="head"><b>${escapeHtml(marker.code)}</b> · ${escapeHtml(stageLabel(marker.region))}</div><div class="name">${escapeHtml(track.name)}</div>${times}${marker.locked ? '' : this.boardHtml(track.id)}<div class="wm3d-state ${marker.locked ? 'locked' : marker.medal ?? 'available'}">${escapeHtml(stateLabel)}</div>`;
    this.detail.dataset['track'] = track.id;
    this.detail.classList.toggle('locked', marker.locked);
    this.ride.disabled = marker.locked && !marker.garage;
    this.ride.innerHTML = `<img class="thumb" src="/art/thumbs/${encodeURIComponent(track.id)}.webp" alt="" loading="lazy"><span class="copy"><strong>${number} · ${escapeHtml(track.name)}</strong><small>${escapeHtml(stageLabel(marker.region))} · <em class="${marker.locked ? 'locked' : marker.medal ?? 'available'}">${escapeHtml(dockState)}</em></small>${marker.locked ? `<small class="rule">${escapeHtml(marker.rule ?? '')}</small>` : medalLadder}</span><span class="ride-arrow" aria-hidden="true">${marker.garage ? 'GARAGE ›' : marker.locked ? '◆' : 'RIDE ›'}</span>`;
    this.ride.setAttribute('aria-label', marker.locked ? `Level ${number}, ${marker.code} ${track.name} locked. ${marker.rule ?? ''}${marker.garage ? ' Open Garage.' : ''}` : `Ride selected level ${number}: ${marker.code} ${track.name}`);
    this.ghost.hidden = !best?.recording || marker.locked;
    this.ghost.innerHTML = `<span>▶</span> ${this.state().ghost ? 'Ghost' : 'Watch PB'}`;
    this.levelSummary.innerHTML = marker.locked
      ? `<b>${number} · ${escapeHtml(track.name)}</b><span>Locked · ${escapeHtml(marker.rule ?? '')}</span>`
      : `<b>${number} · ${escapeHtml(track.name)}</b><span>Best ${best ? formatTime(best.time) : '—'} · Target ${target ? formatTime(target) : '—'}</span>${this.boardHtml(track.id)}`;
    for (const button of this.levelTray.querySelectorAll<HTMLButtonElement>('[data-index]')) button.classList.toggle('selected', Number(button.dataset['index']) === this.focus);
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

  private step(direction: -1 | 1): void {
    if (this.launching || !this.markers.length) return;
    this.focusMarker((this.focus + direction + this.markers.length) % this.markers.length, true);
  }

  private toggleLevels(force?: boolean): void {
    const open = force ?? this.levelTray.hidden;
    this.levelTray.hidden = !open;
    this.levels.setAttribute('aria-expanded', String(open));
  }

  private renderLevels(): void {
    this.levelTray.replaceChildren();
    const header = el('div', 'wm-level-tray-head', '<strong>Choose a level</strong><span>Tap a stop to focus it on the island</span>');
    const grid = el('div', 'wm-level-grid');
    this.markers.forEach((marker, index) => {
      const button = el('button', `wm-level ${marker.locked ? 'locked' : marker.medal ?? 'available'}`,
        `<b>${String(index + 1).padStart(2, '0')}</b><span>${escapeHtml(marker.track.name)}</span><small>${marker.locked ? '◆' : marker.medal ? medalSvg(marker.medal, MEDAL_NAME[marker.medal]) : '○'}</small>`);
      button.type = 'button';
      button.dataset['index'] = String(index);
      button.setAttribute('aria-label', `${marker.code} ${marker.track.name}, ${marker.locked ? 'locked' : marker.medal ? `${MEDAL_NAME[marker.medal]} cleared` : 'ready to ride'}`);
      button.addEventListener('click', () => { this.focusMarker(index, true); this.toggleLevels(false); });
      grid.append(button);
    });
    this.levelTray.append(header, grid, this.levelSummary);
  }

  current(): { marker: Marker } | null {
    return this.markers[this.focus] ? { marker: this.markers[this.focus]! } : null;
  }

  /** A rejected direct launch lands on its locked tower so the reason and Garage action are visible. */
  preferTrack(id: string): void { this.preferredTrack = id; }

  currentRegion(): RegionId | null {
    return this.markers[this.focus]?.region ?? null;
  }

  override setDevice(device: 'keyboard' | 'gamepad' | 'touch' | null): void {
    if (!this.legend) return;
    this.legend.innerHTML = device === 'touch' ? '<span>Tap a tower</span><span>Drag to move · Rotate button · pinch to zoom</span>'
      : device === 'gamepad' ? '<span><i class="pad">✚</i>Tracks</span><span><i class="pad a">A</i>Ride</span><span><i class="pad b">B</i>Back</span>'
        : '<span><kbd>←→</kbd>Tracks</span><span><kbd>Enter</kbd>Ride</span><span><kbd>V</kbd>Ghost</span><span>Drag to move · right drag to orbit</span><span><kbd>Esc</kbd>Back</span>';
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
    if (this.action === 1) return this.alt();
    this.launch(this.focus);
  }

  private launch(index: number): void {
    const marker = this.markers[index];
    if (!marker || this.launching) return;
    if (marker.locked) {
      if (marker.garage) {
        this.sfx.confirm();
        if (this.cb.openProGarage) this.cb.openProGarage();
        else this.cb.goto('garage');
        return;
      }
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
    if (!this.levelTray.hidden) { this.toggleLevels(false); this.sfx.back(); return; }
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
