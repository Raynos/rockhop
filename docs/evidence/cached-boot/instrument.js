// Injected before page scripts so the loading rows survive DOM removal.
(() => {
  const state = { initT: Math.round(performance.now()), end: 0, rows: {}, phases: [] };
  window.__bootProbe = state;
  const attach = () => {
    const loader = document.getElementById('loader');
    if (!loader) return;
    let prev = '';
    const scan = () => {
      const t = performance.now();
      const label = loader.querySelector('.gauge.su .line')?.textContent ?? '';
      const coarse = label.split(' · ')[0] ?? '';
      if (coarse !== prev) { state.phases.push({ t: Math.round(t), label: coarse }); prev = coarse; }
      for (const li of loader.querySelectorAll('ol li.ok')) {
        const key = li.dataset.key;
        if (key && !(key in state.rows)) state.rows[key] = Math.round(t);
      }
      if (loader.dataset.done === '1' && !state.end) state.end = Math.round(t);
    };
    new MutationObserver(scan).observe(loader, { attributes: true, childList: true, characterData: true, subtree: true });
    scan();
  };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', attach, { once: true });
  else attach();
})();
