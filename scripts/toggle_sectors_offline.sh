#!/usr/bin/env bash
# Toggle Sectors discipline modes in /home/fadil/.config/sectors-be/env and
# bounce the api container. Three modes (any one of them can be set, or none):
#
#   SECTORS_OFFLINE=1      - refuse all upstream calls; only serve from freeze
#                            files in output/cache/ammn_fill/ (AMMN only) or
#                            fail loud. The collector raises sectors_offline_mode.
#
#   SECTORS_CACHE_ONLY=1   - prefer cache; on miss, refuse upstream (599) at
#                            server/sectors._get() AND return
#                            {source: sectors_cache_only} at every ADK tool.
#                            Use this when the key is set but you want to burn
#                            zero credits unless the cache is explicitly warmed.
#
#   SECTORS_STALE_OK=0     - strict TTL expiry (rows past expires_at are
#                            misses). Default 1 keeps stale reads free.
#
# Usage:
#   bash scripts/toggle_sectors_offline.sh lock      # SECTORS_OFFLINE=1
#   bash scripts/toggle_sectors_offline.sh cache     # SECTORS_CACHE_ONLY=1
#   bash scripts/toggle_sectors_offline.sh unlock    # all off, key still in env
#
# After any change, bounce the api container so the new env is in effect:
#
#   bash /tmp/restart-api.sh

set -e

ENV_FILE="$HOME/.config/sectors-be/env"
case "${1:-}" in
    lock)
        MODE="SECTORS_OFFLINE"
        VAL="1"
        ;;
    cache)
        MODE="SECTORS_CACHE_ONLY"
        VAL="1"
        ;;
    unlock)
        MODE="__CLEAR__"
        VAL=""
        ;;
    *)
        echo "Usage: $0 {lock|cache|unlock}" >&2
        exit 2
        ;;
esac

if [[ "$MODE" == "__CLEAR__" ]]; then
    # Strip both flags (and the comment line we add) from env, leave key intact
    if [[ -f "$ENV_FILE" ]]; then
        sed -i '/^# SECTORS credit-discipline toggle/d; /^SECTORS_OFFLINE=/d; /^SECTORS_CACHE_ONLY=/d; /^SECTORS_STALE_OK=/d' "$ENV_FILE"
    fi
    echo "[toggle] cleared credit-discipline flags (key preserved)"
else
    if [[ ! -f "$ENV_FILE" ]]; then
        echo "[toggle] env file not found: $ENV_FILE" >&2
        exit 1
    fi
    # Idempotent: drop any prior lines, then append fresh ones
    sed -i '/^# SECTORS credit-discipline toggle/d; /^SECTORS_OFFLINE=/d; /^SECTORS_CACHE_ONLY=/d; /^SECTORS_STALE_OK=/d' "$ENV_FILE"
    {
        echo "# SECTORS credit-discipline toggle (managed by scripts/toggle_sectors_offline.sh)"
        echo "SECTORS_STALE_OK=1"
        echo "${MODE}=${VAL}"
    } >> "$ENV_FILE"
    echo "[toggle] set $MODE=$VAL in $ENV_FILE"
fi

# Always restart the api container so the new env is read by the running process
if [[ -f /tmp/restart-api.sh ]]; then
    bash /tmp/restart-api.sh
else
    echo "[toggle] /tmp/restart-api.sh missing - bounce api container manually:" >&2
    echo "         cd ~/projects/sectors-hackathon && make up" >&2
    exit 1
fi
