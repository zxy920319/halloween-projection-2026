#!/usr/bin/env bash
set -u

section() { printf '\n===== %s =====\n' "$1"; }
run_readonly() {
    printf '\n$'
    printf ' %q' "$@"
    printf '\n'
    "$@" 2>&1 || printf '[probe note] command exited with status %s\n' "$?"
}

section "Operating system"
run_readonly uname -a
run_readonly uname -m
if [ -r /etc/os-release ]; then
    run_readonly cat /etc/os-release
else
    echo "[probe note] /etc/os-release is unavailable"
fi

section "USB"
if command -v lsusb >/dev/null 2>&1; then
    run_readonly lsusb
    run_readonly lsusb -t
else
    echo "[probe note] lsusb is unavailable; install usbutils only with human approval"
fi

section "Video devices and formats"
shopt -s nullglob
devices=(/dev/video*)
if ((${#devices[@]})); then
    run_readonly ls -lah "${devices[@]}"
else
    echo "[probe note] no /dev/video* nodes found"
fi
if command -v v4l2-ctl >/dev/null 2>&1; then
    run_readonly v4l2-ctl --list-devices
    if ((${#devices[@]})); then
        for dev in "${devices[@]}"; do run_readonly v4l2-ctl -d "$dev" --list-formats-ext; done
    fi
else
    echo "[probe note] v4l2-ctl unavailable; v4l-utils may be installed manually after approval"
fi

section "Python"
if command -v python3 >/dev/null 2>&1; then run_readonly python3 --version; else echo "[probe note] python3 unavailable"; fi

section "Orbbec/OpenNI library hints"
if command -v ldconfig >/dev/null 2>&1; then
    ldconfig -p 2>/dev/null | grep -Ei 'openni|orbbec' || echo "[probe note] no matching libraries in ldconfig cache"
else
    echo "[probe note] ldconfig unavailable"
fi
if command -v file >/dev/null 2>&1; then
    for root in /usr/lib /usr/local/lib /opt; do
        [ -d "$root" ] || continue
        find "$root" -type f \( -name 'libOpenNI2.so*' -o -iname '*orbbec*.so*' \) -print 2>/dev/null |
        while IFS= read -r library; do run_readonly file "$library"; done
    done
else
    echo "[probe note] file utility unavailable; library architecture cannot be inspected"
fi

section "Probe boundary"
echo "Read-only inspection only. No packages installed, drivers changed, SDK loaded, or camera stream started."
