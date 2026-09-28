/** C1 lessons are tied to authored metres, not to a physics crash sensor (which can fire after the obstacle). */
export interface FaultCue {
  title: string;
  action: string;
  accessible: string;
}

export function c1FaultCue(x: number, checkpoint: number, pitchRad = 0): FaultCue | null {
  // Marker 2 is x=179.6; the 22° pallet starts at x=209.6 and the deck ends just before the gangway.
  if (checkpoint === 1 && x >= 209 && x < 265) {
    return {
      title: 'DECK LANDING',
      action: 'BRAKE BEFORE RAMP · RELEASE GO AT LIP',
      accessible: 'Deck landing. Brake before the pallet ramp, then release Go at the lip.',
    };
  }
  // Marker 3 is x≈277; the ascending pallet wedges and containers follow it.
  if (checkpoint === 2 && x >= 285 && x < 353) {
    if (pitchRad > 1.2) return {
      title: 'LOOPED ON THE STEPS',
      action: 'RELEASE LEAN BACK · RIDE LEVEL',
      accessible: 'Looped on the causeway steps. Release lean back and ride the steps level.',
    };
    if (pitchRad < -1.2) return {
      title: 'NOSE-DIVED AT A STEP',
      action: 'BRAKE EARLIER · RIDE LEVEL AT CONTACT',
      accessible: 'Nose-dived at a causeway step. Brake earlier and ride level at contact.',
    };
    return {
      title: 'CAUSEWAY STEPS',
      action: 'SET SPEED EARLY · KEEP THE BIKE LEVEL',
      accessible: 'Causeway steps. Set speed early and keep the bike level.',
    };
  }
  return null;
}
