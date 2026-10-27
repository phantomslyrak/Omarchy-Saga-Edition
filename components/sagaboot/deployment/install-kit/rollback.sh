#!/usr/bin/env bash
# Live USB rollback. Generated hashes below are tied to this installation kit.
set -euo pipefail
ORIGINAL_UKI='85a795c69fefbdb66b1a1992d528d7c015263e73f245173639cc5bef649bacb9'
ORIGINAL_MENU='c10c584864048b4a8b5711c29d551a07e7008c1bb607ef3dafb8f31704371c99'
INSTALLED_MENU='bbd542a54797196a39abd67eff63d60d89fc9c09e70a8956804b1dca5200bbd7'
MANIFEST_HASH='392e6fdacc2ce87089c7b8ee2850dde14afd5918d38fe4b636b17c3ca9254910'
hash_file() {
    local value
    [[ -f "$1" && ! -L "$1" ]] || return 1
    value=$(sha256sum -- "$1")
    printf '%s\n' "${value%% *}"
}
verify_file() {
    [[ $(hash_file "$1") == "$2" ]] || { printf 'STOP: checksum mismatch: %s\n' "$1" >&2; return 1; }
}
restore_file() {
    local source=$1 target=$2 expected=$3 temporary="${2}.sagaboot-rollback.tmp"
    [[ ! -e "$temporary" && ! -L "$target" ]] || return 1
    cp -- "$source" "$temporary"
    verify_file "$temporary" "$expected"
    mv -T -- "$temporary" "$target"
    verify_file "$target" "$expected"
    sync
}
rollback_files() {
    local esp=$1 restore=${2:-no} rec current need_original=no rel expected
    rec="$esp/EFI/SagaBoot-v1.0-recovery"
    verify_file "$rec/original.efi" "$ORIGINAL_UKI"
    verify_file "$rec/limine.conf.original" "$ORIGINAL_MENU"
    verify_file "$rec/deployment.json" "$MANIFEST_HASH"
    current=$(hash_file "$esp/limine.conf" || true)
    [[ -z "$current" || "$current" == "$ORIGINAL_MENU" || "$current" == "$INSTALLED_MENU" ]] || {
        echo 'STOP: Limine config changed; manual merge required.' >&2; return 1;
    }
    if [[ $(hash_file "$esp/EFI/Linux/omarchy_linux-omarchy.efi" || true) != "$ORIGINAL_UKI" ]]; then
        need_original=yes
        [[ "$restore" == yes ]] || { echo 'STOP: inspect original UKI; explicit --restore-original required.' >&2; return 1; }
    fi
    # Verify every remaining installed image before performing any write.
    while IFS=' ' read -r expected rel; do
        if [[ -e "$esp/$rel" ]]; then verify_file "$esp/$rel" "$expected"; fi
    done <<'SAGABOOT_HASHES'
7ff4e72881f6023f14d196f1e2b01fa5907414a00b0fdb50f17f4bee275895bd EFI/Linux/omarchy-sagaboot-console.efi
347993bd2b9eea86fc6ca05fd4af5efb120d715997dc62f8ff6952221999c581 EFI/Linux/omarchy-sagaboot-v1.efi
0812f2425a531264416005554b6e0169a5a4222403c09e0546e5027510bb5d66 EFI/Linux/omarchy-sagaboot-v1.efi.extra.d/sagaboot-v1.addon.efi
SAGABOOT_HASHES
    if [[ "$need_original" == yes ]]; then
        restore_file "$rec/original.efi" "$esp/EFI/Linux/omarchy_linux-omarchy.efi" "$ORIGINAL_UKI"
    fi
    if [[ "$current" != "$ORIGINAL_MENU" ]]; then
        restore_file "$rec/limine.conf.original" "$esp/limine.conf" "$ORIGINAL_MENU"
    fi
    verify_file "$esp/EFI/Linux/omarchy_linux-omarchy.efi" "$ORIGINAL_UKI"
    verify_file "$esp/limine.conf" "$ORIGINAL_MENU"
    sync
    rm -f -- "$esp/EFI/Linux/omarchy-sagaboot-v1.efi.extra.d/sagaboot-v1.addon.efi"
    rm -f -- "$esp/EFI/Linux/omarchy-sagaboot-v1.efi" "$esp/EFI/Linux/omarchy-sagaboot-console.efi"
    rm -- "$rec/original.efi" "$rec/limine.conf.original" "$rec/deployment.json" "$rec/rollback.sh"
    rmdir -- "$esp/EFI/Linux/omarchy-sagaboot-v1.efi.extra.d" "$rec"
    sync
    echo 'Original UKI/menu verified. SagaBoot additions removed. No reboot performed.'
}
main() {
    [[ $# -ge 2 && $# -le 3 && $2 == --apply ]] || { echo 'Usage: bash rollback.sh /mounted/linux-esp --apply [--restore-original]' >&2; return 1; }
    [[ $(id -u) == 0 ]] || { echo 'Root in Live USB required' >&2; return 1; }
    local esp source filesystem options restore=no
    esp=$(readlink -f -- "$1")
    source=$(findmnt -rn -M "$esp" -o SOURCE)
    filesystem=$(findmnt -rn -M "$esp" -o FSTYPE)
    options=$(findmnt -rn -M "$esp" -o OPTIONS)
    [[ "$source" == /dev/nvme0n1p3 && "$filesystem" == vfat && ",$options," == *,rw,* ]] || {
        echo 'STOP: only Linux ESP nvme0n1p3 mounted read-write allowed' >&2; return 1;
    }
    if [[ $# == 3 ]]; then [[ $3 == --restore-original ]] || return 1; restore=yes; fi
    rollback_files "$esp" "$restore"
}
if [[ ${BASH_SOURCE[0]} == "$0" ]]; then main "$@"; fi
