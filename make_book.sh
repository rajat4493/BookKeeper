#!/usr/bin/env bash
set -euo pipefail

usage() { echo "Usage: $0 --config book.yml [--pack name]"; exit 1; }
CONFIG=""
PACK=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --config) CONFIG="$2"; shift 2;;
    --pack) PACK="$2"; shift 2;;
    *) usage;;
  esac
done

[[ -z "$CONFIG" ]] && usage

if [ -f ".venv/bin/activate" ]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi

python3 main.py --config "$CONFIG" ${PACK:+--pack "$PACK"}
