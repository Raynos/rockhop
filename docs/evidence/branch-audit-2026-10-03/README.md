# Branch audit — 2026-10-03

After fetching origin, all seven non-main local branches and all fetched
remote branches are represented in main. No outstanding branch merge remains.

Four local branches were already ancestors. astra-merge, blender-work and
main-now pointed to history before the approved oversized-video purge.
Their recorded rewritten tips are independently verified main ancestors;
the sole tree difference is removal of the 141,657,181-byte trailer MP4.

The three branch pointers now name their verified rewritten counterparts.
Original tips remain in local refs/archive/pre-purge/ for provenance.
An atomic ref transaction checked the original tips and main before changing
pointers. No unrelated-history merge restored the purged video.

Validation: every local/fetched remote tip is a main ancestor; main HEAD
and its tree were unchanged by ref alignment. Full pins are in audit.json.
Native research adaptations remain queued under their existing plan; this
ancestry audit does not claim those older app changes are enabled or tested.
