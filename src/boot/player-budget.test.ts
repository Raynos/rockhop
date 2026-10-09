import { expect, it } from 'vitest';
import { playerBudget, PLAYER_JS_GZIP_CAP, SELECTED_RIDER_JS_GZIP_CAP } from './player-budget';
it('enforces both independent caps and reports the actual combined download', () => {
  expect(playerBudget(PLAYER_JS_GZIP_CAP, SELECTED_RIDER_JS_GZIP_CAP)).toEqual({
    coreBytes: PLAYER_JS_GZIP_CAP, selectedBytes: SELECTED_RIDER_JS_GZIP_CAP,
    combinedBytes: PLAYER_JS_GZIP_CAP + SELECTED_RIDER_JS_GZIP_CAP, pass: true,
  });
  expect(playerBudget(PLAYER_JS_GZIP_CAP + 1, 0).pass).toBe(false);
  expect(playerBudget(1, SELECTED_RIDER_JS_GZIP_CAP + 1).pass).toBe(false);
  expect(playerBudget(0, 0).pass).toBe(false);
});
