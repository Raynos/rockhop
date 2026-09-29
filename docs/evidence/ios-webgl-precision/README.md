# Safari null shader precision at renderer startup

The user's public iPhone screenshot is from `playrockhop.vercel.app` build `f9f7a05` and shows `getShaderPrecisionFormat(...HIGH_FLOAT).precision` throwing because Safari returned `null`. Three r186 dereferences the answer during `new WebGLRenderer` before the game can finish loading.

The fix obtains one WebGL2 context, installs a null-safe `getShaderPrecisionFormat` method on that context, and passes the same context to Three. Real precision results remain untouched. A missing result becomes precision `0`, so Three selects the next supported tier. If Safari forbids the method override, `lowp` avoids Three's unsafe probes. A genuinely lost or unavailable WebGL2 context still produces the existing startup error; no automatic context recovery is claimed.

Verification on the qualification branch: four focused unit cases pass, including a later probe turning null. Silent headless WebKit at 874×330 CSS pixels and DPR 3 completed loading and reached the menu with zero page errors in four cases: normal → highp; high-float null → mediump; all precision responses null → lowp; first highp response valid and the next null → mediump. Typecheck and lint pass. Physical iPhone Safari retest and production deployment verification remain required.
