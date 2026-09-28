#!/usr/bin/env bash
set -euo pipefail
export AGENT_BROWSER_SESSION=finish-remaster-codex

# Silent headless review: 852×393 result states and each one-tap route.
agent-browser set viewport 852 393
agent-browser open http://127.0.0.1:8743/
agent-browser record start docs/evidence/finish-remaster/interaction.mp4 --fps 20
agent-browser wait 900
agent-browser click 'button[data-scenario="best"]'
agent-browser wait 900
agent-browser click 'button[data-scenario="medal"]'
agent-browser wait 900
agent-browser click 'button[data-scenario="same"]'
agent-browser wait 900
agent-browser click 'button[data-action="retry"]'
agent-browser wait 900
agent-browser click '#back'
agent-browser click 'button[data-action="next"]'
agent-browser wait 900
agent-browser click '#back'
agent-browser click 'button[data-action="map"]'
agent-browser wait 900
agent-browser click '#back'
agent-browser click 'button[data-action="replay"]'
agent-browser wait 1100
agent-browser record stop
