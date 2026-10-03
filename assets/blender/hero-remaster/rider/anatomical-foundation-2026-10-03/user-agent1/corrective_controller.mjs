export function correctiveCoefficients(pose, config, centers) {
  const distances = centers.map(center => Math.sqrt(config.joints.reduce((sum, name) => {
    const current = pose[name].quaternionWXYZ, target = center.jointLocalQuaternionsWXYZ[name];
    const dot = current.reduce((s, v, i) => s + v * target[i], 0);
    const angle = 2 * Math.acos(Math.min(1, Math.abs(dot)));
    return sum + angle * angle;
  }, 0)));
  const minimum = Math.min(...distances);
  if (minimum < 1e-5) return distances.slice(1).map((_, i) => Number(i + 1 === distances.indexOf(minimum)));
  const inverse = distances.map(d => d ** -4), sum = inverse.reduce((a, b) => a + b, 0);
  return inverse.slice(1).map(w => w / sum);
}
