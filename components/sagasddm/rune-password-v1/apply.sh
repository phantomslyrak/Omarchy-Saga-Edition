#!/usr/bin/env bash
set -euo pipefail
base=$(cd -- "$(dirname -- "$0")" && pwd)
python3 "$base/update.py" apply
python3 "$base/update.py" check-rollback
