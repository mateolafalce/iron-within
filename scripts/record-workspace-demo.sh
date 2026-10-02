#!/bin/bash
# Record the desktop while visiting the first three workspaces, three seconds each.
# Puts the current workspace back when it finishes. Leaves the grade as it was,
# except it turns the grade on for the take if it was off.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="${1:-$ROOT/demo/cinematic-grade-workspaces.mp4}"
HOLD="${HOLD_SECONDS:-3}"
COUNT="${WORKSPACE_COUNT:-3}"
FPS="${FPS:-15}"
DISPLAY="${DISPLAY:-:0}"
export DISPLAY

if ! command -v gst-launch-1.0 >/dev/null 2>&1; then
    echo "gst-launch-1.0 is required" >&2
    exit 1
fi
if ! command -v wmctrl >/dev/null 2>&1; then
    echo "wmctrl is required" >&2
    exit 1
fi

mapfile -t desks < <(wmctrl -d | awk '{print $1}')
if ((${#desks[@]} < COUNT)); then
    echo "Need ${COUNT} workspaces, found ${#desks[@]}" >&2
    exit 1
fi

current="$(wmctrl -d | awk '/\*/ {print $1; exit}')"
if [[ -z "$current" ]]; then
    echo "No current workspace" >&2
    exit 1
fi

grade_was_on=1
if [[ -x "$ROOT/bin/cinematic-grade" ]]; then
    if ! "$ROOT/bin/cinematic-grade" status | grep -q '"active":true'; then
        grade_was_on=0
        "$ROOT/bin/cinematic-grade" on >/dev/null
    fi
fi

mkdir -p "$(dirname "$OUT")"
rm -f "$OUT"
log="$(mktemp /tmp/iron-within-record.XXXXXX.log)"
gst_pid=""
restored=0
grade_restored=0

stop_recorder() {
    if [[ -n "$gst_pid" ]] && kill -0 "$gst_pid" 2>/dev/null; then
        kill -INT "$gst_pid" 2>/dev/null || true
        wait "$gst_pid" 2>/dev/null || true
    fi
    gst_pid=""
}

restore_workspace() {
    local now=""
    wmctrl -s "$current" 2>/dev/null || true
    for _ in $(seq 1 20); do
        now="$(wmctrl -d | awk '/\*/ {print $1; exit}')"
        if [[ "$now" == "$current" ]]; then
            restored=1
            return 0
        fi
        sleep 0.1
    done
    wmctrl -s "$current" 2>/dev/null || true
    sleep 0.4
    now="$(wmctrl -d | awk '/\*/ {print $1; exit}')"
    if [[ "$now" == "$current" ]]; then
        restored=1
        return 0
    fi
    echo "Could not restore workspace ${current} (still ${now})" >&2
    return 1
}

restore_grade() {
    if [[ "$grade_restored" -eq 1 ]]; then
        return 0
    fi
    grade_restored=1
    if [[ "$grade_was_on" -eq 0 && -x "$ROOT/bin/cinematic-grade" ]]; then
        "$ROOT/bin/cinematic-grade" off >/dev/null || true
    fi
}

cleanup() {
    local status=$?
    trap - EXIT
    stop_recorder
    if [[ "$restored" -eq 0 ]]; then
        restore_workspace || true
    fi
    restore_grade
    if [[ "$status" -ne 0 ]]; then
        echo "Recording failed. Log: $log" >&2
        exit "$status"
    fi
    rm -f "$log"
}
trap cleanup EXIT

gst-launch-1.0 -e \
    ximagesrc display-name="$DISPLAY" use-damage=false show-pointer=true \
    ! videoconvert \
    ! videorate \
    ! "video/x-raw,format=I420,framerate=${FPS}/1" \
    ! x264enc tune=zerolatency speed-preset=ultrafast bitrate=8000 key-int-max="$((FPS * 2))" \
    ! h264parse \
    ! mp4mux faststart=true \
    ! filesink location="$OUT" \
    >"$log" 2>&1 &
gst_pid=$!

for _ in $(seq 1 50); do
    if ! kill -0 "$gst_pid" 2>/dev/null; then
        echo "Recorder exited before PLAYING" >&2
        cat "$log" >&2
        gst_pid=""
        exit 1
    fi
    if grep -q "PLAYING" "$log"; then
        break
    fi
    sleep 0.1
done

for ((n = 0; n < COUNT; n++)); do
    target="${desks[n]}"
    wmctrl -s "$target"
    echo "workspace ${target} for ${HOLD}s"
    sleep "$HOLD"
    now="$(wmctrl -d | awk '/\*/ {print $1; exit}')"
    if [[ "$now" != "$target" ]]; then
        echo "Workspace switch failed: wanted ${target}, still ${now}" >&2
        exit 1
    fi
done

stop_recorder

if [[ ! -s "$OUT" ]]; then
    echo "No video was written" >&2
    cat "$log" >&2
    exit 1
fi

if ! restore_workspace; then
    echo "Video is at ${OUT}, but the previous workspace was not restored" >&2
    exit 1
fi
restore_grade

echo "Wrote ${OUT}"
echo "Restored workspace ${current}"
