(() => {
  localStorage.setItem('rockhop.sound', '0');
  const state = { firstScriptMs: Math.round(performance.now()), download100Ms: null, setup100Ms: null, readyMs: null, rows: {}, phases: [], shaderUpdates: [] };
  window.__cachedBootG4 = state;
  const attach = () => {
    const loader = document.getElementById('loader');
    if (!loader) return;
    let prior = '';
    let priorShader = '';
    const scan = () => {
      const now = Math.round(performance.now());
      if (loader.dataset.download === '100' && state.download100Ms === null) state.download100Ms = now;
      if (loader.dataset.setup === '100' && state.setup100Ms === null) state.setup100Ms = now;
      if (loader.dataset.done === '1' && state.readyMs === null) state.readyMs = now;
      const label = (loader.querySelector('.gauge.su .line')?.textContent ?? '').split(' · ')[0] ?? '';
      if (label !== prior) { prior = label; state.phases.push({ ms: now, label }); }
      if (label === 'Shaders') {
        const full = loader.querySelector('.gauge.su .line')?.textContent ?? '';
        if (full !== priorShader) { priorShader = full; state.shaderUpdates.push({ ms: now, label: full }); }
      }
      for (const el of loader.querySelectorAll('ol li.ok')) {
        if (el.dataset.key && !(el.dataset.key in state.rows)) state.rows[el.dataset.key] = now;
      }
    };
    new MutationObserver(scan).observe(loader, { attributes: true, childList: true, characterData: true, subtree: true });
    scan();
  };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', attach, { once: true });
  else attach();
})();
