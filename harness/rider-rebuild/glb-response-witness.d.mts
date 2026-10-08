import type { Response } from 'playwright';
interface ImmutableModelWitness { sha256: string; bytes: number }
export function witnessGlbResponse(response: Response, cache: Map<string, Promise<ImmutableModelWitness>>): Promise<ImmutableModelWitness & {
  url: string; status: number; browserContentLength: string | null; hashScope: string;
}>;
