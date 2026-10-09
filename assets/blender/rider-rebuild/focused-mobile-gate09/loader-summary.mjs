/** Summarize painted counters; timing never invents progress or a phone result. */
export function summarizeLoader(events) {
  const rows = events.filter(row => row.kind === 'loader');
  const dwell = [], regressions = [];
  let previous, removed = false, reinserted = false, finished = false;
  for (const row of rows) {
    const detail = row.detail;
    if (!detail.present) removed = true;
    else if (removed) reinserted = true;
    if (detail.done === '1' && detail.download === '100' && detail.setup === '100') finished = true;
    if (previous?.detail.present) {
      const a = previous.detail;
      const ms = Math.max(0, row.atMs - previous.atMs);
      const key = [a.download, a.setup, a.step, a.setupLine, a.downloadLine];
      const last = dwell.at(-1);
      if (last && JSON.stringify(last.key) === JSON.stringify(key)) last.ms += ms;
      else dwell.push({ key, atMs: previous.atMs, ms });
      if (detail.present) for (const field of ['download', 'setup']) {
        if (a[field] !== null && detail[field] !== null && Number(detail[field]) < Number(a[field]))
          regressions.push({ atMs: row.atMs, field, before: Number(a[field]), after: Number(detail[field]) });
      }
    }
    previous = row;
  }
  const counterDwell = field => {
    const index = field === 'download' ? 0 : 1;
    const runs = [];
    for (const row of dwell) {
      const value = row.key[index];
      if (value === null) continue;
      const last = runs.at(-1);
      if (last?.value === Number(value)) last.ms += row.ms;
      else runs.push({ value: Number(value), atMs: row.atMs, ms: row.ms });
    }
    return { runs, longest30Ms: Math.max(0, ...runs.filter(row => row.value === 30).map(row => row.ms)) };
  };
  return { finished, removed, reinserted, regressions, dwell,
    download: counterDwell('download'), setup: counterDwell('setup'),
    removedAtMs: rows.find(row => !row.detail.present)?.atMs ?? null,
    limit: 'Observed rendered counters and stage text on this host/network; no physical iPhone stall acceptance.' };
}
