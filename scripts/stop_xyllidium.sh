#!/usr/bin/env bash
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
for n in bridge engine scope; do
  if [ -f "$ROOT/logs/$n.pid" ]; then
    kill "$(cat "$ROOT/logs/$n.pid")" 2>/dev/null || true
    rm -f "$ROOT/logs/$n.pid"
    echo "stopped $n"
  fi
done
