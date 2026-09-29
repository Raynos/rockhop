export interface MountedWorldMap3D {
  selectStage(index: number, focus?: boolean): void;
  setLocked(locked: boolean[]): void;
  setProgress(locked: boolean[], medals: (string | null)[]): void;
  setDragMode(mode: 'pan' | 'orbit'): void;
  viewState(): { dragMode: 'pan' | 'orbit'; target: { x: number; y: number; z: number }; azimuth: number; distance: number; states: string[] };
  resize(): void;
  dispose(): void;
  stats(): { fps: number; drawCalls: number; triangles: number; meshMerge: { mergedObjects: number; mergedBatches: number }; selected: number; disposed: boolean };
  towerScreenPoint(index: number): { x: number; y: number } | null;
}

export function mountWorldMap3D(root: HTMLElement, onSelect: (index: number) => void, initialIndex?: number, locked?: boolean[], medals?: (string | null)[]): MountedWorldMap3D;

export interface MountedWorldMap3DShell {
  selectStage(index: number, focus?: boolean): void;
  setLocked(locked: boolean[]): void;
  setProgress(locked: boolean[], medals: (string | null)[]): void;
  setDragMode(mode: 'pan' | 'orbit'): void;
  resize(): void;
  dispose(): void;
}

export function mountWorldMap3DShell(root: HTMLElement, onSelect: (index: number) => void, initialIndex?: number, locked?: boolean[], medals?: (string | null)[], onError?: (error: unknown) => void): MountedWorldMap3DShell;
