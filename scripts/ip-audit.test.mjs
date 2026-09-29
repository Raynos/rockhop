// The IP audit's matching rules (scripts/ip-audit-rules.mjs): the cases that decide whether bar 1 means anything.
import { describe, expect, it } from 'vitest';
import { spawnSync } from 'node:child_process';
import { mkdtempSync, mkdirSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { GENERIC_LEVEL_NAMES, assetRightsHits, auditText, franchiseHits, levelHits } from './ip-audit-rules.mjs';

const auditScript = join(dirname(fileURLToPath(import.meta.url)), 'ip-audit.mjs');

describe('strict artifact scan', () => {
  it('rejects the disputed facial-hair mesh when it returns to a release GLB', () => {
    const root = mkdtempSync(join(tmpdir(), 'rockhop-ip-audit-'));
    try {
      const models = join(root, 'models');
      mkdirSync(models, { recursive: true });
      const json = Buffer.from(JSON.stringify({ nodes: [{ name: 'Street01_grinsegold_full_beard_Runtime' }] }));
      const padded = Buffer.alloc(Math.ceil(json.length / 4) * 4, 0x20);
      json.copy(padded);
      const glb = Buffer.alloc(20 + padded.length);
      glb.writeUInt32LE(0x46546c67, 0);
      glb.writeUInt32LE(2, 4);
      glb.writeUInt32LE(glb.length, 8);
      glb.writeUInt32LE(padded.length, 12);
      glb.writeUInt32LE(0x4e4f534a, 16);
      padded.copy(glb, 20);
      writeFileSync(join(models, 'rider.glb'), glb);
      const run = spawnSync(process.execPath, [auditScript, '--strict', '--json', root], { encoding: 'utf8' });
      expect(run.status).toBe(1);
      const report = JSON.parse(run.stdout);
      expect(report.byFile['models/rider.glb'] ?? Object.values(report.byFile)[0]).toMatchObject({ grinsegold: 1, full_beard: 1 });
    } finally {
      rmSync(root, { recursive: true, force: true });
    }
  });

  it('finds a retired brand name inside the Capacitor build/web payload when scanning its parent', () => {
    const root = mkdtempSync(join(tmpdir(), 'rockhop-ip-audit-'));
    try {
      const web = join(root, 'store', 'build', 'web');
      mkdirSync(web, { recursive: true });
      writeFileSync(join(web, 'index.html'), '<title>Trials Gauntlet</title>');
      const run = spawnSync(process.execPath, [auditScript, '--strict', '--json', join(root, 'store')], { encoding: 'utf8' });
      expect(run.status).toBe(1);
      expect(run.stderr).toBe('');
      const report = JSON.parse(run.stdout);
      expect(Object.entries(report.byFile).find(([f]) => f.endsWith('/store/build/web/index.html'))?.[1]).toEqual({ trials: 1, gauntlet: 1 });
    } finally {
      rmSync(root, { recursive: true, force: true });
    }
  });

  it('fails when an explicitly requested release payload is missing', () => {
    const root = mkdtempSync(join(tmpdir(), 'rockhop-ip-audit-'));
    try {
      const web = join(root, 'store', 'build', 'web');
      const run = spawnSync(process.execPath, [auditScript, '--strict', '--json', web], { encoding: 'utf8' });
      expect(run.status).toBe(1);
      const report = JSON.parse(run.stdout);
      expect(report.missing).toHaveLength(1);
      expect(report.missing[0]).toMatch(/\/store\/build\/web$/);
      expect(report.scanned).toBe(0);
    } finally {
      rmSync(root, { recursive: true, force: true });
    }
  });
});

describe('franchise terms: case-insensitive, whole words, strict', () => {
  it.each([
    ['Trials Gauntlet', 'trials', 1],
    ['TRIALS', 'trials', 1],
    ['trials-gauntlet-demo', 'trials', 1],
    ['trials-gauntlet-demo', 'gauntlet', 1],
    ['trials-gauntlet-demo', 'demo', 1],
    ['localStorage["trials.best"]', 'trials', 1],
    ['trials_key', 'trials', 1],
    ['isTrialsMode', 'trials', 1],
    ['trialsKey', 'trials', 1],
    ['x3-gauntlet', 'gauntlet', 1],
    ['Gauntlets', 'gauntlet', 1],
    ['demos', 'demo', 1],
    ['demo2', 'demo', 1],
    ['Trials Rising', 'rising', 1],
    ['The Rising Pillars', 'rising', 1],
    ['No Fear', 'no fear', 1],
    ['a RedLynx title', 'redlynx', 1],
    ['Ubisoft', 'ubisoft', 1],
  ])('%j counts %s', (text, term, n) => {
    expect(franchiseHits(text, term)).toBe(n);
  });

  it.each([
    // The OFL licence texts: "arising" is the licence's own word, not the franchise.
    ['OTHER DEALINGS IN THE FONT SOFTWARE ... ARISING FROM, OUT OF THE USE', 'rising'],
    ['or other liability, whether in an action of contract, tort or otherwise, arising from', 'rising'],
    ['demonstrate', 'demo'],
    ['prodemo', 'demo'],
    ['demolish', 'demo'],
    ['confusion', 'fusion'],
    ['revolution', 'evolution'],
    ['retrials', 'trials'],
  ])('%j does not count %s', (text, term) => {
    expect(franchiseHits(text, term)).toBe(0);
  });
});

describe('retired level names: case-sensitive; generic names only as a title', () => {
  it('the generic names are the riding-vocabulary curriculum names', () => {
    for (const n of ['Lean Back', 'See-Saw', 'Hop Up', 'Stairway', 'Uphill Weight', 'Rear Wheel First', 'First Ride', 'Kicker Row', 'Drum Roll']) expect(GENERIC_LEVEL_NAMES.has(n)).toBe(true);
    for (const n of ['The Stack', 'The Rolling Mill', 'Container Yard', 'Canyon Run']) expect(GENERIC_LEVEL_NAMES.has(n)).toBe(false);
  });

  it.each([
    // hints, tutorials and segment labels share the riding words: never a title
    ['Lean back if the nose drops', 'Lean Back'],
    ['"Lean back if the nose drops"', 'Lean Back'],
    ['hint("Lean Back to land the drop")', 'Lean Back'],
    ['LEAN BACK', 'Lean Back'],
    ['"LEAN BACK"', 'Lean Back'],
    ['the see-saw tips at its centre', 'See-Saw'],
    ['"Gap onto the see-saw"', 'See-Saw'],
    ['See-Saw ahead: slow down', 'See-Saw'],
    ['Stairway: hop each step', 'Stairway'],
    ['"hop up the ledge"', 'Hop Up'],
    ['first ride of the day', 'First Ride'],
    ['a drum roll plays', 'Drum Roll'],
    // distinctive names are title case: lower-case prose is not the name, nor a longer word
    ['Copy the stack trace', 'The Stack'],
    ['"the stack"', 'The Stack'],
    ['Snowline', 'Snow Line'],
    ['SNOWLINE', 'Snow Line'],
    ['The Stacks', 'The Stack'],
  ])('%j does not count %s', (text, name) => {
    expect(levelHits(text, name)).toBe(0);
  });

  it.each([
    // a title: the whole of a string literal, a JSON value or an HTML text node
    ['{name:"Lean Back",tier:"beginner"}', 'Lean Back', 1],
    ["course('b2-lean-back', 'Lean Back', 'beginner')", 'Lean Back', 1],
    ['<h2>See-Saw</h2>', 'See-Saw', 1],
    ['<b> Stairway </b>', 'Stairway', 1],
    ['`Hop Up`', 'Hop Up', 1],
    ['"name": "Rear Wheel First"', 'Rear Wheel First', 1],
    // distinctive names count anywhere, as authored or in capitals
    ['Next: The Stack', 'The Stack', 1],
    ['THE ROLLING MILL', 'The Rolling Mill', 1],
    ['"Container Yard"', 'Container Yard', 1],
    ['canyon: Canyon Run!', 'Canyon Run', 1],
    ['Flat 200m', 'Flat 200', 0],
  ])('%j counts %s ×%i', (text, name, n) => {
    expect(levelHits(text, name)).toBe(n);
  });
});

describe('auditText', () => {
  it('reports per term, a name that is a franchise term once, nothing for clean text', () => {
    expect(auditText('Trials Gauntlet: The Stack, "Lean Back"', ['The Stack', 'Lean Back', 'Gauntlet'])).toEqual({ trials: 1, gauntlet: 1, 'The Stack': 1, 'Lean Back': 1 });
    expect(auditText('ROCKHOP. Lean back if the nose drops. Licence: ARISING FROM', ['Lean Back'])).toEqual({});
  });
});

describe('known rights exclusions', () => {
  it('scans GLB JSON names without flagging ordinary game copy', () => {
    expect(assetRightsHits('{"name":"Moustache_black_diff"}')).toEqual({ moustache: 1 });
    expect(assetRightsHits('{"name":"rockhop_rider_skin"}')).toEqual({});
  });
});
