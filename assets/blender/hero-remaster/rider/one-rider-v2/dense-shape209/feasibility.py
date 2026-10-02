#!/usr/bin/env python3
"""No Torch imports or allocations; count dense decoder storage and queries."""
import json
import math
from pathlib import Path

ROOT = Path('/Users/raynos/projects/games/rockhop')
OUT = ROOT / 'docs/evidence/hero-remaster/one-rider-v2/dense-shape209'


def counts(resolution, chunks=4096):
    points = (resolution + 1) ** 3
    return {'resolution': resolution, 'denseQueries': points,
            'chunkQueries': chunks, 'chunkCount': math.ceil(points / chunks),
            'float32CoordinateBytes': points * 3 * 4,
            'float32ScalarGridBytes': points * 4,
            'vanillaTransientCPUBytesEstimate': points * (3 * 4 + 3 * 4 + 3 * 4),
            'interpretation': 'Coordinate/grid payload only; excludes model, attention, tensors, allocator and process memory'}


def main():
    report = {'status': 'UNEXECUTED_CONDITIONAL_RECIPE',
              'torchImported': False, 'gpuJobs': 0, 'modelExecutions': 0,
              'unadmittedMatched380': counts(380), 'explicitDenseOnly256Proxy': counts(256),
              'timeEstimate': 'Not established: query count alone cannot predict MPS throughput.',
              'runtimeAdmission': 'Do not repeat Flash380: diagnostic207 observed 82.017GB anonymous memory. Dense-only256 is a separately registered new proxy; sample once, retain latents, restore ordinary attention and profile eight chunks before full admission. Forecast dense time with 1.5 safety factor below 80% of remaining 1800 seconds; require baseline-aware memory headroom.',
              'reportedDiagnostic207': {'observedAnonymousBytes': 82017000000,
                                        'preJumpAnonymousBytes': 56970000000,
                                        'baselineAnonymousBytes': 44520000000,
                                        'nativeNPZSHA256': '8c337ad381a5c498a3655764d391cd14137fa7aa05ed5d7f3b94c8385a07ac53',
                                        'verification': 'Parent-supplied receipt; not independently inspected in this recipe'},
              'memoryLimitBytes': 70000000000, 'batchSeconds': 1800}
    assert report['unadmittedMatched380']['denseQueries'] == 55306341
    assert report['unadmittedMatched380']['chunkCount'] == 13503
    assert report['explicitDenseOnly256Proxy']['denseQueries'] == 16974593
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'feasibility.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
