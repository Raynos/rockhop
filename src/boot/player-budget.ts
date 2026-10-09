/** Selected-rider code is measured separately from the original player. */
export const PLAYER_JS_GZIP_CAP = 701 * 1024;
export const SELECTED_RIDER_JS_GZIP_CAP = 24 * 1024;
export const SELECTED_RIDER_CHUNK = /^assets\/rider-selected-[\w-]+\.js$/;
/** Dedicated standard texture decoder allowance; original game/rig caps stay fixed. */
export const TEXTURE_CODEC_JS_GZIP_CAP = 48 * 1024;
export const TEXTURE_CODEC_CHUNK = /^assets\/(rider-textures|basis_transcoder)-[\w-]+\.js$/;
export function playerBudget(coreBytes: number, selectedBytes: number, textureCodecBytes = 0): { coreBytes: number; selectedBytes: number; combinedBytes: number; pass: boolean } {
  return { coreBytes, selectedBytes, combinedBytes: coreBytes + selectedBytes + textureCodecBytes,
    pass: coreBytes > 0 && coreBytes <= PLAYER_JS_GZIP_CAP && selectedBytes >= 0 && selectedBytes <= SELECTED_RIDER_JS_GZIP_CAP && textureCodecBytes >= 0 && textureCodecBytes <= TEXTURE_CODEC_JS_GZIP_CAP };
}
