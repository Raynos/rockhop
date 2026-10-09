/** Optional selected-rider code is measured separately from the original player. */
export const PLAYER_JS_GZIP_CAP = 701 * 1024;
export const SELECTED_RIDER_JS_GZIP_CAP = 24 * 1024;
export const SELECTED_RIDER_CHUNK = /^assets\/rider-selected-[\w-]+\.js$/;
export function playerBudget(coreBytes: number, selectedBytes: number): { coreBytes: number; selectedBytes: number; combinedBytes: number; pass: boolean } {
  return { coreBytes, selectedBytes, combinedBytes: coreBytes + selectedBytes,
    pass: coreBytes > 0 && coreBytes <= PLAYER_JS_GZIP_CAP && selectedBytes >= 0 && selectedBytes <= SELECTED_RIDER_JS_GZIP_CAP };
}
