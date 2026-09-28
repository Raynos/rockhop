import base from '../../../../vite.config.ts';

// The parent can edit other campaign files in this shared checkout while this
// played map capture runs. Disable hot reload so a track edit cannot reset the
// camera halfway through a recorded orbit.
export default {
  ...base,
  server: { ...base.server, hmr: false, port: 5184, strictPort: true },
};
