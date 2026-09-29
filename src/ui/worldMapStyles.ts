/** 3D island level select chrome; the terrain and twelve towers live in Three.js. */
export const WORLD_MAP_CSS = `
.worldmap-screen { background: #103a48; overflow: hidden; font-family: var(--font); }
.worldmap-screen.leave { transition: opacity var(--t3) var(--ease); opacity: 0; }
.worldmap-screen .wm3d-host { position: absolute; inset: 0; z-index: 0; overflow: hidden; background: #1c5265; touch-action: none; }
.worldmap-screen .wm3d-host canvas { display: block; width: 100%; height: 100%; touch-action: none; }
.worldmap-screen .wm-brand { position: absolute; left: calc(16px + var(--sal)); top: calc(12px + var(--sat)); z-index: 5; color: var(--cream); pointer-events: none; text-shadow: 0 2px 8px #092c38; }
.worldmap-screen .wm-brand .plate { display: flex; align-items: center; gap: 12px; }
.worldmap-screen .wm-brand .wordmark svg { width: clamp(115px, 16vw, 178px); height: auto; }
.worldmap-screen .wm-brand span { font: 800 10px/1 var(--sans); letter-spacing: .18em; text-transform: uppercase; }
.worldmap-screen .wm-brand .stamp { font: 700 9px/1.4 var(--mono); opacity: .7; }
.worldmap-screen .backbtn { top: calc(12px + var(--sat)); z-index: 6; }
.worldmap-screen .wm-progress { position: absolute; left: calc(16px + var(--sal)); bottom: calc(12px + var(--sab)); z-index: 6; display: flex; align-items: center; gap: 12px; padding: 8px 10px; border-radius: 7px; background: #10272ed9; color: var(--cream); font: 800 11px/1 var(--sans); letter-spacing: .07em; }
.worldmap-screen .wm-progress .dots { display: flex; gap: 6px; align-items: center; }
.worldmap-screen .wm-progress .dots span { display: flex; align-items: center; gap: 2px; }
.worldmap-screen .wm-progress svg { width: 14px; height: 14px; }
.worldmap-screen .wm3d-detail { position: absolute; left: 50%; top: calc(12px + var(--sat)); z-index: 5; transform: translateX(-50%); min-width: min(27vw, 210px); max-width: min(35vw, 280px); padding: 8px 12px; border-radius: 10px; background: rgba(15,31,35,.94); box-shadow: 0 0 0 1px rgba(239,227,200,.25), 0 8px 25px #09181c99; color: var(--cream); text-align: center; pointer-events: none; }
.worldmap-screen .wm3d-detail .head { color: var(--ochre); font: 800 10px/1.2 var(--sans); letter-spacing: .11em; text-transform: uppercase; }
.worldmap-screen .wm3d-detail .name { margin-top: 3px; font: 400 21px/1 var(--display); text-transform: uppercase; }
.worldmap-screen .wm3d-detail .times { margin-top: 4px; color: var(--ink-dim); font: 700 11px/1.2 var(--mono); }
.worldmap-screen .wm3d-detail .times b { color: var(--green); }
.worldmap-screen .wm3d-detail .rule { margin-top: 5px; color: var(--ochre); font: 800 10px/1.2 var(--sans); text-transform: uppercase; }
.worldmap-screen .wm3d-detail .board { display: none; }
.worldmap-screen .wm3d-detail .wm3d-medal { margin-top: 5px; font: 800 10px/1.2 var(--sans); letter-spacing: .08em; text-transform: uppercase; }
.worldmap-screen .wm3d-detail .wm3d-medal.bronze { color: #dba372; }
.worldmap-screen .wm3d-detail .wm3d-medal.silver { color: #e0e8e4; }
.worldmap-screen .wm3d-detail .wm3d-medal.gold { color: #f4c34c; }
.worldmap-screen .wm3d-detail .wm3d-medal.platinum { color: #7af0ee; }
.worldmap-screen .wm-actions { position: absolute; right: calc(18px + var(--sar)); bottom: calc(12px + var(--sab)); z-index: 6; display: flex; gap: 8px; }
#ui .wm-actions button { min-height: 48px; min-width: 48px; border: 0; padding: 0 15px; cursor: pointer; font: 800 15px/1 var(--sans); text-transform: uppercase; }
#ui .wm-actions button small { display: block; margin-top: 3px; font: 700 9px/1 var(--sans); letter-spacing: .05em; }
#ui .wm-actions .wm-ride { color: var(--teal); background: var(--cream); border-radius: 10px; box-shadow: 0 6px 20px #09232bb8; }
#ui .wm-actions .wm-ride[disabled] { color: var(--ink-dim); background: #162a2c; cursor: default; }
#ui .wm-actions .wm-ghost { color: var(--cream); background: #162a2c; border-radius: 10px; }
#ui .wm-actions .wm-ghost[hidden] { display: none; }
#ui .wm-actions button.on { outline: 3px solid var(--ochre); }
.worldmap-screen .legend { display: none; }
.worldmap-screen .wm3d-rotate { display: none; position: absolute; inset: 0; z-index: 10; align-items: center; justify-content: center; flex-direction: column; gap: 12px; background: radial-gradient(circle at 50% 40%, #247283, #0c454e 72%); color: var(--cream); text-align: center; text-transform: uppercase; }
.worldmap-screen .wm3d-rotate span { font-size: 72px; line-height: 1; }
.worldmap-screen .wm3d-rotate strong { font: 400 clamp(28px, 7vw, 48px)/1 var(--display); }
.worldmap-screen .wm3d-rotate small { font: 700 13px/1.4 var(--sans); letter-spacing: .18em; }
.worldmap-screen .wm3d-rotate.show { display: flex; }
.worldmap-screen .wm3d-loading { display: none; position: absolute; inset: 0; z-index: 8; align-items: center; justify-content: center; flex-direction: column; gap: 16px; background: radial-gradient(circle at center, #246775, #0d3742 75%); color: var(--cream); text-align: center; }
.worldmap-screen .wm3d-loading.show { display: flex; }
.worldmap-screen .wm3d-loading strong { font: 400 24px/1 var(--display); text-transform: uppercase; }
.worldmap-screen .wm3d-loading .spinner { width: 45px; height: 45px; border: 4px solid #ffffff44; border-top-color: var(--cream); border-radius: 50%; animation: wm3d-spin 1s linear infinite; }
@keyframes wm3d-spin { to { transform: rotate(360deg); } }
.worldmap-screen .wm3d-loading button { min-width: 110px; min-height: 46px; border-radius: 8px; border: 1px solid var(--cream); color: var(--cream); background: #125861; font: 800 13px var(--sans); text-transform: uppercase; }
.worldmap-screen .wm3d-failure { display: none; position: absolute; inset: 0; z-index: 8; align-items: center; justify-content: center; flex-direction: column; gap: 12px; background: #0c2935; color: var(--cream); text-align: center; }
.worldmap-screen .wm3d-failure.show { display: flex; }
.worldmap-screen .wm3d-failure strong { font: 400 32px/1 var(--display); }
.worldmap-screen .wm3d-failure p { margin: 0; font: 700 14px/1.4 var(--sans); }
.worldmap-screen .wm3d-failure button { min-width: 110px; min-height: 46px; border-radius: 8px; border: 1px solid var(--cream); color: var(--cream); background: #125861; font: 800 13px var(--sans); text-transform: uppercase; }
@media (orientation: portrait) {
  .worldmap-screen .wm3d-host, .worldmap-screen .wm-brand, .worldmap-screen .backbtn, .worldmap-screen .wm-progress, .worldmap-screen .wm3d-detail, .worldmap-screen .wm-actions, .worldmap-screen .wm3d-loading, .worldmap-screen .wm3d-failure { display: none; }
  .worldmap-screen .wm3d-rotate { display: flex; }
}
`;

export function injectWorldMapStyles(): void {
  if (document.getElementById('worldmap-css')) return;
  const style = document.createElement('style');
  style.id = 'worldmap-css';
  style.textContent = WORLD_MAP_CSS;
  document.head.appendChild(style);
}
