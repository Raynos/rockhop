import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { expect, it } from 'vitest';

it('keeps both shipped Street wrist rings sewn through Garage and riding poses', () => {
  const temporary = fs.mkdtempSync(path.join(os.tmpdir(), 'rockhop-wrist-seams-'));
  const report = path.join(temporary, 'report.json');
  try {
    execFileSync(process.execPath, ['--import', 'tsx', 'harness/hero-remaster/wrist-seams.mts',
      '--full=public/models/rider-street-mustard.glb',
      '--full-map=assets/blender/hero-remaster/delivery/rider-street-mustard.glb.seams.json',
      '--lod=public/models/rider-street-mustard-lod.glb',
      '--lod-map=assets/blender/hero-remaster/delivery/rider-street-mustard-lod.glb.seams.json',
      `--out=${report}`,
    ], { timeout: 30_000, maxBuffer: 1024 * 1024 });
    const result = JSON.parse(fs.readFileSync(report, 'utf8'));
    expect(result.pass).toBe(true);
    expect(result.subjects.map((s: { subject: string }) => s.subject)).toEqual(['full', 'lod']);
    for (const subject of result.subjects) {
      expect(subject.topology).toHaveLength(4);
      expect(subject.poses).toHaveLength(7);
    }
  } finally { fs.rmSync(temporary, { recursive: true, force: true }); }
}, 35_000);
