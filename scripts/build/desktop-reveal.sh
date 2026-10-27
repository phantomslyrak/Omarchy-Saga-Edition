#!/usr/bin/env bash
# Build only. Historical helper installs its scanner exclusively under the component.
set -euo pipefail
root=$(cd -- "$(dirname -- "$0")/../.." && pwd)
exec python3 -B "$root/components/desktop-reveal/tools/build" "$@"
