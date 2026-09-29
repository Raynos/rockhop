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
.worldmap-screen .wm-progress { display: flex; flex-direction: column; justify-content: center; align-items: flex-start; gap: 7px; min-width: 0; color: var(--cream); font: 800 11px/1 var(--sans); letter-spacing: .07em; text-transform: uppercase; white-space: nowrap; }
.worldmap-screen .wm-progress .n b { color: #ffaf3c; font-size: 17px; }
.worldmap-screen .wm-progress .dots { display: flex; gap: 6px; align-items: center; }
.worldmap-screen .wm-progress .dots span { display: flex; align-items: center; gap: 2px; }
.worldmap-screen .wm-progress svg { width: 14px; height: 14px; }
.worldmap-screen .wm3d-detail { display: none; }
.worldmap-screen .wm3d-detail .head { color: var(--ochre); font: 800 10px/1.2 var(--sans); letter-spacing: .11em; text-transform: uppercase; }
.worldmap-screen .wm3d-detail .name { margin-top: 3px; font: 400 21px/1 var(--display); text-transform: uppercase; }
.worldmap-screen .wm3d-detail .times { margin-top: 4px; color: var(--ink-dim); font: 700 11px/1.2 var(--mono); }
.worldmap-screen .wm3d-detail .times b { color: var(--green); }
.worldmap-screen .wm3d-detail .rule { margin-top: 5px; color: var(--ochre); font: 800 10px/1.2 var(--sans); text-transform: uppercase; }
.worldmap-screen .wm3d-detail .board { display: none; }
.worldmap-screen .wm3d-detail .wm3d-state { margin-top: 5px; font: 800 10px/1.2 var(--sans); letter-spacing: .08em; text-transform: uppercase; }
.worldmap-screen .wm3d-detail .wm3d-state.available { color: #ffd17a; }
.worldmap-screen .wm3d-detail .wm3d-state.locked { color: #9baaad; }
.worldmap-screen .wm3d-detail .wm3d-state.bronze { color: #dd9161; }
.worldmap-screen .wm3d-detail .wm3d-state.silver { color: #d9e8e8; }
.worldmap-screen .wm3d-detail .wm3d-state.gold { color: #ffd44f; }
.worldmap-screen .wm3d-detail .wm3d-state.platinum { color: #72f4ee; }
.worldmap-screen .wm-dock { position: absolute; inset: auto 0 0; z-index: 6; display: grid; grid-template-columns: minmax(146px,1fr) 48px minmax(190px,1.4fr) 48px 84px minmax(170px,1.2fr); align-items: center; gap: 8px; padding: 8px calc(12px + var(--sar)) calc(8px + var(--sab)) calc(12px + var(--sal)); border-top: 1px solid #c6e2d771; background: linear-gradient(180deg, #132e36ee, #071e26f5); box-shadow: 0 -8px 30px #0a25368a; }
#ui .worldmap-screen .wm-dock button { min-height: 54px; min-width: 0; cursor: pointer; border: 1px solid #a8c9c183; border-radius: 9px; color: var(--cream); background: #183a43eb; font: 800 13px/1 var(--sans); text-transform: uppercase; }
#ui .worldmap-screen .wm-dock button:focus-visible, #ui .worldmap-screen .wm-orbit:focus-visible, #ui .worldmap-screen .wm-level-tray button:focus-visible { outline: 3px solid #ffcc77; outline-offset: 2px; }
#ui .worldmap-screen .wm-dock button.on, #ui .worldmap-screen .wm-ghost.on { outline: 3px solid var(--ochre); outline-offset: 2px; }
#ui .worldmap-screen .wm-dock .wm-step { font: 400 37px/1 var(--display); }
#ui .worldmap-screen .wm-dock .wm-step span { position: relative; top: -2px; }
#ui .worldmap-screen .wm-dock .wm-ride { display: flex; align-items: center; gap: 8px; padding: 4px 7px; text-align: left; overflow: hidden; }
#ui .worldmap-screen .wm-dock .wm-ride .thumb { flex: 0 0 56px; width: 56px; height: 46px; object-fit: cover; border-radius: 5px; border: 1px solid #dfd7b396; }
#ui .worldmap-screen .wm-dock .wm-ride .copy { min-width: 0; flex: 1; }
#ui .worldmap-screen .wm-dock .wm-ride strong { display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font: 800 13px/1.1 var(--sans); }
#ui .worldmap-screen .wm-dock .wm-ride small { display: block; margin-top: 4px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font: 700 9px/1.1 var(--sans); letter-spacing: .04em; }
#ui .worldmap-screen .wm-dock .wm-ride em { font-style: normal; }
#ui .worldmap-screen .wm-dock .wm-ride em.available { color: #93ef9a; }
#ui .worldmap-screen .wm-dock .wm-ride em.locked { color: #abbcba; }
#ui .worldmap-screen .wm-dock .wm-ride em.bronze { color: #e7a273; }
#ui .worldmap-screen .wm-dock .wm-ride em.silver { color: #d4e7ec; }
#ui .worldmap-screen .wm-dock .wm-ride em.gold { color: #ffd477; }
#ui .worldmap-screen .wm-dock .wm-ride em.platinum { color: #79f2ee; }
#ui .worldmap-screen .wm-dock .wm-medal-ladder { display: flex; gap: 5px; margin-top: 4px; }
#ui .worldmap-screen .wm-dock .wm-medal-ladder i { display: block; width: 9px; height: 9px; border: 1px solid #dce9db; border-radius: 50%; box-shadow: inset 0 1px 2px #ffffff88, 0 1px 2px #061b1dbb; }
#ui .worldmap-screen .wm-dock .wm-medal-ladder i.bronze { background: #be784c; }
#ui .worldmap-screen .wm-dock .wm-medal-ladder i.silver { background: #d4e3e6; }
#ui .worldmap-screen .wm-dock .wm-medal-ladder i.gold { background: #ffd258; }
#ui .worldmap-screen .wm-dock .wm-medal-ladder i.platinum { background: #70eeed; }
#ui .worldmap-screen .wm-dock .wm-medal-ladder i.unearned { background: #304b50; border-color: #718789; }
#ui .worldmap-screen .wm-dock .wm-ride .rule { color: #ffd477; }
#ui .worldmap-screen .wm-dock .wm-ride .ride-arrow { color: #ffb754; font: 800 10px/1 var(--sans); white-space: nowrap; }
#ui .worldmap-screen .wm-dock .wm-ride[disabled] { opacity: .72; cursor: default; }
#ui .worldmap-screen .wm-dock .wm-levels { white-space: nowrap; }
#ui .worldmap-screen .wm-dock .wm-levels span { margin-right: 4px; font-size: 20px; vertical-align: -2px; }
#ui .worldmap-screen .wm-dock .wm-levels[aria-expanded="true"] { color: #152f37; background: #f0ddae; }
#ui .worldmap-screen .wm-dock .wm-quick { display: flex; align-items: center; justify-content: center; gap: 10px; border: 0; color: #183238; background: linear-gradient(#ffbd4f, #ff941d); box-shadow: inset 0 1px #ffe4a0, 0 4px 16px #07181a80; }
#ui .worldmap-screen .wm-dock .wm-quick .play { font-size: 20px; }
#ui .worldmap-screen .wm-dock .wm-quick small { display: block; margin-top: 4px; font: 800 9px/1 var(--sans); letter-spacing: .04em; }
#ui .worldmap-screen .wm-orbit { position: absolute; right: calc(114px + var(--sar)); top: calc(12px + var(--sat)); z-index: 6; min-height: 44px; padding: 0 14px; border: 1px solid #bed3ca9c; border-radius: 999px; color: var(--cream); background: #103943e8; font: 800 11px/1 var(--sans); text-transform: uppercase; cursor: pointer; }
#ui .worldmap-screen .wm-orbit small { display: none; }
#ui .worldmap-screen .wm-orbit[aria-pressed="true"] { color: #173841; background: #ffd17a; }
.worldmap-screen .wm-level-tray { position: absolute; right: calc(12px + var(--sar)); bottom: calc(82px + var(--sab)); z-index: 7; width: min(580px, calc(100% - 24px - var(--sal) - var(--sar))); max-height: calc(100% - 100px - var(--sat) - var(--sab)); overflow: auto; padding: 10px; border: 1px solid #c7ded2ae; border-radius: 12px; background: #0c2730f7; box-shadow: 0 14px 36px #041419c7; color: var(--cream); }
.worldmap-screen .wm-level-tray[hidden] { display: none; }
.worldmap-screen .wm-level-tray-head { display: flex; align-items: center; gap: 12px; margin-bottom: 8px; font: 800 11px/1.2 var(--sans); text-transform: uppercase; letter-spacing: .06em; }
.worldmap-screen .wm-level-tray-head span { flex: 1; opacity: .7; font-size: 9px; }
#ui .worldmap-screen .wm-ghost { position: absolute; right: calc(12px + var(--sar)); top: calc(64px + var(--sat)); z-index: 6; min-height: 44px; padding: 0 13px; border: 1px solid #bdd5c099; border-radius: 8px; color: var(--cream); background: #285058; font: 800 10px var(--sans); text-transform: uppercase; cursor: pointer; }
#ui .worldmap-screen .wm-ghost[hidden] { display: none; }
.worldmap-screen .wm-level-grid { display: grid; grid-template-columns: repeat(6, minmax(0,1fr)); gap: 6px; }
#ui .worldmap-screen .wm-level { display: flex; align-items: center; gap: 4px; min-width: 0; min-height: 45px; padding: 4px 5px; border: 1px solid #7da5a594; border-radius: 7px; color: var(--cream); background: #1b3c44; text-align: left; cursor: pointer; }
#ui .worldmap-screen .wm-level b { color: #ffd18a; font: 800 12px/1 var(--sans); }
#ui .worldmap-screen .wm-level span { overflow: hidden; flex: 1; white-space: nowrap; text-overflow: ellipsis; font: 700 9px/1.2 var(--sans); }
#ui .worldmap-screen .wm-level small { color: #adc6c3; font-size: 12px; }
#ui .worldmap-screen .wm-level svg { width: 15px; height: 15px; }
#ui .worldmap-screen .wm-level.locked { opacity: .56; }
#ui .worldmap-screen .wm-level.selected { border-color: #ffbd4f; box-shadow: inset 0 0 0 1px #ffbd4f; }
.worldmap-screen .wm-level-summary { display: flex; align-items: center; flex-wrap: wrap; gap: 5px 12px; min-height: 27px; margin-top: 8px; padding: 7px 4px 0; border-top: 1px solid #a0c0b16e; font: 700 10px/1.2 var(--sans); }
.worldmap-screen .wm-level-summary b { color: #ffd18a; text-transform: uppercase; }
.worldmap-screen .wm-level-summary span { color: var(--cream); }
.worldmap-screen .wm-level-summary .board { display: flex; gap: 6px; width: 100%; }
.worldmap-screen .wm-level-summary .board span { padding: 3px 5px; border-radius: 4px; background: #345459; font: 700 9px/1 var(--mono); }
@media (max-width: 780px) and (orientation: landscape) {
  .worldmap-screen .wm-dock { grid-template-columns: 44px minmax(0,1fr) 44px 68px minmax(135px,1fr); }
  .worldmap-screen .wm-progress { position: absolute; left: calc(12px + var(--sal)); bottom: calc(74px + var(--sab)); padding: 6px 8px; border-radius: 6px; background: #10272eea; }
  .worldmap-screen .wm-progress .dots { display: none; }
  #ui .worldmap-screen .wm-dock .wm-ride .thumb { display: none; }
  #ui .worldmap-screen .wm-dock .wm-levels { font-size: 10px; }
  #ui .worldmap-screen .wm-dock .wm-levels span { margin-right: 0; }
  .worldmap-screen .wm-level-grid { grid-template-columns: repeat(4, minmax(0,1fr)); }
}
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
  .worldmap-screen .wm3d-host, .worldmap-screen .wm-brand, .worldmap-screen .backbtn, .worldmap-screen .wm-progress, .worldmap-screen .wm3d-detail, .worldmap-screen .wm-dock, .worldmap-screen .wm-orbit, .worldmap-screen .wm-ghost, .worldmap-screen .wm-level-tray, .worldmap-screen .wm3d-loading, .worldmap-screen .wm3d-failure { display: none; }
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
