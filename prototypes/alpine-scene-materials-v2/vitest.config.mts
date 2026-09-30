import { defineConfig } from 'vitest/config';
export default defineConfig({ test: { include: ['prototypes/alpine-scene-materials-v2/ownership.test.ts'], environment:'node' } });
