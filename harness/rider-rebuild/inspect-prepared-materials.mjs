/** Read-only actual prepared selected denim maps and UV addressing. */
export const inspectPreparedRiderMaterials = () => {
  const rider = window.__render.debug.rider;
  const rows = [];
  rider.scene.traverse(mesh => {
    if (!mesh.isMesh) return;
    const materials = Array.isArray(mesh.material) ? mesh.material : [mesh.material];
    for (const material of materials) {
      if (material.name !== 'OriginalSelectedWholeJeansPBR4K') continue;
      const uv = mesh.geometry.getAttribute('uv');
      const maps = {};
      for (const key of ['map', 'roughnessMap', 'metalnessMap', 'normalMap']) {
        const texture = material[key], image = texture.image;
        const canvas = document.createElement('canvas');
        canvas.width = image.width; canvas.height = image.height;
        const context = canvas.getContext('2d', { willReadFrequently: true });
        context.drawImage(image, 0, 0);
        const pixels = context.getImageData(0, 0, image.width, image.height).data;
        const samples = [];
        for (let i = 0; i < uv.count; i++) {
          const u = uv.getX(i), v = uv.getY(i);
          const x = Math.min(image.width - 1, Math.max(0, Math.floor(u * image.width)));
          const y = Math.min(image.height - 1, Math.max(0, Math.floor(v * image.height)));
          samples.push(Array.from(pixels.subarray((y * image.width + x) * 4, (y * image.width + x) * 4 + 4)));
        }
        maps[key] = { width: image.width, height: image.height, flipY: texture.flipY,
          colorSpace: texture.colorSpace, channel: texture.channel, matrix: texture.matrix.toArray(),
          repeat: texture.repeat.toArray(), offset: texture.offset.toArray(),
          alphaZeroRows: samples.filter(p => p[3] === 0).length,
          medianRGB: [0, 1, 2].map(c => samples.map(p => p[c]).sort((a,b) => a-b)[Math.floor(samples.length/2)]),
          firstSamples: samples.slice(0, 8) };
      }
      rows.push({ mesh: mesh.name, material: material.name, uvCount: uv.count,
        roughness: material.roughness, metalness: material.metalness,
        color: material.color.toArray(), emissive: material.emissive.toArray(),
        normalMapType: material.normalMapType, normalScale: material.normalScale.toArray(), maps });
    }
  });
  return rows;
};
