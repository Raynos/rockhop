/**
 * ALPINE — the alpine forest trail (B-ride, D20): logs, log stacks, the sawmill and its flume, logging trucks,
 * timber ramps and decks, rocks, a lake below the peaks. Easy -> medium. The zone teaches the rider's own moves:
 * stairs at speed, the hop, logs and the balance board.
 *
 * Authoring numbers: `FEEL` / docs/design/tracks.md §0 (physics v2). Stairs are 0.12 m risers at a 0.8 m run up
 * and 0.15 x 0.6 down, no flight taller than 1.2 m; hop ledges 0.4-0.45 m 6-8 m past their spawn (the hop window
 * is 5-8 m/s); log pyramids two rows behind an entry ramp to the first log's top; boards <= 22 deg with 14 m of
 * flat after them before anything that needs speed.
 */
import { rockhop } from './builder';

/**
 * A1 SAWDUST — through the sawmill yard. TEACHES stairs at speed (gas up the timber steps, no brakes on the way
 * down) and the rear-wheel-first landing over the mill race. DEMANDS the flume: up the ramp onto the flume trough,
 * 16 m along it, off its lip over the mill pond onto the landing deck.
 */
export const A1 = rockhop('A1', 'a1-sawdust', 'Sawdust', 'alpine', 'easy', {
  technique: 'stairs at speed, then release and pitch forward over the flume landing',
  demands: 'climb the 24 deg flume, cross the pond and land level on the deck',
  idea: 'sawmill flume jump',
  hero: 'The Flume',
  attemptsBand: [1, 3],
  targetTimeS: 50, // provisional: new clean Rookie bot 30.35 s; phone medal calibration remains
})
  .hint('Gas up the stairs')
  .hint('Release GO; lean forward at the flume')
  .camera({ mode: 'side' })
  .setPiece('start', 'The Mill Gate')
  .flat(6)
  .arch({ style: 'start' })
  .flat(18)
  .endSetPiece()
  .bumpDrum(0.4, 0.2, { surface: 'wood', prop: 'log' }) // bark slabs in the track
  .flat(8)
  .bumpDrum(0.4, 0.2, { surface: 'wood', prop: 'log', variant: 1 })
  .flat(12)
  .checkpoint()
  .flat(16)
  .camera({ mode: 'side-tight', zoomBias: -0.5 })
  .setPiece('climb', 'The Loading Dock')
  .stair({ count: 8, height: 0.12, length: 0.8, surface: 'wood', prop: 'timber-deck' }) // 0.96 m at 8.5 deg
  .box({ width: 8, height: 0.96, surface: 'wood', prop: 'timber-deck' })
  .ramp({ length: 10, height: 0.96, direction: 'down', surface: 'wood', prop: 'timber-deck' })
  .endSetPiece()
  .camera({ mode: 'side' })
  .flat(10)
  .rollers(24, 0.25, 3)
  .flat(16)
  .camera({ mode: 'high34' })
  .ramp({ length: 5, height: 1.2, surface: 'wood', prop: 'timber-deck' }) // over the mill race
  .gap({ width: 5 })
  .gapLanding(1.0, 6, 8, 10)
  .camera({ mode: 'side' })
  .flat(12)
  .bumpDrum(0.5, 0.25, { surface: 'wood', prop: 'log' })
  .flat(10)
  .checkpoint()
  .flat(16)
  .camera({ mode: 'side-tight', zoomBias: -0.5 })
  .setPiece('climb', 'The Saw Shed')
  .stair({ count: 10, height: 0.12, length: 0.8, surface: 'wood', prop: 'timber-deck' }) // 1.2 m at speed
  .box({ width: 6, height: 1.2, surface: 'wood', prop: 'timber-deck' })
  .stair({ count: 8, height: 0.15, length: 0.6, direction: 'down', surface: 'wood', prop: 'timber-deck' }) // brake, release before the lip
  .endSetPiece()
  .camera({ mode: 'side' })
  .flat(12)
  .wave(30, 1.2, 16)
  .flat(8)
  .checkpoint()
  .flat(18) // full read and restart run-up from Marker 3 to the flume
  .camera({ mode: 'side-tight', zoomBias: -0.4 })
  .setPiece('air', 'The Flume')
  .kickerPlank({ angleDeg: 24, rise: 2.0 }) // short foot gives the flume a readable, committed entry
  .box({ width: 16, height: 2.0, surface: 'wood', prop: 'flume' }) // the flume: 16 m of run along the trough
  .ramp({ length: 2, height: 0.4, surface: 'wood', prop: 'flume' }, { base: 2.0 }) // pond lip: level the bike in flight
  .gap({ width: 6 })
  .gapLanding(1.2, 8, 8, 12) // the landing deck over the pond
  .endSetPiece()
  .camera({ mode: 'side' })
  .flat(12)
  .rollers(20, 0.25, 3)
  .flat(4)
  .arch({ style: 'crowd' })
  .setPiece('finish')
  .flat(10)
  .arch({ style: 'finish' })
  .finish();

/**
 * A2 LOG JAM — the river bend where the log drive jammed. TEACHES logs: roll the piles from their ramp, lean back
 * over the loose ones, roll the big log's top from its cribbing, and ride the teetering log (a see-saw: slow on,
 * past the pivot, let it tip). DEMANDS the jam: a jump onto the teetering log, straight into a five-log pile.
 */
export const A2 = rockhop('A2', 'a2-log-jam', 'Log Jam', 'alpine', 'medium', {
  technique: 'preload and level over the first log stack, then meter speed across the teetering log',
  demands: 'the jam: a 3.5 m jump onto a 22 deg teetering log, then a five-log two-row pile',
  idea: 'ride the teetering log jam',
  hero: 'The Jam',
  attemptsBand: [2, 4],
  targetTimeS: 50, // gold: skill-3 bot 29.98 s x 1.6 = 48.0, rounded up to 5 s, non-decreasing through the tier (OBSIDIAN = 0.85 x gold, 0 bails)
})
  .hint('Lean back before the log stack; level on top')
  .hint('Level the landing after the pile')
  .hint('Slow for the teetering log; gas out as it tips')
  .camera({ mode: 'side' })
  .setPiece('start', 'The Landing')
  .flat(6)
  .arch({ style: 'start' })
  .flat(18)
  .endSetPiece()
  .checkpoint()
  .flat(16)
  .camera({ mode: 'side-tight', zoomBias: -0.5 })
  .ramp({ length: 4, height: 0.6, surface: 'wood', prop: 'timber-deck' }) // a straight skid ramp to the log tops (8.5 deg: a concave lip launches at 12 m/s)
  .logpile({ radius: 0.3, count: 5, rows: 2, surface: 'wood', prop: 'log' }) // five logs, four on top: roll across
  .flat(12)
  .rollers(20, 0.2, 3)
  .flat(8)
  .camera({ mode: 'side' })
  .rollers(20, 0.25, 3)
  .flat(8)
  .checkpoint()
  .flat(3)
  .camera({ mode: 'low' })
  .seesawEntry({ length: 8, height: 1.2, surface: 'wood', prop: 'log' }) // the first teetering log: 17 deg, taken slow
  .flat(14)
  .camera({ mode: 'side' })
  .wave(30, 1.2, 16)
  .flat(26)
  .camera({ mode: 'side-tight', zoomBias: -0.5 })
  .drumStep({ radius: 0.6, surface: 'wood', prop: 'log' }, { exit: true }) // a big log on its cribbing: roll the top
  .flat(10)
  .camera({ mode: 'low' })
  .seesawEntry({ length: 8, height: 1.5, surface: 'wood', prop: 'log', variant: 1 }) // the long teetering log: 21 deg
  .flat(14)
  .camera({ mode: 'side' })
  .bumpRow(2, 0.3, 16)
  .flat(8)
  .checkpoint()
  .flat(16)
  .camera({ mode: 'low', cut: true })
  .setPiece('balance', 'The Jam')
  .ramp({ length: 4, height: 1.0, surface: 'wood', prop: 'log-stack' })
  .gap({ width: 3.5 })
  .seesaw({ length: 8, height: 1.6, surface: 'wood', prop: 'log' }) // land on the log: it dips, roll up, it tips
  .flat(14)
  .ramp({ length: 4, height: 0.6, surface: 'wood', prop: 'timber-deck' })
  .logpile({ radius: 0.3, count: 5, rows: 2, surface: 'wood', prop: 'log' }) // the jam: five logs long, two rows
  .ramp({ length: 9, height: 0.9, direction: 'down', surface: 'wood', prop: 'timber-deck' }) // a skid ramp off the pile top
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

/**
 * A3 TIMBERLINE — the logging road up to the last trees. TEACHES the hop (preload back with a little gas, snap
 * forward) onto cribbing and stumps, and the thin landing on a skid beam. DEMANDS the log loader: a kicker onto the
 * logging truck's bed, a hop onto its log load and across to the landing.
 *
 * The former 0.38 m truck load could be passed after automatic respawns under neutral full GO. A 0.5 m load now
 * requires a deliberate front-wheel lift, with the exit landing raised to match its top. Touch difficulty is unmeasured.
 */
export const A3 = rockhop('A3', 'a3-timberline', 'Timberline', 'alpine', 'medium', {
  technique: 'lift the front for the truck load, then settle on the thin landing',
  demands: 'hop onto the truck, lift over its 0.5 m log load, then clear the exit',
  idea: 'hop the logging truck load',
  hero: 'The Log Loader',
  attemptsBand: [2, 5],
  targetTimeS: 50, // provisional: new clean Rookie bot 24.817 s; preserve campaign clock ladder pending phone play
})
  .hint('Lean back to lift onto the log load')
  .hint('Level the bike over the exit gap')
  .camera({ mode: 'side' })
  .setPiece('start', 'The Logging Road')
  .flat(6)
  .arch({ style: 'start' })
  .flat(18)
  .endSetPiece()
  .checkpoint()
  .flat(7)
  .camera({ mode: 'side-tight' })
  .ledge({ height: 0.4, length: 7, surface: 'wood', prop: 'log-stack' }) // hop 1: onto the cribbing
  .ramp({ length: 5, height: 0.4, direction: 'down', surface: 'wood', prop: 'timber-deck' })
  .flat(12)
  .camera({ mode: 'side' })
  .rollers(20, 0.25, 3)
  .flat(10)
  .checkpoint()
  .flat(16)
  .camera({ mode: 'low' })
  .ramp({ length: 5, height: 1.0, surface: 'wood', prop: 'timber-deck' }) // kicker onto the skid beam
  .gap({ width: 3 })
  .ramp({ length: 2, height: 0.25, surface: 'wood', prop: 'timber-deck' }, { base: 0.75 }) // landing lip
  .plank({ length: 6, height: 1.0, surface: 'wood', prop: 'timber-deck' }) // the beam: a 6 m thin landing at 1.0
  .ramp({ length: 5, height: 1.0, direction: 'down', surface: 'wood', prop: 'timber-deck' })
  .flat(14)
  .camera({ mode: 'side' })
  .wave(30, 1.2, 16)
  .flat(8)
  .checkpoint()
  .flat(7)
  .camera({ mode: 'side-tight' })
  .ledge({ height: 0.4, length: 6, surface: 'wood', prop: 'stump' }) // stump row: hop on
  .gap({ width: 1.2, depth: 2 }) // hop across the stump gap
  .ramp({ length: 2, height: 0.2, surface: 'wood', prop: 'timber-deck' }, { base: 0.2 }) // landing lip
  .box({ width: 6, height: 0.4, surface: 'wood', prop: 'log-stack' })
  .ramp({ length: 5, height: 0.4, direction: 'down', surface: 'wood', prop: 'timber-deck' })
  .flat(14)
  .camera({ mode: 'side' })
  .bumpDrum(0.5, 0.25, { surface: 'wood', prop: 'log' })
  .flat(10)
  .checkpoint()
  .flat(16)
  .camera({ mode: 'low', cut: true })
  .setPiece('air', 'The Log Loader')
  .ramp({ length: 6, height: 1.2, surface: 'wood', prop: 'timber-deck' }) // kicker onto the truck
  .gap({ width: 3 })
  .ramp({ length: 2, height: 0.25, surface: 'metal', prop: 'truck-bed' }, { base: 0.95 })
  .box({ width: 8, height: 1.2, prop: 'truck-bed' }) // the logging truck bed
  .ledge({ height: 0.5, length: 6, surface: 'wood', prop: 'log-stack' }, { base: 1.2 }) // full GO noses into the load; lean back to lift
  .gap({ width: 1.5, depth: 2 }) // and across to the landing
  .ramp({ length: 3, height: 0.32, surface: 'wood', prop: 'timber-deck' }, { base: 1.38 }) // landing lip to 1.7 m deck
  .box({ width: 6, height: 1.7, surface: 'wood', prop: 'timber-deck' })
  .ramp({ length: 14, height: 1.7, direction: 'down', surface: 'wood', prop: 'timber-deck' })
  .endSetPiece()
  .camera({ mode: 'side' })
  .flat(12)
  .rollers(24, 0.25, 3)
  .flat(6)
  .arch({ style: 'crowd' })
  .setPiece('finish')
  .flat(10)
  .arch({ style: 'finish' })
  .finish();

export const ALPINE_TRACKS = [A1, A2, A3] as const;
