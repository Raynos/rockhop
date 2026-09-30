/** Inspection supersamples desktop edges while bounding Garage targets to 2560 × 1440. */
export function garagePixelRatio(displayDpr: number, cssWidth: number, cssHeight: number): number {
  return Math.min(Math.max(displayDpr, 1.5), 2, 2560 / Math.max(1, cssWidth), 1440 / Math.max(1, cssHeight));
}
