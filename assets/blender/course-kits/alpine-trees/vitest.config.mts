import { defineConfig } from 'vitest/config';

export default defineConfig({ test: { include: ['assets/blender/course-kits/alpine-trees/integration.test.ts'], environment: 'node' } });
