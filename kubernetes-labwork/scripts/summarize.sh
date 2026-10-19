#!/usr/bin/env bash
# Purpose: summarise a monitor log — totals, failures, timestamp range, responses per version
# Usage: ./scripts/summarise.sh <monitor.log>
set -euo pipefail
LOG="${1:?usage: summarise.sh <log>}"
total=$(grep -c . "$LOG" || true)
failed=$(grep -c ' FAIL ' "$LOG" || true)
first=$(head -n1 "$LOG" | awk '{print $1}')
last=$(tail -n1 "$LOG" | awk '{print $1}')
echo "total requests: $total"
echo "failed requests: $failed"
echo "first timestamp: $first"
echo "last  timestamp: $last"
echo "responses per version:"
grep ' OK ' "$LOG" | grep -o '"version": *"[^"]*"' | sed 's/.*"\([^"]*\)"$/\1/' | sort | uniq -c