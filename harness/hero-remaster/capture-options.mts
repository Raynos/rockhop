/** Remove private named options before interpreting the existing positional capture CLI. */
export function captureOptions(args: readonly string[]): { positional: string[]; surfaceMap: string | null } {
  const positional: string[] = [];
  let surfaceMap: string | null = null;
  for (let i = 0; i < args.length; i++) {
    const arg = args[i]!;
    if (arg !== '--surface-map' && !arg.startsWith('--surface-map=')) { positional.push(arg); continue; }
    if (surfaceMap !== null) throw new Error('duplicate --surface-map');
    const value = arg === '--surface-map' ? args[++i] : arg.slice('--surface-map='.length);
    if (!value?.trim() || value.startsWith('--')) throw new Error('--surface-map requires a file path');
    surfaceMap = value;
  }
  return { positional, surfaceMap };
}
