# Gate33 software-backend failure

The completed retry used the portable default SwiftShader backend instead of the explicit Metal configuration of passed gate32. Preserve the actual failure: 8/11 checks pass, with boot readiness312.086ms, first synced frame6464.845ms and restart synced-frameP95630.365ms failing. Clear, byte-identical finish/replay, crash and one-tick restart pass. Product fingerprint remains fd8fe7c2.

The next invocation explicitly requests Metal, whose launcher probes the real WebGL2 renderer and rejects software fallback. No test limit, product source or resource bound changes. This failure is not a passed player gate or a rider result.
