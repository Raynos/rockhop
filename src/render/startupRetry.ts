import { WebGL2ContextUnavailableError } from './index';

/** Safari can temporarily refuse WebGL2 while its previous page's GPU resources retire. */
const RETRY_DELAYS_MS = [250, 750, 1500, 3000] as const;

export async function retryWebGL2Startup<T>(create: (attempt: number) => T, pause: (ms: number) => Promise<void> = (ms) => new Promise(resolve => setTimeout(resolve, ms))): Promise<T> {
  for (let attempt = 0; ; attempt++) {
    try {
      return create(attempt);
    } catch (error) {
      if (!(error instanceof WebGL2ContextUnavailableError) || attempt >= RETRY_DELAYS_MS.length) throw error;
      console.warn(`[rockhop] WebGL2 startup ${error.reason}; retry ${attempt + 1}/${RETRY_DELAYS_MS.length} in ${RETRY_DELAYS_MS[attempt]} ms`);
      await pause(RETRY_DELAYS_MS[attempt]!);
    }
  }
}
