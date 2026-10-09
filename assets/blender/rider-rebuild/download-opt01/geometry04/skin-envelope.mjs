// Conservative native hierarchy bound for a weight-only storage derivative.
import assert from 'node:assert/strict';
import { accessorBytes } from '../geometry01/glb.mjs';
export async function buildSkinEnvelope(glb, rootTranslationLimitMeters = 4) {
  const j = glb.json, skin = j.skins[0];
  assert.equal(j.skins.length, 1);
  const parent = new Map();
  for (const [i, node] of j.nodes.entries()) for (const child of node.children ?? []) parent.set(child, i);
  const scales = j.nodes.map(n => Math.max(...(n.scale ?? [1, 1, 1]).map(Math.abs)));
  const translations = j.nodes.map(n => Math.hypot(...(n.translation ?? [0, 0, 0])));
  for (const animation of j.animations ?? []) for (const channel of animation.channels) {
    if (!['scale', 'translation'].includes(channel.target.path)) continue;
    const sampler = animation.samplers[channel.sampler];
    assert.equal(sampler.interpolation ?? 'LINEAR', 'LINEAR');
    const bytes = await accessorBytes(glb, sampler.output);
    const values = new Float32Array(bytes.buffer, bytes.byteOffset, bytes.length / 4);
    for (let first = 0; first < values.length; first += 3) {
      if (channel.target.path === 'scale') scales[channel.target.node] = Math.max(scales[channel.target.node],
        ...values.subarray(first, first + 3).map(Math.abs));
      else translations[channel.target.node] = Math.max(translations[channel.target.node],
        Math.hypot(...values.subarray(first, first + 3)));
    }
  }
  const jointNodes = new Set(skin.joints);
  const rootNodes = skin.joints.filter(i => !jointNodes.has(parent.get(i)));
  assert.equal(rootNodes.length, 1);
  translations[rootNodes[0]] = Math.max(translations[rootNodes[0]], rootTranslationLimitMeters);
  const hierarchyScale = j.nodes.map((_, i) => {
    let value = 1, current = i;
    while (current !== undefined) {
      assert(!j.nodes[current].matrix);
      value *= scales[current]; current = parent.get(current);
    }
    return value;
  });
  const bindBytes = await accessorBytes(glb, skin.inverseBindMatrices);
  const binds = new Float32Array(bindBytes.buffer, bindBytes.byteOffset, bindBytes.length / 4);
  const paths = skin.joints.map(node => {
    const result = []; let current = node;
    while (current !== undefined) { result.push(current); current = parent.get(current); }
    return result;
  });
  const pairDistance = new Float64Array(skin.joints.length ** 2);
  for (let a = 0; a < paths.length; a++) for (let b = 0; b < paths.length; b++) {
    let ia = paths[a].length - 1, ib = paths[b].length - 1;
    while (ia >= 0 && ib >= 0 && paths[a][ia] === paths[b][ib]) { ia--; ib--; }
    let distance = 0;
    for (let k = 0; k <= ia; k++) distance += translations[paths[a][k]] * hierarchyScale[parent.get(paths[a][k])] ;
    for (let k = 0; k <= ib; k++) distance += translations[paths[b][k]] * hierarchyScale[parent.get(paths[b][k])] ;
    assert(Number.isFinite(distance)); pairDistance[a * paths.length + b] = distance;
  }
  const rootFrameTranslationBounds = paths.map(p => p.reduce((sum, node) =>
    sum + translations[node] * (hierarchyScale[parent.get(node)] ?? 1), 0));
  const result = { jointCount: skin.joints.length, binds, pairDistance,
    scales: skin.joints.map(i => hierarchyScale[i]), rootFrameTranslationBounds,
    receipt: { rootTranslationLimitMeters, rootNode: j.nodes[rootNodes[0]].name,
      formula: 'sum |deltaWeight_j|*(jointPairPathBound + scaled inverse-bind offsets) + |sum deltaWeight|*referencePointBound',
      covers: 'Any rotations/translations preserving measured local bone translation/scale bounds; native root translation up to recorded limit; source LINEAR tracks',
      excluded: 'Alternate generic assets or future drivers exceeding local bone translation/scale bounds',
      nativeJoints: skin.joints.map((node, joint) => ({ joint, name: j.nodes[node].name,
        hierarchyScaleBound: hierarchyScale[node], localTranslationBound: translations[node],
        rootFrameTranslationBound: rootFrameTranslationBounds[joint] })) } };
  result.weightErrorBound = (position, jointSlots, beforeWeights, afterWeights) => {
    const offsets = new Float64Array(4);
    for (let slot = 0; slot < 4; slot++) {
      const joint = jointSlots[slot], o = joint * 16, m = binds;
      const x = m[o] * position[0] + m[o + 4] * position[1] + m[o + 8] * position[2] + m[o + 12];
      const y = m[o + 1] * position[0] + m[o + 5] * position[1] + m[o + 9] * position[2] + m[o + 13];
      const z = m[o + 2] * position[0] + m[o + 6] * position[1] + m[o + 10] * position[2] + m[o + 14];
      offsets[slot] = Math.hypot(x, y, z) * result.scales[joint];
    }
    let best = Infinity, sumDelta = 0;
    for (let slot = 0; slot < 4; slot++) sumDelta += afterWeights[slot] - beforeWeights[slot];
    for (let reference = 0; reference < 4; reference++) {
      let bound = Math.abs(sumDelta) * (offsets[reference] + rootFrameTranslationBounds[jointSlots[reference]]);
      for (let slot = 0; slot < 4; slot++) {
        if (slot === reference) continue;
        const lever = pairDistance[jointSlots[slot] * paths.length + jointSlots[reference]]
          + offsets[slot] + offsets[reference];
        bound += Math.abs(afterWeights[slot] - beforeWeights[slot]) * lever;
      }
      best = Math.min(best, bound);
    }
    return best;
  };
  return result;
}
export function quantizeWeights(weights) {
  const sum = weights.reduce((s, w) => s + Math.abs(w), 0);
  assert(sum > 0 && weights.every(w => Number.isFinite(w) && w >= 0));
  const normalized = weights.map(w => w / sum);
  const scaled = normalized.map(w => w * 65535);
  const q = scaled.map(Math.floor);
  const order = [0, 1, 2, 3].sort((a, b) => (scaled[b] - q[b]) - (scaled[a] - q[a]) || a - b);
  const remaining = 65535 - q.reduce((s, w) => s + w, 0);
  assert(remaining >= 0 && remaining <= 3);
  for (let i = 0; i < remaining; i++) q[order[i]]++;
  assert.equal(q.reduce((s, w) => s + w, 0), 65535);
  return q;
}
