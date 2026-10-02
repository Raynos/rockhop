# Hosted setup attempt01

The existing16event controls pass at390/1200px. The separate new-clip
checker then times out at page.goto waiting for global networkidle. A large
video library can retain metadata/range requests; this is not a decoded clip
failure. Preserve events-check.json and failed process.json. The new checker
uses DOM readiness then exact complete media hash and actual playback to end.
Only that failed new-clip stage retries in hosted-matched-retry02; source,
site version, videos and earlier passed event checks remain unchanged.
