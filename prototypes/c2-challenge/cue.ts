/** Prototype-only timing cue for the crane landing, shown in the rendered play clip. */
export function installC2Cue(): (bikeX: number) => void {
  document.getElementById('c2-air-cue')?.remove();
  const cue = document.createElement('div');
  cue.id = 'c2-air-cue';
  cue.setAttribute('role', 'status');
  cue.setAttribute('aria-label', 'Level the bike in flight. Release GO or lean forward to meet the barge.');
  cue.style.cssText = [
    'position:fixed', 'left:max(18px,env(safe-area-inset-left))', 'top:56px', 'z-index:9999',
    'width:265px', 'height:66px', 'box-sizing:border-box', 'display:none', 'align-items:center',
    'gap:11px', 'padding:8px 12px', 'border:2px solid #ffbe50', 'border-radius:11px',
    'background:rgba(9,39,45,.94)', 'box-shadow:0 3px 0 #642d1c,0 8px 20px rgba(0,0,0,.25)',
    'pointer-events:none', 'font-family:system-ui,-apple-system,sans-serif', 'color:#fff5d8', 'text-align:left',
  ].join(';');
  cue.innerHTML = '<span aria-hidden="true" style="display:grid;place-items:center;flex:0 0 36px;height:36px;border-radius:7px;background:#ffbd4e;color:#163b3e;font-size:22px;font-weight:950;line-height:1">↘</span><span style="display:flex;flex-direction:column;min-width:0"><strong style="font-size:19px;line-height:22px;font-weight:950;letter-spacing:.03em;white-space:nowrap">LEVEL THE BIKE</strong><small style="font-size:12px;line-height:17px;font-weight:800;white-space:nowrap;color:#f6ddaa">RELEASE OR LEAN FORWARD</small></span>';
  document.body.append(cue);
  return (bikeX: number) => { cue.style.display = bikeX >= 284 && bikeX < 323 ? 'flex' : 'none'; };
}
