/** Prototype-only contextual C1 cue. Mount on the game page; update once per rendered frame. */
export function installC1Cue(): (bikeX: number) => void {
  const previous = document.getElementById('c1-slowdown-cue');
  previous?.remove();
  const cue = document.createElement('div');
  cue.id = 'c1-slowdown-cue';
  cue.setAttribute('role', 'status');
  cue.setAttribute('aria-label', 'Ease off. Brake before the pallet ramp.');
  cue.style.cssText = [
    'position:fixed',
    'left:max(18px,env(safe-area-inset-left))',
    'top:56px',
    'z-index:9999',
    'width:252px',
    'height:66px',
    'box-sizing:border-box',
    'display:none',
    'align-items:center',
    'gap:11px',
    'padding:8px 12px',
    'border:2px solid #ffbe50',
    'border-radius:11px',
    'background:rgba(9,39,45,.94)',
    'box-shadow:0 3px 0 #642d1c,0 8px 20px rgba(0,0,0,.25)',
    'pointer-events:none',
    'font-family:system-ui,-apple-system,sans-serif',
    'color:#fff5d8',
    'text-align:left',
  ].join(';');
  cue.innerHTML = '<span aria-hidden="true" style="display:grid;place-items:center;flex:0 0 36px;height:36px;border-radius:7px;background:#ffbd4e;color:#163b3e;font-size:25px;font-weight:950;line-height:1">↓</span><span style="display:flex;flex-direction:column;min-width:0"><strong style="font-size:20px;line-height:22px;font-weight:950;letter-spacing:.07em;white-space:nowrap">EASE OFF</strong><small style="font-size:13px;line-height:17px;font-weight:800;white-space:nowrap;color:#f6ddaa">BRAKE BEFORE THE RAMP</small></span>';
  document.body.append(cue);
  return (bikeX: number) => {
    // Marker 2 checkpoint (x=179.6), then the girder and 18 m braking lane; hide at the ramp foot.
    cue.style.display = bikeX >= 179.6 && bikeX < 209.6 ? 'flex' : 'none';
  };
}
