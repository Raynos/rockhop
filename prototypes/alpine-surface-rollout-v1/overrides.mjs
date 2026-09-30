/** Extend the existing accepted A1 surface settings to the two audited Alpine courses. */
export function overrides(files) {
  const biome='src/render/world/biomeKit.ts',deck='src/render/world/zones/zoneDeck.ts';
  const prior="track.def.id === 'a1-sawdust'";
  const next="['a1-sawdust','a2-log-jam','a3-timberline'].includes(track.def.id)";
  if(files[biome].split(prior).length!==2||files[deck].split(prior).length!==3)throw new Error('Current accepted surface anchors changed');
  return {[biome]:files[biome].replace(prior,next),
    [deck]:files[deck].replaceAll(prior,next)};
}
