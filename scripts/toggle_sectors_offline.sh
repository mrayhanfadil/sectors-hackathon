#!/usr/bin/env bash
# Toggle SECTORS_OFFLINE=1 in /home/fadil/.config/sectors-be/env and bounce the
# api container. With SECTORS_OFFLINE=1:
#   * AMMN falls back to output/cache/ammn_fill/<...>.json (AMMN-FILLD freeze,
#     0-credit cache hit when present);
#   * every other ticker raises sectors_offline_mode in the collector and the
#     run aborts loud (the same loud-empty contract as keyless).
# Use this to pause credit burns without uninstalling the Sectors key.

set -euo pipefail
ENV_FILE="${ENV_FILE:-/home/fadil/.config/sectors-be/env}"
ACTION="${1:-lock}"
if [ ! -f "$ENV_FILE" ]; then
  echo "ENV_FILE=$ENV_FILE does not exist - aborting" >&2
  exit 1
fi
case "$ACTION" in
  lock|1)
    if grep -qE '^SECTORS_OFFLINE=' "$ENV_FILE"; then
      sed -i 's/^SECTORS_OFFLINE=.*/SECTORS_OFFLINE=1/' "$ENV_FILE"
    else
      printf '\nSECTORS_OFFLINE=1\n' >> "$ENV_FILE"
    fi
    chmod 600 "$ENV_FILE"
    echo "locked: SECTORS_OFFLINE=1 set in $ENV_FILE"
    ;;
  unlock|0)
    sed -i '/^SECTORS_OFFLINE=/d' "$ENV_FILE"
    echo "unlocked: SECTORS_OFFLINE line removed from $ENV_FILE"
    ;;
  *)
    echo "usage: $0 [lock|unlock]" >&2
    exit 2
    ;;
esac
