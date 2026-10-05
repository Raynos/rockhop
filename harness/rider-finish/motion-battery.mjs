/** Anatomical FK diagnostics. These trajectories are not gameplay or accepted animation. */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import crypto from 'node:crypto';
import { pathToFileURL } from 'node:url';
const smooth = t => t * t * (3 - 2 * t);
const rotation = (bone, axis, degrees) => ({ bone, axisNative: axis, degrees });
const arms = (left, right = left) => [rotation('upperArm.L', [0, 1, 0], left), rotation('upperArm.R', [0, 1, 0], right)];
const legs = (hip, knee) => ['L', 'R'].flatMap(s => [rotation(`thigh.${s}`, [0, 1, 0], hip), rotation(`shin.${s}`, [0, 1, 0], knee)]);
const pose = (rotations = [], rootTranslationNativeM = [0, 0, 0], armDirections = null) => ({ rotations, rootTranslationNativeM, armDirections });
export const staticCases = [
  { name: 'true-rest-action-off', target: pose(), meaning: 'Original bind/rest; all basis transforms identity, all actions and constraints disabled.' },
  { name: 'neutral', target: pose([], [0, 0, 0], { L: [0, 0, -1], R: [0, 0, -1] }), meaning: 'Both upper/lower arms directed down in armature-native coordinates; bind rest is separately retained.' },
  { name: 'A', target: pose([], [0, 0, 0], { L: [0, -Math.SQRT1_2, -Math.SQRT1_2], R: [0, Math.SQRT1_2, -Math.SQRT1_2] }), meaning: 'Straight upper/lower arms 45 degrees below horizontal.' },
  { name: 'T', target: pose([], [0, 0, 0], { L: [0, -1, 0], R: [0, 1, 0] }), meaning: 'Straight upper/lower arms horizontal.' },
  { name: 'reach', target: pose([], [0, 0, 0], { L: [1, 0, 0], R: [1, 0, 0] }), meaning: 'Straight forward upper/lower arm targets.' },
  { name: 'raised', target: pose([], [0, 0, 0], { L: [0, 0, 1], R: [0, 0, 1] }), meaning: 'Straight overhead upper/lower arm targets.' },
  { name: 'asymmetric', target: pose([rotation('forearm.R', [0, 1, 0], -55)], [0, 0, 0], { L: [0, 0, 1], R: [1, 0, 0] }), meaning: 'Left overhead; right forward plus 55 degree forearm delta.' },
  { name: 'crouch', target: pose([...legs(-45, 85), rotation('chest', [0, 1, 0], 15)], [0, 0, -.15]), meaning: 'FK hip/knee diagnostic, not floor-support IK.' },
  { name: 'turn', target: pose([rotation('pelvis', [0, 0, 1], 35), rotation('chest', [0, 0, 1], 15), rotation('head', [0, 0, 1], 20)]), meaning: 'Pelvis35/chest15/head20 rest-frame yaw deltas; no locomotion contact claim.' },
  { name: 'jump', target: pose([...legs(-20, 35), ...arms(-30)], [0, 0, .20]), meaning: 'Raised root FK silhouette test; no ballistic trajectory claim.' },
  { name: 'landing', target: pose([...legs(-50, 90), ...arms(-20), rotation('chest', [0, 1, 0], 20)], [0, 0, -.18]), meaning: 'Compression FK stress; no ground-contact qualification.' },
];
function scalePose(p, weight) {
  return { rotations: p.rotations.map(r => ({ ...r, degrees: r.degrees * weight })), rootTranslationNativeM: p.rootTranslationNativeM.map(x => x * weight), armDirections: p.armDirections, armDirectionBlend: weight };
}
export function buildBattery({ hz = 12, transitionS = 1, holdS = .25, cycles = 2 } = {}) {
  assert(Number.isInteger(hz) && hz >= 2 && hz <= 120);
  assert(transitionS > 0 && holdS >= 0 && Number.isInteger(cycles) && cycles > 0);
  assert(Math.round(hz * transitionS) >= 1, 'Transition duration must contain at least one sample interval');
  const frames = [], cases = [];
  const add = (name, phase, command) => frames.push({ index: frames.length, timeS: frames.length / hz, case: name, phase, command });
  for (const fixture of staticCases) {
    const start = frames.length, forward = [];
    const count = Math.round(hz * transitionS);
    for (let i = 0; i <= count; i++) { const command = scalePose(fixture.target, smooth(i / count)); forward.push(command); add(fixture.name, 'forward', command); }
    for (let i = 0; i < Math.round(hz * holdS); i++) add(fixture.name, 'hold', forward.at(-1));
    for (const command of forward.slice().reverse()) add(fixture.name, 'reverse', command);
    cases.push({ name: fixture.name, start, end: frames.length - 1, meaning: fixture.meaning, target: fixture.target });
  }
  for (const { name, swing, knee, chest, rootBob } of [{ name: 'walk', swing: 25, knee: 35, chest: 3, rootBob: .015 }, { name: 'jog', swing: 40, knee: 65, chest: 8, rootBob: .04 }, { name: 'idle', swing: 0, knee: 0, chest: 1.5, rootBob: .003 }]) {
    const start = frames.length, sequence = [];
    for (let i = 0; i <= cycles * hz; i++) {
      const phase = i / hz * Math.PI * 2, envelope = Math.sin(Math.PI * i / (cycles * hz)) ** 2;
      const command = pose([
        ...['L', 'R'].flatMap((side, j) => { const s = Math.sin(phase + j * Math.PI) * envelope; return [rotation(`thigh.${side}`, [0, 1, 0], swing * s), rotation(`shin.${side}`, [0, 1, 0], knee * Math.max(0, -s)), rotation(`upperArm.${side}`, [0, 1, 0], -swing * .6 * s)]; }),
        rotation('chest', [0, 1, 0], chest * Math.sin(phase) * envelope),
      ], [0, 0, rootBob * Math.sin(phase * 2) * envelope]);
      sequence.push(command); add(name, 'forward', command);
    }
    for (const command of sequence.slice().reverse()) add(name, 'reverse', command);
    cases.push({ name, start, end: frames.length - 1, meaning: 'Bounded FK cycle diagnostic, stationary root; no gait, ground support or natural-animation acceptance.', rangesDegrees: { hip: [-swing, swing], knee: [0, knee], arm: [-swing * .6, swing * .6], chest: [-chest, chest] }, rootBobM: rootBob });
  }
  return { schema: 'rockhop-semantic-motion-v1', status: 'UNACCEPTED_FK_DIAGNOSTIC', axes: 'Native armature +Xforward/+Zup/-Yleft. Rotation axes are expressed in the immutable REST armature frame and conjugated into each bone basis.', sampling: { hz, transitionS, holdS, cycles }, cases, frames,
    separateRequiredFixtures: ['Native bike forward/back driver', 'actual47 recorded physics driver', 'presentation50 separately labeled'],
    limits: ['Synthetic gait/jump/landing trajectories test geometry and skin, not physical support or animation acceptance.', 'No changes to rest bones, hierarchy, binds, source geometry or production assets.', 'Finite samples do not prove continuous contact or parity.'] };
}
if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const output = process.argv[2]; assert(output && !fs.existsSync(output), 'Usage: node motion-battery.mjs NEW.json');
  const bytes = JSON.stringify(buildBattery(), null, 2) + '\n'; fs.writeFileSync(output, bytes);
  process.stdout.write(JSON.stringify({ output, frames: buildBattery().frames.length, sha256: crypto.createHash('sha256').update(bytes).digest('hex') }) + '\n');
}
