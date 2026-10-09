/** Node-only build helper: hash and retain the exact bytes emitted or served for each model URL. */
import { createHash } from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import type { Plugin } from 'vite';

export interface ModelAsset {
  logical: string;
  url: string;
  bytes: Buffer;
  sha256: string;
}

const sha = (bytes: Buffer | string): string => createHash('sha256').update(bytes).digest('hex');

export function readModelCatalog(publicDir: string, required: readonly string[] = []): ModelAsset[] {
  const sources = new Map<string, Buffer>();
  const walk = (directory: string, prefix: string): void => {
    for (const entry of fs.readdirSync(directory, { withFileTypes: true })) {
      const logical = `${prefix}/${entry.name}`;
      if (entry.isDirectory()) walk(path.join(directory, entry.name), logical);
      else if (entry.name.endsWith('.glb')) sources.set(logical, fs.readFileSync(path.join(directory, entry.name)));
    }
  };
  const directory = path.join(publicDir, 'models');
  if (fs.existsSync(directory)) walk(directory, 'models');
  for (const logical of required) if (!sources.has(logical)) throw new Error(`model catalog: missing required asset ${logical}`);
  const digests = new Map([...sources].map(([logical, bytes]) => [logical, sha(bytes)]));
  return [...sources.keys()].sort().map(logical => {
    const full = logical.replace(/-lod\.glb$/, '.glb');
    const lod = full.replace(/\.glb$/, '-lod.glb');
    if (!sources.has(full) || !sources.has(lod)) throw new Error(`model catalog: full/LOD pair is incomplete: ${full}, ${lod}`);
    const pairHash = sha(`${full}\n${digests.get(full)}\n${lod}\n${digests.get(lod)}`).slice(0, 16);
    const digest = digests.get(logical)!;
    const folder = path.posix.dirname(logical);
    const name = path.posix.basename(logical, '.glb');
    return { logical, url: `${folder}/${pairHash}/${name}-${digest.slice(0, 16)}.glb`, bytes: sources.get(logical)!, sha256: digest };
  });
}

/** External course maps receive byte snapshots just like their model pair. */
export function readModelResources(publicDir: string): ModelAsset[] {
  const assets: ModelAsset[] = [];
  const walk = (directory: string, prefix: string): void => {
    for (const entry of fs.readdirSync(directory, { withFileTypes: true })) {
      const logical = `${prefix}/${entry.name}`;
      if (entry.isDirectory()) walk(path.join(directory, entry.name), logical);
      else if (/\.(webp|png|jpe?g|avif|ktx2)$/.test(entry.name)) {
        const bytes = fs.readFileSync(path.join(directory, entry.name));
        const digest = sha(bytes), ext = path.posix.extname(logical);
        const name = path.posix.basename(logical, ext), folder = path.posix.dirname(logical);
        assets.push({ logical, url: `${folder}/${digest.slice(0, 16)}/${name}-${digest.slice(0, 16)}${ext}`, bytes, sha256: digest });
      }
    }
  };
  const directory = path.join(publicDir, 'models');
  if (fs.existsSync(directory)) walk(directory, 'models');
  return assets.sort((a, b) => a.logical.localeCompare(b.logical));
}

export function writeModelCatalog(root: string, assets: readonly ModelAsset[], resources: readonly ModelAsset[] = []): void {
  const values = Object.fromEntries(assets.map(asset => [asset.logical, { url: asset.url, bytes: asset.bytes.length }]));
  const source = '// Generated from public/models by trials:model-assets. Do not edit.\n'
    + '// URLs identify the snapshotted full/LOD pair and each file\'s actual bytes.\n'
    + `export const MODEL_ASSETS = ${JSON.stringify(values, null, 2)} as const;\n`
    + '// Full SHA256 receipts stay in model-catalog.json; runtime resolves URLs and download sizes only.\n'
    + `export const MODEL_RESOURCES = ${JSON.stringify(Object.fromEntries(resources.map(a => [a.logical, { url: a.url, bytes: a.bytes.length }])), null, 2)} as const;\n`;
  const output = path.join(root, 'src', 'render', 'hero', 'models.generated.ts');
  if (!fs.existsSync(output) || fs.readFileSync(output, 'utf8') !== source) fs.writeFileSync(output, source);
}

/** Catalog refresh is atomic at the JavaScript level: a request gets one complete byte snapshot. */
export function modelAssetsPlugin(required: readonly string[], onCatalog?: (assets: readonly ModelAsset[], root: string) => void): Plugin {
  let root = process.cwd();
  let assets: ModelAsset[] = [];
  let resources: ModelAsset[] = [];
  const aliases = new Map<string, ModelAsset>();
  const refresh = (): void => {
    const next = readModelCatalog(path.join(root, 'public'), required);
    resources = readModelResources(path.join(root, 'public'));
    writeModelCatalog(root, next, resources);
    assets = next;
    // Retain old dev snapshots while modules referring to their URLs remain in flight.
    for (const asset of [...next, ...resources]) aliases.set(`/${asset.url}`, asset);
    onCatalog?.(next, root);
  };
  return {
    name: 'trials:model-assets',
    enforce: 'pre',
    configResolved(config) { root = config.root; refresh(); },
    buildStart() {
      // Fail rather than compile a URL for bytes modified after config resolution.
      const current = [...readModelCatalog(path.join(root, 'public'), required), ...readModelResources(path.join(root, 'public'))];
      if (JSON.stringify(current.map(asset => [asset.logical, asset.sha256])) !== JSON.stringify([...assets, ...resources].map(asset => [asset.logical, asset.sha256]))) {
        throw new Error('model catalog: assets changed during build startup; restart the build');
      }
      for (const asset of [...assets, ...resources]) this.addWatchFile(path.join(root, 'public', asset.logical));
    },
    generateBundle() {
      for (const asset of [...assets, ...resources]) this.emitFile({ type: 'asset', fileName: asset.url, source: asset.bytes });
      const models: { logical: string; url: string; bytes: number; sha256: string; optional?: boolean }[] = assets.map(asset => ({ logical: asset.logical, url: asset.url, bytes: asset.bytes.length, sha256: asset.sha256 }));
      const selectedPath = path.join(root, 'public/rider-remaster-source.json');
      if (fs.existsSync(selectedPath)) {
        const selected = JSON.parse(fs.readFileSync(selectedPath, 'utf8')) as { url: string; bytes: number; sha256: string };
        if (!/^https:\/\/[^/]+\.public\.blob\.vercel-storage\.com\//.test(selected.url) || !/^[a-f0-9]{64}$/.test(selected.sha256) || selected.bytes <= 0) throw new Error('Invalid optional rider asset');
        for (const suffix of ['', '-lod']) models.push({ logical: `models/rider-street-remastered${suffix}.glb`, ...selected, optional: false });
      }
      this.emitFile({
        type: 'asset', fileName: 'model-catalog.json',
        source: JSON.stringify({ models, resources: resources.map(asset => ({ logical: asset.logical, url: asset.url, bytes: asset.bytes.length, sha256: asset.sha256 })) }, null, 2) + '\n',
      });
    },
    configureServer(server) {
      const update = (file: string): void => {
        const modelRoot = path.join(root, 'public', 'models') + path.sep;
        if (!file.startsWith(modelRoot) || !/\.(glb|webp|png|jpe?g|avif|ktx2)$/.test(file)) return;
        try {
          refresh();
          server.ws.send({ type: 'full-reload' });
        } catch (error) {
          server.config.logger.error(String(error));
          server.ws.send({ type: 'error', err: { message: String(error), stack: '' } });
        }
      };
      server.watcher.on('add', update).on('change', update).on('unlink', update);
      server.httpServer?.once('close', () => {
        server.watcher.off('add', update).off('change', update).off('unlink', update);
      });
      server.middlewares.use((req, res, next) => {
        const pathname = new URL(req.url ?? '/', 'http://localhost').pathname;
        const asset = aliases.get(pathname);
        if (!asset) {
          if (/^\/models\/(?:[\w-]+\/)*[a-f0-9]{16}\/[\w.-]+-[a-f0-9]{16}\.(?:glb|webp|png|jpe?g|avif|ktx2)$/.test(pathname)) {
            res.statusCode = 404;
            res.end('Unknown model byte snapshot');
            return;
          }
          return next();
        }
        const ext = path.posix.extname(asset.logical);
        const mime: Record<string, string> = { '.glb': 'model/gltf-binary', '.webp': 'image/webp', '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.avif': 'image/avif', '.ktx2': 'image/ktx2' };
        res.setHeader('Content-Type', mime[ext] ?? 'application/octet-stream');
        res.setHeader('Content-Length', asset.bytes.length);
        res.setHeader('Cache-Control', 'public, max-age=31536000, immutable');
        res.end(req.method === 'HEAD' ? undefined : asset.bytes);
      });
    },
  };
}
