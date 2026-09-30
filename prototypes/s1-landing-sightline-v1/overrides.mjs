/** One targeted S1 station camera key; existing frozen paired build recipe. */
export function overrides(files) {
 const file='src/tracks/rockhop/snowline.ts';
 const before="  .flat(30) // 28 m is the GO failure threshold; 2 m of margin keeps the repeatable overspeed landing legible\n  .camera({ mode: 'side-tight', zoomBias: -0.4 })";
 const after="  .camera({ mode: 'side-tight', zoomBias: 0.4, screenX: 0.32, pitch: 0.55, blend: 0.45 })\n  .flat(30) // 28 m is the GO failure threshold; 2 m of margin keeps the repeatable overspeed landing legible";
 if(files[file].split(before).length!==2) throw new Error('S1 camera anchor changed');
 return {[file]:files[file].replace(before,after)};
}
