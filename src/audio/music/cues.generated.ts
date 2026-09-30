// Written by assets/audio/pipeline/remaster_master.py — do not edit by hand.
import type { CueFile, MusicCue } from './cues';

export const CUE_FILES: Partial<Record<MusicCue, CueFile>> = {
  menu: { file: 'menu-5246888f.mp3', loop: true, pre: 0.5, len: 33.506395833333336, gainDb: 0, bpm: 85.9537, bytes: 691245 },
  map: { file: 'map-768b83c4.mp3', loop: true, pre: 0.5, len: 26.958375, gainDb: 0, bpm: 71.2209, bytes: 560205 },
  coast: { file: 'coast-138653e7.mp3', loop: true, pre: 0.5, len: 24.891791666666666, gainDb: 0, bpm: 115.7008, bytes: 518925 },
  alpine: { file: 'alpine-9593e6b7.mp3', loop: true, pre: 0.5, len: 29.930520833333333, gainDb: 0, bpm: 96.2228, bytes: 619725 },
  quarry: { file: 'quarry-fe5dba27.mp3', loop: true, pre: 0.5, len: 32.4150625, gainDb: 0, bpm: 88.8476, bytes: 669645 },
  snowline: { file: 'snowline-cb054b7b.mp3', loop: true, pre: 0.5, len: 22.3608125, gainDb: 0, bpm: 128.7968, bytes: 468525 },
  results: { file: 'results-6b8f5a93.mp3', loop: false, pre: 0, len: 4.0, gainDb: 0, bpm: 85.9537, bytes: 81165 },
};
