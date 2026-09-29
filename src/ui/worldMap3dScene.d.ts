export interface MountedWorldMap3D {
  selectStage(index: number, focus?: boolean): void;
  setLocked(locked: boolean[]): void;
  setProgress(locked: boolean[], medals: (string | null)[]): void;
  resize(): void;
  dispose(): void;
  stats(): { fps: number; drawCalls: number; triangles: number; meshMerge: { mergedObjects: number; mergedBatches: number }; selected: number; disposed: boolean };
  towerScreenPoint(index: number): { x: number; y: number } | null;
}

export function mountWorldMap3D(root: HTMLElement, onSelect: (index: number) => void, initialIndex?: number, locked?: boolean[], medals?: (string | null)[]): MountedWorldMap3D;

export interface MountedWorldMap3DReview {
  selectStage(index: number, focus?: boolean): void;
  setLocked(locked: boolean[]): void;
  setProgress(locked: boolean[], medals: (string | null)[]): void;
  setDetail(html: string, id: string, locked: boolean, medal?: string | null): void;
  resize(): void;
  dispose(): void;
}

export function mountWorldMap3DReview(root: HTMLElement, onSelect: (index: number) => void, initialIndex?: number, locked?: boolean[], medals?: (string | null)[]): MountedWorldMap3DReview;
