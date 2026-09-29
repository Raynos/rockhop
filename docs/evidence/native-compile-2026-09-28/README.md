# Both store shells compile from the same committed source

On 2026-09-28, `node scripts/store-build.mjs release --ios` and `node scripts/store-build.mjs release --android` each exported clean committed source `5102b6b14f74e5de8186f76b4fcd9a06063ee303` into the store web bundle. `store/build/SOURCE` named that SHA and `store/build/MODE` read `release`. The bundle build rejected automation hooks and copied the same web payload into both Capacitor shells.

- iOS: the unsigned **Release iPhone Simulator** app compiled at `store/build/ios-derived/Build/Products/Release-iphonesimulator/App.app` (54 MiB). This checks Swift/Capacitor compilation; it is not an iPhone archive or a signed TestFlight build.
- Android: `bundleRelease` produced the upload-key-signed `android/app/build/outputs/bundle/release/app-release.aab` (46 MiB). `jarsigner -verify` returned exit 0 and `jar verified`; its self-signed upload certificate warning does not establish Play acceptance. The AAB SHA-256 was `908c4038201d73d9bb6d32feb21d25d64da0600b6494434a17ca5aca344c1f19`.
- `node scripts/ip-audit.mjs --strict store/build/web ios android store/metadata` returned exit 0 with zero retired-name/franchise matches across 168 inspected files. This text scan does not resolve the separate source-rights question in `store/COMPLIANCE.md`.

The iOS `Info.plist` lists only landscape orientations, and Android requests `sensorLandscape`. No physical phone, install, signed iOS archive, continuous session, store upload or store review was exercised. This is a compile and payload check on a development candidate; Gate 4 and Gate 5 remain open.

## Current qualification-source rebuild

`node scripts/store-build.mjs release --ios --android` passed again from a clean export of committed `44002a6ba4b65a29efc8b600d8aca088ee2ed524` after the medal-clock, finish-label and harbor-review rounds. Both shells received one release web payload. Android produced a 46 MiB signed AAB (SHA-256 `061f4bae1e9708795d62740c719382cd025f18ce6be14d199b1615c33f484870`); `jarsigner -verify` returned `jar verified`, and `keytool` reported the existing upload certificate SHA-256 beginning `C3:61:7C:2E` and ending `1F:57`. `jarsigner -verify -strict` flags the expected self-signed upload certificate, so it is not used as a Play acceptance result. The unsigned iOS Release simulator app compiled at 54 MiB. `store/build/SOURCE` names the exact SHA, `MODE` is `release`, and the strict retired-name scan passed **0 hits across 168 files** in the store web payload, native shells and listing metadata. A signed iOS archive, Play upload, and real-device play remain open.

## After the clean street-rider export

`node scripts/store-build.mjs release --ios --android` passed from a clean export of committed `42e401f3cd8603611414cd64bc3512c1352bd529`; `store/build/SOURCE` and `MODE` read that SHA and `release`. The 45 MiB Android AAB SHA-256 is `81c4ff5d00da13d4bf3590b725b5b2d2e385bf74bc17341e432a10ab7731b22e`, and `jarsigner -verify` exited 0. The unsigned iOS Release simulator app compiled at 52 MiB. iOS lists only LandscapeRight/LandscapeLeft; Android requests `sensorLandscape`.

The strict `node scripts/ip-audit.mjs --strict store/build/web ios android store/metadata` scan passed **0 hits across 168 files**. It now also checks GLB JSON for the disputed facial-hair source names, while the [runtime rights evidence](../hero-art/delivery/provenance/beard-rights-audit/README.md) records the specific omission. This check does not settle rights for every other third-party asset. A signed iOS archive, physical iPhone/Android runs, store uploads and review are still open.

## After the finish-goal and map-review rounds

`node scripts/store-build.mjs release --ios --android` passed from a clean export of committed `904bf473e551d220a8c8f0e01eb747062853381d`; `store/build/SOURCE` reads that exact SHA. The 45 MiB Android AAB SHA-256 is `468e5244e39739d0183d3289275fcd282feb46406d20a1cc890c41448e0387b3`, and `jarsigner -verify` returned `jar verified` (the upload certificate is self-signed). The unsigned iOS Release simulator app compiled at 52 MiB with only LandscapeRight/LandscapeLeft in `Info.plist`. The strict payload and metadata audit passed **0 hits across 168 files**, including the clean rider checks. This rebuild includes the finish Pro-goal heading; the selected C island is still review-only and absent from the store bundle. Physical device play, a signed iOS archive, store testing and final rights review remain open.
