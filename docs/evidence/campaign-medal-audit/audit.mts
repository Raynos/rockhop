/** Recalculate the live 12-course medal clocks against pinned skill-3 recordings. Silent Node only. */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { execFileSync } from 'node:child_process';
import { expandFrames } from '../../../src/core/replay';
import { medalFor, targetForBike } from '../../../src/game/rules';
import { ROCKHOP_TRACKS } from '../../../src/tracks/rockhop';
import { CareerEconomy, PRO_PRICE, SCRAP_REWARD } from '../../../src/ui/economy';
import { trackUnlocked } from '../../../src/ui/progress';
import { createSimFor } from '../../../harness/lib/sim';
import { loadRecording } from '../../../harness/lib/recording';
import { srcFingerprint } from '../../../harness/lib/metrics';
import type { BikeClass, Medal } from '../../../src/core/types';

const outDir = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(outDir, '../../..');
const startFingerprint = srcFingerprint();
const round = (n: number | null, places = 3): number | null => n === null ? null : Number(n.toFixed(places));
const rows: Record<string, unknown>[] = [];
const byCourse = new Map<string, Record<BikeClass, { medal: Medal; clean: boolean } | null>>();

for (const [index, course] of ROCKHOP_TRACKS.entries()) {
  const result: Record<BikeClass, { medal: Medal; clean: boolean } | null> = { rookie: null, pro: null };
  byCourse.set(course.id, result);
  for (const bike of ['rookie', 'pro'] as const) {
    const relative = `harness/inputs/${course.id}/bot-3${bike === 'pro' ? '-pro' : ''}.json`;
    const file = path.join(root, relative);
    const goldS = targetForBike(course.def.meta?.targetTimeS as number | undefined, bike);
    const diamondS = goldS === null ? null : goldS * 0.85;
    const base = { index: index + 1, code: course.code, courseId: course.id, zone: course.zone, bike, reference: fs.existsSync(file) ? relative : null,
      goldS: round(goldS), silverS: round(goldS === null ? null : goldS * 1.25), diamondS: round(diamondS), diamondGoal: course.def.diamondGoal?.id ?? null };
    if (!fs.existsSync(file)) {
      rows.push({ ...base, status: 'missing-recording', clean: null, clearS: null, faults: null, medal: null });
      continue;
    }
    const recording = loadRecording(file);
    if (recording.header.trackId !== course.id || (recording.header.bike ?? 'rookie') !== bike) throw new Error(`recording mismatch ${relative}`);
    const sim = await createSimFor(recording);
    sim.run(expandFrames(recording));
    const phase = sim.phase();
    const clearS = phase === 'finished' ? sim.runTime() : null;
    const faults = sim.faults();
    const clean = phase === 'finished' && faults === 0;
    const crossed = course.def.diamondGoal ? sim.rules.counters().diamondRouteCrossed === true : null;
    const medal = clearS === null ? null : medalFor(clearS, faults, course.def.meta?.targetTimeS as number | undefined, bike, crossed ?? undefined);
    const row = { ...base, status: phase === 'finished' ? (clean ? 'clean' : 'faulted-clear') : phase, clean,
      clearS: round(clearS), faults, medal, rewardScrap: medal ? SCRAP_REWARD[medal] : null,
      ratioToGold: round(clearS !== null && goldS !== null ? clearS / goldS : null), goldHeadroomS: round(clearS !== null && goldS !== null ? goldS - clearS : null),
      diamondClockPasses: clean && clearS !== null && diamondS !== null ? clearS <= diamondS : false,
      diamondHeadroomS: round(clearS !== null && diamondS !== null ? diamondS - clearS : null), diamondRouteCrossed: crossed,
      sourceStamp: /\bsrc=([a-f0-9]+)/.exec(recording.header.note ?? '')?.[1] ?? null, hash: sim.hash() };
    rows.push(row);
    if (medal) result[bike] = { medal, clean };
  }
}

function unlockPath(name: string, medalForCourse: (_id: string, index: number) => Medal) {
  const economy = new CareerEconomy(null);
  const medals = new Map<string, Medal>();
  const steps: Record<string, unknown>[] = [];
  const tracks = ROCKHOP_TRACKS.map(r => r.def);
  for (const [index, course] of ROCKHOP_TRACKS.entries()) {
    const medal = medalForCourse(course.id, index);
    const award = economy.award(course.id, medal);
    medals.set(course.id, medal);
    steps.push({ after: course.code, index: index + 1, medal, earned: award.delta, wallet: award.wallet, proAffordable: award.wallet >= PRO_PRICE,
      d3Unlocked: trackUnlocked(tracks, ROCKHOP_TRACKS[8]!.def, id => medals.get(id) ?? null),
      snowlineUnlocked: trackUnlocked(tracks, ROCKHOP_TRACKS[9]!.def, id => medals.get(id) ?? null) });
  }
  const firstAffordable = steps.find(s => s['proAffordable'] === true);
  const firstD3Open = steps.find(s => s['d3Unlocked'] === true);
  const purchase = new CareerEconomy(null);
  for (let i = 0; i < Number(firstAffordable?.['index'] ?? 0); i++) purchase.award(ROCKHOP_TRACKS[i]!.id, medalForCourse(ROCKHOP_TRACKS[i]!.id, i));
  const purchaseResult = firstAffordable ? purchase.purchasePro() : null;
  return { name, proPrice: PRO_PRICE, firstAffordableAfter: firstAffordable?.['after'] ?? null, firstD3OpenAfter: firstD3Open?.['after'] ?? null,
    walletWhenD3Opens: firstD3Open?.['wallet'] ?? null, walletAfterFirstEight: steps[7]?.['wallet'] ?? null,
    purchaseAtFirstAffordable: purchaseResult, walletAfterPurchase: purchase.snapshot().wallet, steps };
}

const bronzePath = unlockPath('bronze-only', () => 'bronze');
const rookieReferencePath = unlockPath('pinned-rookie-reference', id => byCourse.get(id)?.rookie?.medal ?? 'bronze');
const endFingerprint = srcFingerprint();
if (endFingerprint !== startFingerprint) throw new Error(`source changed during audit ${startFingerprint} -> ${endFingerprint}`);
const clean = rows.filter(r => r['status'] === 'clean');
const report = { schema: 1, sourceFingerprint: startFingerprint, gitHead: execFileSync('git', ['rev-parse', '--short', 'HEAD'], { cwd: root, encoding: 'utf8' }).trim(),
  method: 'Pinned skill-3 bot recordings replayed under current Node physics and medalFor; no new inputs or human runs',
  courseCount: ROCKHOP_TRACKS.length, referenceCount: rows.filter(r => r['reference'] !== null).length, cleanReferenceCount: clean.length,
  missing: rows.filter(r => r['status'] === 'missing-recording').map(r => `${r['code']} ${r['bike']}`),
  faulted: rows.filter(r => r['status'] === 'faulted-clear').map(r => `${r['code']} ${r['bike']}`),
  generousGoldClock: clean.filter(r => typeof r['ratioToGold'] === 'number' && (r['ratioToGold'] as number) <= 0.75).map(r => `${r['code']} ${r['bike']}`),
  diamondTimeButRouteBlocked: clean.filter(r => r['diamondClockPasses'] === true && r['diamondRouteCrossed'] === false).map(r => `${r['code']} ${r['bike']}`),
  rows, unlockPaths: [bronzePath, rookieReferencePath] };
fs.writeFileSync(path.join(outDir, 'audit.json'), JSON.stringify(report, null, 2) + '\n');
const columns = ['index', 'code', 'courseId', 'zone', 'bike', 'status', 'clean', 'goldS', 'silverS', 'diamondS', 'clearS', 'faults', 'medal', 'rewardScrap', 'ratioToGold', 'goldHeadroomS', 'diamondClockPasses', 'diamondHeadroomS', 'diamondRouteCrossed', 'reference', 'sourceStamp', 'hash'];
const csv = [columns.join(','), ...rows.map(row => columns.map(key => {
  const value = row[key] === null || row[key] === undefined ? '' : String(row[key]);
  return /[",\n]/.test(value) ? `"${value.replaceAll('"', '""')}"` : value;
}).join(','))].join('\n') + '\n';
fs.writeFileSync(path.join(outDir, 'audit.csv'), csv);
console.log(JSON.stringify({ sourceFingerprint: startFingerprint, references: report.referenceCount, clean: clean.length, missing: report.missing,
  faulted: report.faulted, generousGoldClock: report.generousGoldClock, diamondTimeButRouteBlocked: report.diamondTimeButRouteBlocked,
  unlock: report.unlockPaths.map(p => ({ name: p.name, firstAffordableAfter: p.firstAffordableAfter, firstD3OpenAfter: p.firstD3OpenAfter, walletWhenD3Opens: p.walletWhenD3Opens })) }));
