import { defineConfig } from 'vitest/config';
export default defineConfig({ test: { include: ['assets/blender/course-kits/coast-harbor/*.test.ts'], environment: 'node' } });
