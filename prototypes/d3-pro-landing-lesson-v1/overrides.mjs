/** Baseline HUD only is the immutable git4623e834 blob; all other current inputs match. */
import {execFileSync} from 'node:child_process';
export function overrides(files) {
 const hud='src/ui/hud.ts';
 const old=execFileSync('git',['show','4623e834:src/ui/hud.ts'],{encoding:'utf8'});
 if(!files[hud].includes("const d3Cart = t.id === 'd3-rope-walk'")) throw new Error('Current D3 HUD lesson missing');
 return {[hud]:old};
}
