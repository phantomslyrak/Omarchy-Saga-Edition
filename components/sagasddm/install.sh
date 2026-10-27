#!/usr/bin/env bash
set -euo pipefail
[[ $EUID == 0 ]] || { echo 'Run from the host terminal with sudo.' >&2; exit 1; }
[[ ${1:-} == --with-system-launcher && $# == 1 ]] || {
    echo 'Required explicit option: --with-system-launcher (no ACL changes).' >&2
    exit 2
}
base=$(cd -- "$(dirname -- "$0")" && pwd)
exec /usr/bin/python3 "$base/tools/install-system.py" "$base"
