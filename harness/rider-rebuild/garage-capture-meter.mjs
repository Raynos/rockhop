/** Browser-side capture instrumentation: real render submissions and real RAF.
 * No pose, camera, animation-clock or frame-cap changes. */
export function installGarageCaptureMeter() {
  const owner = window.__render, gpu = owner?.renderer;
  if (!owner || typeof owner.render !== 'function' || !Number.isFinite(gpu?.info?.render?.frame)) {
    throw new Error('Actual Three renderer frame counter required for Garage FPS');
  }
  if (window.__garageCaptureMeter) throw new Error('Garage capture meter already installed');
  const productMeter = document.querySelector('.fpsmeter');
  const productMeterVisible = !!productMeter && !productMeter.hidden
    && getComputedStyle(productMeter).display !== 'none';
  // The product pill counts App frames. This capture always shows actual
  // Three render submissions separately, including skipped-draw detection.
  const overlay = document.createElement('pre');
  if (overlay) {
    overlay.id = 'garage-capture-fps';
    overlay.setAttribute('aria-label', 'Measured Garage render performance');
    overlay.style.cssText = 'position:fixed;left:50%;top:12px;transform:translateX(-50%);'
      + 'z-index:2147483647;pointer-events:none;margin:0;padding:9px 13px;border-radius:5px;'
      + 'background:rgba(0,0,0,.86);color:#fff;font:14px/1.4 monospace;font-variant-numeric:tabular-nums;';
    overlay.textContent = 'GAME RENDER FPS: measuring actual frames…\nRAF: measuring actual callbacks…';
    document.body.append(overlay);
  }
  const original = owner.render;
  let start = performance.now(), lastPaint = start, rafId, active = true;
  const rendered = [], raf = [], cpuMs = [], samples = [];
  let renderCalls = 0, skippedCalls = 0;
  const percentile = (values, fraction) => {
    if (!values.length) return null;
    const sorted = [...values].sort((a, b) => a - b);
    return sorted[Math.min(sorted.length - 1, Math.floor(sorted.length * fraction))];
  };
  const gaps = times => times.slice(1).map((t, i) => t - times[i]);
  const measure = (times, end) => {
    const intervals = gaps(times);
    return { frames: times.length, fps: times.length * 1000 / Math.max(1, end - start),
      intervalMs: { p50: percentile(intervals, .5), p95: percentile(intervals, .95),
        maximum: intervals.length ? Math.max(...intervals) : null } };
  };
  function wrapped(...args) {
    const before = gpu.info.render.frame, at = performance.now();
    try { return original.apply(this, args); }
    finally {
      const end = performance.now(); renderCalls++;
      // Multiple Three passes belong to one game render. An unchanged-frame
      // early return advances no Three frame counter and counts as skipped.
      if (gpu.info.render.frame > before) { rendered.push(end); cpuMs.push(end - at); }
      else skippedCalls++;
    }
  }
  owner.render = wrapped;
  function heartbeat() {
    if (!active) return;
    const now = performance.now();
    raf.push(now);
    if (now - lastPaint >= 500) {
      const since = Math.max(start, now - 2000);
      const recent = rendered.filter(t => t >= since), recentRaf = raf.filter(t => t >= since);
      const intervals = gaps(recent), ms = now - since;
      const sample = { elapsedMs: now - start, windowMs: ms, renderedFrames: recent.length,
        renderFPS: recent.length * 1000 / Math.max(1, ms), rafFPS: recentRaf.length * 1000 / Math.max(1, ms),
        frameMsP50: percentile(intervals, .5), frameMsP95: percentile(intervals, .95) };
      samples.push(sample);
      if (overlay) {
        const fmt = value => value === null ? '—' : value.toFixed(1);
        overlay.textContent = `GAME RENDER ${sample.renderFPS.toFixed(1)} FPS · frame ${fmt(sample.frameMsP50)} / ${fmt(sample.frameMsP95)} ms p50/p95\n`
          + `RAF ${sample.rafFPS.toFixed(1)} callbacks/s · actual wall clock\nVideo stream rate measured separately after capture`;
      }
      lastPaint = now;
    }
    rafId = requestAnimationFrame(heartbeat);
  }
  rafId = requestAnimationFrame(heartbeat);
  const read = () => {
    const end = performance.now();
    return { durationMs: end - start, renderCalls, skippedCalls, rendered: measure(rendered, end),
      raf: measure(raf, end), renderCpuMs: { p50: percentile(cpuMs, .5), p95: percentile(cpuMs, .95) },
      samples: [...samples], productMeterVisible, overlay: overlay ? 'actual render/RAF capture meter' : 'existing product FPS HUD',
      meaning: 'One game render counted only when Three render.frame advances; multiple passes coalesced. CPU submissions, not GPU completion or encoded video frames.' };
  };
  window.__garageCaptureMeter = { read, reset() {
    // Reset measurement only; never touch the application's animation clock.
    start = lastPaint = performance.now();
    rendered.length = raf.length = cpuMs.length = samples.length = 0;
    renderCalls = skippedCalls = 0;
  }, stop() {
    const result = read(); active = false; cancelAnimationFrame(rafId);
    if (owner.render === wrapped) owner.render = original;
    return result;
  } };
  return { productMeterVisible, overlayInstalled: !!overlay };
}
