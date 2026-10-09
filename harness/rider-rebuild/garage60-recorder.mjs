/** Browser function injected only after the actual selected Garage is ready.
 * Copy the live WebGL surface before presentation discards its buffer. The
 * capture canvas is separate; no product pixels, camera or clock are changed.
 */
export function installGarage60Recorder({ fps = 60, bitrate = 16000000, expectedSourceSHA256,
  schedulerTestOnlyStart = null }) {
  // Self-contained so Playwright can serialize this exact browser function.
  // The CPU fixture branch returns the SAME stateful kernel before touching DOM.
  if (!Number.isFinite(fps) || fps <= 0) throw new Error('Positive nominal rate required');
  const period = 1000 / fps;
  const createSlotScheduler = start => {
    let lastSlot = -1;
    return at => {
      const slot = Math.floor((at-start)/period+.5);
      if (slot <= lastSlot) return null;
      lastSlot = slot;
      return slot;
    };
  };
  if (schedulerTestOnlyStart !== null) return createSlotScheduler(schedulerTestOnlyStart);
  const owner = globalThis.window.__render, gpu = owner?.renderer, surface = owner?.canvas;
  if (!owner || typeof owner.render !== 'function' || !surface || !Number.isFinite(gpu?.info?.render?.frame))
    throw new Error('Actual game WebGL canvas/render counter required');
  if (globalThis.window.__garage60Recorder) throw new Error('Recorder already installed');
  const gl=gpu.getContext(),debug=gl.getExtension('WEBGL_debug_renderer_info');
  const actualRenderer=String(gl.getParameter(debug?debug.UNMASKED_RENDERER_WEBGL:gl.RENDERER));
  if (!/Metal/.test(actualRenderer)) throw new Error('Actual game canvas must use Metal');
  const canvas = globalThis.document.createElement('canvas');
  canvas.width = surface.width; canvas.height = surface.height;
  const ctx = canvas.getContext('2d', { alpha: false });
  if (!ctx || !canvas.captureStream || !globalThis.window.MediaRecorder) throw new Error('Canvas recording unavailable');
  const choices = ['video/mp4;codecs=avc1.42001E', 'video/webm;codecs=vp8'];
  const mimeType = choices.find(type => globalThis.MediaRecorder.isTypeSupported(type));
  if (!mimeType) throw new Error('No supported H264/VP8 MediaRecorder');
  const stream = canvas.captureStream(0), track = stream.getVideoTracks()[0];
  if (!track || typeof track.requestFrame !== 'function' || stream.getAudioTracks().length)
    throw new Error('Manual video-only canvas capture required');
  const recorder = new globalThis.MediaRecorder(stream, { mimeType, videoBitsPerSecond: bitrate });
  const chunks = [], failures = [], rendered = [], raf = [], requests = [], slots = [], hud = [], copyCpuMs = [];
  const recent = [], recentRaf = [];
  let active = true, armed = false, started = null, ended = null, scheduleSlot = null;
  let heartbeatId, lastHud = -Infinity, label = 'Render / RAF: measuring…', totalBytes = 0;
  const original = owner.render;
  const percentile = (values, q) => [...values].sort((a,b) => a-b)[Math.floor((values.length-1)*q)] ?? null;
  const hudEpoch = performance.now();
  const pollRaf = () => {
    if (!active) return;
    const at = performance.now(); recentRaf.push(at);
    while (recentRaf[0] < at-2000) recentRaf.shift();
    if (started !== null && ended === null) raf.push(at);
    heartbeatId = globalThis.requestAnimationFrame(pollRaf);
  };
  heartbeatId = globalThis.requestAnimationFrame(pollRaf);
  const draw = at => {
    if (surface.width !== canvas.width || surface.height !== canvas.height)
      throw new Error('Drawing buffer resized during film');
    ctx.drawImage(surface, 0, 0); // 1:1 actual submitted surface, no interpolation.
    if (at-lastHud >= 500) {
      const since = Math.max(hudEpoch, at-2000), elapsed = at-since;
      const times = recent.filter(t => t >= since), r = recentRaf.filter(t => t >= since);
      const gaps = times.slice(1).map((t,i) => t-times[i]);
      const row = { at, windowMs: elapsed, renders: times.length, rafs: r.length,
        renderFPS: times.length*1000/elapsed, rafFPS: r.length*1000/elapsed,
        renderGapP95Ms: percentile(gaps,.95) };
      hud.push(row);
      label = `Render ${row.renderFPS.toFixed(1)} FPS | RAF ${row.rafFPS.toFixed(1)} FPS | p95 ${row.renderGapP95Ms?.toFixed(1) ?? '—'} ms`;
      lastHud = at;
    }
    const size = Math.max(12, Math.round(canvas.width/85));
    ctx.fillStyle = 'rgba(0,0,0,.9)'; ctx.fillRect(0,0,canvas.width,size*2.5);
    ctx.fillStyle = '#fff'; ctx.font = `${size}px monospace`;
    ctx.fillText(label,10,size*1.7);
  };
  recorder.ondataavailable = event => {
    if (event.data.size) { chunks.push(event.data); totalBytes += event.data.size; }
  };
  recorder.onerror = event => failures.push(String(event.error?.message ?? 'MediaRecorder error'));
  function wrapped(...args) {
    const before = gpu.info.render.frame;
    const result = original.apply(this,args);
    if (!active || gpu.info.render.frame <= before) return result;
    const at = performance.now(); recent.push(at);
    while (recent[0] < at-2000) recent.shift();
    if (started !== null && ended === null) rendered.push(at);
    if (!armed || ended !== null) return result;
    try {
      if (!globalThis.document.querySelector('.garage-screen.live') || !owner.stageOn
          || owner.debug.rider.debug.candidate.sourceSHA256 !== expectedSourceSHA256)
        throw new Error('Actual selected Garage source disappeared during film');
      if (started === null) {
        draw(at); recorder.start(1000); started = at; scheduleSlot = createSlotScheduler(started);
        rendered.push(at);
      }
      const slot = scheduleSlot(at);
      if (slot !== null) {
        const copyAt=performance.now();draw(at);track.requestFrame();requests.push(at);slots.push(slot);
        copyCpuMs.push(performance.now()-copyAt);
        // One NEW real render per increasing nearest nominal slot. Missing
        // slots are skipped; never catch up or manufacture frames/timestamps.
      }
    } catch (error) { failures.push(error.message); armed = false; }
    return result;
  }
  owner.render = wrapped;
  globalThis.window.__garage60Recorder = {
    arm() { if (armed || started !== null) throw new Error('Recorder cannot restart'); armed = true; },
    started() { return started !== null; },
    async finish() {
      ended = performance.now(); armed = false; active = false; globalThis.cancelAnimationFrame(heartbeatId);
      if (owner.render === wrapped) owner.render = original;
      if (recorder.state !== 'inactive') await new Promise((resolve,reject) => {
        recorder.onstop = resolve; recorder.onerror = event => reject(event.error); recorder.stop();
      });
      stream.getTracks().forEach(value => value.stop());
      if (started === null || failures.length) throw new Error(failures.join('; ') || 'No actual rendered film frame');
      return { mimeType: recorder.mimeType, requestedFPS: fps, videoBitsPerSecond: recorder.videoBitsPerSecond,
        width:canvas.width,height:canvas.height,started,ended,totalBytes,chunkCount:chunks.length,
        actualRenderTimesMs:rendered,actualRafTimesMs:raf,captureRequestTimesMs:requests,captureNominalSlots:slots,hudSamples:hud,
        captureCopyCpuMs:{p50:percentile(copyCpuMs,.5),p95:percentile(copyCpuMs,.95)},
        scope:'Actual Garage WebGL surface plus capture-owned measured HUD; DOM Garage controls are outside canvas.',
        meaning:'Requested60 defines nominal slots, not observed FPS. HUD measures real render submissions/RAF, not GPU completion or encoded frames.' };
    },
    async chunk(index) {
      const bytes = new Uint8Array(await chunks[index].arrayBuffer());
      let text = ''; for (let at=0; at<bytes.length; at+=32768) text += String.fromCharCode(...bytes.subarray(at,at+32768));
      return btoa(text);
    },
    dispose() { active=false;globalThis.cancelAnimationFrame(heartbeatId); if (owner.render===wrapped) owner.render=original;
      if(recorder.state!=='inactive') recorder.stop(); stream.getTracks().forEach(value=>value.stop()); }
  };
  return { supportedMimeTypes:choices.filter(type=>globalThis.MediaRecorder.isTypeSupported(type)),chosenMimeType:mimeType,
    width:canvas.width,height:canvas.height,requestedFPS:fps,audioTracks:stream.getAudioTracks().length,actualRenderer };
}
