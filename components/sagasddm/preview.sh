#!/usr/bin/env bash
set -euo pipefail
base=$(cd -- "$(dirname -- "$0")" && pwd)
QT_QPA_PLATFORMTHEME= QT_QPA_PLATFORM=wayland QT_SCALE_FACTOR=1.25 QT_FORCE_STDERR_LOGGING=1 sddm-greeter-qt6 --test-mode --theme "$base/saga-sddm"
