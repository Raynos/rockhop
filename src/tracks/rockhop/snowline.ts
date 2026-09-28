/**
 * SNOWLINE — glacier and ski-lift country (B-ride-snow, D20): ice ledges and shelves, lift towers, avalanche
 * fences, snow-cats, timber bridges, crevasses, cornices. Hard -> extreme. The last zone asks for everything the
 * rider has learned, higher and closer together: cap rows on the lift towers, momentum faces on the ice, the
 * cornice roll-off, spinning snow-cat rollers and crevasse slots.
 *
 * Authoring numbers: `FEEL` / docs/design/tracks.md §0 (physics v2). Faces 45 deg over the 0.3 m kicker foot from a
 * 30 m run-in onto a >= 12 m top; cap rows entered from a shelf 0.3-0.4 m under the caps; spinning tops from a
 * shelf, three at most; roll-offs <= 40 deg onto a >= 8 x h descent; platform lips straight 2 x 0.4.
 */
import { rockhop } from './builder';

/** Crevasse slots: 0.7 m kill pits at `pitch`, crossed on the rear wheel. */
function slots(b: ReturnType<typeof rockhop>, count: number, pitch: number): ReturnType<typeof rockhop> {
  for (let i = 0; i < count; i++) b.gap({ width: 0.7, depth: 1.5, hazard: 'kill' }).flat(pitch - 0.7);
  return b;
}

/**
 * S1 LIFT LINE — up the lift line to the top station. TEACHES the tower caps (a rolling hop from the ice shelf onto
 * the first sheave platform, hold the line cap to cap) and the ice-shelf gap chain. DEMANDS the lift line: three
 * tower caps climbing 1.3 -> 1.6 over the crevasse and the jump off the top station.
 */
export const S1 = (() => {
  const base = rockhop('S1', 's1-lift-line', 'Lift Line', 'snowline', 'hard', {
    technique: 'tower caps, ice-shelf gaps and a controlled station landing',
    demands: 'settle at the station lip, then climb three tower caps over the crevasse',
    idea: 'ride the ski-lift towers',
    hero: 'The Lift Line',
    attemptsBand: [5, 10],
    targetTimeS: 40.25, // Pro upper reference 30.333 s; Diamond 30.791 s also requires station-shelf proof
  })
  .hint('Carry speed across the ice shelves')
  .hint('Ease off at the station lip; land level')
  .hint('Use rear-wheel grip on the tower caps')
  .hint('Level the station jump to catch the high snow shelf')
  .camera({ mode: 'side' })
  .setPiece('start', 'The Base Station')
  .flat(6)
  .arch({ style: 'start' })
  .flat(18)
  .endSetPiece()
  .checkpoint()
  .flat(16)
  .camera({ mode: 'high34' })
  .ramp({ length: 5, height: 1.0, surface: 'snow', prop: 'ice-ledge' })
  .gap({ width: 3 })
  .platform(12, 1.0, { landing: 0.4, landingLength: 3, length: 2, curve: 0 }) // ice shelf 1
  .gap({ width: 3 })
  .platform(12, 1.2, { landing: 0.4, landingLength: 3, length: 2, curve: 0 }) // ice shelf 2
  .gap({ width: 2.5 })
  .gapLanding(1.2, 5, 6, 10)
  .camera({ mode: 'side' })
  .flat(12)
  .bumpRow(2, 0.3, 16)
  .flat(8)
  .checkpoint()
  .flat(12)
  .camera({ mode: 'low' })
  .setPiece('balance', 'The First Towers')
  .ramp({ length: 5, height: 1.0, surface: 'snow', prop: 'ice-ledge' })
  .box({ width: 4, height: 1.0, surface: 'snow', prop: 'ice-ledge' }) // the loading shelf
  .poleRow([1.3, 1.3, 1.3], 1.2, { radius: 0.3 }) // three tower caps level, 0.3 m above the shelf
  .space(0.6)
  .box({ width: 5, height: 1.3, surface: 'snow', prop: 'ice-ledge' })
  .ramp({ length: 10, height: 1.3, direction: 'down', surface: 'snow', prop: 'ice-ledge' })
  .endSetPiece()
  .flat(12)
  .camera({ mode: 'side' })
  .wave(30, 1.2, 16)
  .flat(8)
  .checkpoint()
  .flat(30) // 28 m is the GO failure threshold; 2 m of margin keeps the repeatable overspeed landing legible
  .camera({ mode: 'side-tight', zoomBias: -0.4 })
  .kickerPlank({ angleDeg: 22, rise: 2.2 }) // the station lip: full throttle pitches the bike high over the deck
  .box({ width: 12, height: 2.2, surface: 'snow', prop: 'ice-ledge' })
  .ramp({ length: 28, height: 2.2, direction: 'down', surface: 'snow', prop: 'ice-ledge' })
  .camera({ mode: 'side' })
  .flat(10)
  .rollers(20, 0.25, 3)
  .flat(8)
  .checkpoint()
  .flat(12)
  .camera({ mode: 'low', cut: true })
  .setPiece('balance', 'The Lift Line')
  .ramp({ length: 5, height: 1.0, surface: 'snow', prop: 'ice-ledge' })
  .box({ width: 4, height: 1.0, surface: 'snow', prop: 'ice-ledge' })
  .poleRow([1.3, 1.45, 1.6], 1.2, { radius: 0.3 }) // the towers climb the line
  .space(0.6)
  .box({ width: 6, height: 1.6, surface: 'snow', prop: 'lift-tower' }) // the top station deck
  .ramp({ length: 2, height: 0.4, surface: 'wood', prop: 'lift-tower' }, { base: 1.6 }) // off the station lip
  .ramp({ length: 16, height: 1.5, direction: 'down', surface: 'snow', prop: 'ice-ledge' }) // a 0.5 m drop onto the piste
  .endSetPiece()
  .camera({ mode: 'side' })
  .flat(12)
  .wave(30, 1.2, 16)
  .flat(4)
  .arch({ style: 'crowd' })
  .setPiece('finish')
  .flat(10)
  .arch({ style: 'finish' })
  .finish();
  // The upper station shelf begins beyond the mandatory deck. Its one-way surface leaves the descending piste
  // open below, while a level Pro station jump can put the rear wheel on the high line.
  const deckIndex = base.obstacles.length;
  base.obstacles.push({ kind: 'open-platform', pos: { x: 288, y: 0 },
    params: { length: 10, height: 4.6, thickness: 0.18, surface: 'snow' } });
  base.diamondGoal = { id: 's1-station-shelf', platformObstacleIndex: deckIndex, x: 293.5, minRearY: 4.8 };
  return base;
})();

/**
 * S2 CORNICE — over the ridge and off the wind lip. TEACHES momentum faces on the ice (45 deg over the kicker foot),
 * the snow-cat's spinning rollers and the fence hop. DEMANDS the cornice: up the ice wall onto the ridge, along the
 * cornice and off its wind lip onto the avalanche slope — then the fences and the shelf chain home.
 */
export const S2 = (() => {
  const base = rockhop('S2', 's2-cornice', 'Cornice', 'snowline', 'extreme', {
    technique: 'ice face, rollers, fence hop',
    demands: 'wind shelf for Diamond',
    idea: 'cornice jump',
    hero: 'The Cornice',
    attemptsBand: [6, 12],
    targetTimeS: 44.5, // Pro upper line: 33.792 s < 44.5 * 0.9 * 0.85 = 34.043 s; lower line remains Gold
  })
  .camera({ mode: 'side' })
  .setPiece('start', 'The Hut')
  .flat(6)
  .arch({ style: 'start' })
  .flat(18)
  .endSetPiece()
  .checkpoint()
  .flat(16)
  .camera({ mode: 'side-tight', zoomBias: -0.5 })
  .setPiece('balance', 'The Snow-Cat')
  .drumStep({ radius: 0.8, rolls: true, prop: 'snowcat' }) // the snow-cat's front roller from its blade
  .gap({ width: 1.5 })
  .drum({ radius: 0.8, rolls: true, prop: 'snowcat' }) // the middle roller
  .gap({ width: 1.5 })
  .drum({ radius: 0.8, rolls: true, prop: 'snowcat' }) // the rear roller
  .box({ width: 2, height: 1.2, surface: 'metal', prop: 'snowcat' })
  .ramp({ length: 8, height: 1.2, direction: 'down', surface: 'snow', prop: 'ice-ledge' })
  .endSetPiece()
  .camera({ mode: 'side' })
  .flat(12)
  .bumpRow(2, 0.3, 16)
  .flat(8)
  .checkpoint()
  .flat(3)
  .flat(27) // 30 m run-in to the ice wall
  .camera({ mode: 'side-tight', pitch: (12 * Math.PI) / 180 })
  .setPiece('climb', 'The Cornice')
  .kickerPlank({ angleDeg: 45, rise: 3.4 }) // the ice wall
  .box({ width: 16, height: 3.4, surface: 'snow', prop: 'cornice' }) // along the cornice: 16 m to set the speed for the lip
  .ramp({ length: 2, height: 0.4, surface: 'snow', prop: 'cornice' }, { base: 3.4 }) // the wind lip: 11 deg
  .gap({ width: 5.5 }) // over the crevasse below the cornice
  .ramp({ length: 8, height: 2.2, surface: 'snow', prop: 'ice-ledge' }) // land on the ice shelf's slope: a 1.6 m drop from the lip
  .box({ width: 6, height: 2.2, surface: 'snow', prop: 'ice-ledge' })
  .ramp({ length: 20, height: 2.2, direction: 'down', surface: 'snow', prop: 'ice-ledge' }) // down the avalanche slope
  .endSetPiece()
  .camera({ mode: 'side' })
  .flat(12)
  .rollers(20, 0.25, 3)
  .flat(8)
  .checkpoint()
  .flat(8)
  .camera({ mode: 'side-tight' })
  .ledge({ height: 0.4, length: 6, surface: 'wood', prop: 'fence' }) // the fence line: hop on
  .gap({ width: 1.2, depth: 2 })
  .ramp({ length: 2, height: 0.2, surface: 'wood', prop: 'fence' }, { base: 0.2 })
  .box({ width: 6, height: 0.4, surface: 'wood', prop: 'fence' })
  .ramp({ length: 5, height: 0.4, direction: 'down', surface: 'snow', prop: 'ice-ledge' })
  .flat(14)
  .camera({ mode: 'side-tight' })
  .steppedWall({ height: 1.0, width: 8, lip: 0.15, surface: 'snow', prop: 'ice-ledge' }, 0.3) // onto the bergschrund shelf
  .flat(3)
  .gap({ width: 0.7, depth: 1.5, hazard: 'kill' }) // the bergschrund: six crevasse slots on the rear wheel
  .flat(1.5)
  .gap({ width: 0.7, depth: 1.5, hazard: 'kill' })
  .flat(1.5)
  .gap({ width: 0.7, depth: 1.5, hazard: 'kill' })
  .flat(1.5)
  .gap({ width: 0.7, depth: 1.5, hazard: 'kill' })
  .flat(1.5)
  .gap({ width: 0.7, depth: 1.5, hazard: 'kill' })
  .flat(1.5)
  .gap({ width: 0.7, depth: 1.5, hazard: 'kill' })
  .flat(12)
  .camera({ mode: 'side' })
  .wave(30, 1.2, 16)
  .flat(8)
  .checkpoint()
  .flat(12)
  .camera({ mode: 'low' })
  .ramp({ length: 5, height: 1.0, surface: 'snow', prop: 'ice-ledge' })
  .box({ width: 4, height: 1.0, surface: 'snow', prop: 'ice-ledge' }) // the marker shelf
  .poleRow([1.35, 1.35, 1.35], 1.1, { radius: 0.3 }) // the old lift's tower stumps over the last crevasse
  .space(0.6)
  .box({ width: 5, height: 1.35, surface: 'snow', prop: 'ice-ledge' })
  .ramp({ length: 11, height: 1.35, direction: 'down', surface: 'snow', prop: 'ice-ledge' })
  .camera({ mode: 'side' })
  .flat(12)
  .wave(30, 1.2, 16)
  .flat(6)
  .arch({ style: 'crowd' })
  .setPiece('finish')
  .flat(10)
  .arch({ style: 'finish' })
  .finish();
  // The Pro's stronger launch from the ice wall can land on this one-way wind shelf. The Rookie's measured
  // lower trajectory passes underneath; both bikes can still clear the main ice-shelf line below it.
  // Explicit x prevents the optional shelf from moving the course cursor or changing checkpoint spacing.
  const deckIndex = base.obstacles.length;
  base.obstacles.push({ kind: 'open-platform', pos: { x: 157, y: 0 },
    params: { length: 13, height: 8.5, thickness: 0.18, surface: 'snow' } });
  base.diamondGoal = { id: 's2-wind-shelf', platformObstacleIndex: deckIndex, x: 165, minRearY: 8.7 };
  return base;
})();

/**
 * S3 WHITEOUT — the summit run in the storm. DEMANDS everything the snowline taught, closer together: the crevasse
 * slots on the rear wheel, the spinning rollers, the fence hop, and the summit: a rising shelf chain up to the top
 * towers and a cap row at the top, then the long run down in the whiteout.
 *
 * Riding-poses physics (a736a26f): with the caps 0.4 m over the shelf one average reflex seed of 45 hit the
 * 50-attempt cap at the towers. The caps are now 0.35 m over it (2.55 m): every seed clears, mean 9.56.
 */
export const S3 = (() => {
  const b = rockhop('S3', 's3-whiteout', 'Whiteout', 'snowline', 'extreme', {
    technique: 'everything, closer together',
    demands: 'the summit: a climbing ice-shelf chain to 2.2 m, four summit tower caps at 2.55 m over the crevasse, off the station and down',
    idea: 'stormy summit tower climb',
    hero: 'The Summit Towers',
    attemptsBand: [8, 16],
    targetTimeS: 39.5, // Pro upper reference 29.600 s; Diamond 30.218 s also requires summit-shelf proof
  })
    .hint('Ride high over the snow-cat to catch the wind shelf')
    .camera({ mode: 'side' })
    .setPiece('start', 'The Top Station')
    .flat(6)
    .arch({ style: 'start' })
    .flat(18)
    .endSetPiece()
    .checkpoint()
    .flat(16)
    .camera({ mode: 'side-tight' })
    .steppedWall({ height: 1.0, width: 8, lip: 0.15, surface: 'snow', prop: 'ice-ledge' }, 0.3) // onto the ice shelf
    .flat(3);
  slots(b, 6, 2.3); // the crevasse field
  b.flat(8)
    .camera({ mode: 'side' })
    .bumpRow(2, 0.3, 16)
    .flat(8)
    .checkpoint()
    .flat(16)
    .camera({ mode: 'side-tight', zoomBias: -0.5 })
    .drumStep({ radius: 0.9, rolls: true, prop: 'snowcat' }) // the stranded snow-cat's rollers
    .gap({ width: 1.5 })
    .drum({ radius: 0.9, rolls: true, prop: 'snowcat' })
    .gap({ width: 1.5 })
    .drum({ radius: 0.9, rolls: true, prop: 'snowcat' })
    .box({ width: 2, height: 1.3, surface: 'metal', prop: 'snowcat' })
    .ramp({ length: 10, height: 1.3, direction: 'down', surface: 'snow', prop: 'ice-ledge' })
    .flat(12)
    .camera({ mode: 'side' })
    .rollers(20, 0.25, 3)
    .flat(8)
    .checkpoint()
    .flat(8)
    .camera({ mode: 'side-tight' })
    .ledge({ height: 0.4, length: 6, surface: 'wood', prop: 'fence' }) // the buried fence: hop on, hop across
    .gap({ width: 1.2, depth: 2 })
    .ramp({ length: 2, height: 0.2, surface: 'wood', prop: 'fence' }, { base: 0.2 })
    .box({ width: 6, height: 0.4, surface: 'wood', prop: 'fence' })
    .ramp({ length: 5, height: 0.4, direction: 'down', surface: 'snow', prop: 'ice-ledge' })
    .flat(12)
    .camera({ mode: 'side' })
    .wave(30, 1.2, 16)
    .flat(8)
    .checkpoint()
    .flat(16)
    .camera({ mode: 'high34' })
    .setPiece('climb', 'The Summit Towers')
    .ramp({ length: 5, height: 1.0, surface: 'snow', prop: 'ice-ledge' })
    .gap({ width: 3 })
    .platform(10, 1.4, { landing: 0.4, landingLength: 3, length: 2, curve: 0 }) // the shelves step up the summit
    .gap({ width: 3 })
    .platform(10, 1.8, { landing: 0.4, landingLength: 3, length: 2, curve: 0 })
    .gap({ width: 2.5 })
    .ramp({ length: 3, height: 0.4, surface: 'snow', prop: 'ice-ledge' }, { base: 1.8 }) // landing lip onto the top shelf
    .box({ width: 10, height: 2.2, surface: 'snow', prop: 'ice-ledge' }) // the top shelf: settle
    .camera({ mode: 'low' })
    .poleRow([2.55, 2.55, 2.55, 2.55], 1.2, { radius: 0.3 }) // the summit towers, 0.35 m above the shelf
    .space(0.5)
    .box({ width: 5, height: 2.6, surface: 'snow', prop: 'lift-tower' })
    .ramp({ length: 22, height: 2.6, direction: 'down', surface: 'snow', prop: 'ice-ledge' })
    .endSetPiece()
    .camera({ mode: 'high34', cut: true })
    .flat(10)
    .setPiece('drop', 'The Whiteout')
    .rollers(30, 0.3, 4)
    .endSetPiece()
    .camera({ mode: 'side' })
    .flat(8)
    .arch({ style: 'crowd' })
    .setPiece('finish')
    .flat(10)
    .arch({ style: 'finish' });
  const base = b.finish();
  // The one-way wind shelf sits above the snow-cat exit. The ordinary landing keeps its full lower passage.
  const deckIndex = base.obstacles.length;
  base.obstacles.push({ kind: 'open-platform', pos: { x: 144, y: 0 },
    params: { length: 8, height: 3.1, thickness: 0.18, surface: 'snow' } });
  base.diamondGoal = { id: 's3-snowcat-shelf', platformObstacleIndex: deckIndex, x: 148.4, minRearY: 3.3 };
  return base;
})();

export const SNOWLINE_TRACKS = [S1, S2, S3] as const;
