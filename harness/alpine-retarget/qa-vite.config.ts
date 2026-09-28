/** Frozen, non-shipping QA bundle for played Alpine captures.
 *
 * The production build budget remains enforced by vite.config.ts. This copy
 * excludes only its budget plugin so an unrelated small bundle overage cannot
 * interrupt visual capture; the artifact is never deployed.
 */
import base from '../../vite.config';
import type { Plugin, UserConfig } from 'vite';

const config = base as UserConfig;
// This repository's base config declares a concrete synchronous Plugin array.
const plugins = config.plugins as Plugin[];

export default {
  ...config,
  plugins: plugins.filter((plugin) => plugin.name !== 'rockhop:bundle-budget'),
  build: { ...config.build, outDir: 'harness/out/alpine-qa-dist' },
} satisfies UserConfig;
