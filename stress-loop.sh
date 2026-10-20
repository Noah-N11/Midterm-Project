#!/bin/bash

set -u

LOG_FILE="/var/log/stress-loop.log"
REST_DURATION=15

log() {
    echo "$(date '+%F %T') - $1" >> "$LOG_FILE"
}

send_stress_event() {
    local event="$1"
    local fifo="/run/unix-monitor/stress-events.fifo"

    if [ -p "$fifo" ]; then
        timeout 1s bash -c 'printf "%s\n" "$1" > "$2"' \
            _ "$event" "$fifo" || true
    fi
}

run_test() {
    local category="$1"
    local duration="$2"
    shift 2

    log "Starting ${category} stress test for ${duration}s"
    send_stress_event "$category"

    stress-ng "$@" --timeout "${duration}s" \
        --metrics-brief >> "$LOG_FILE" 2>&1
    local result=$?

    log "Finished ${category} stress test (exit code: ${result})"
    send_stress_event "IDLE"

    sleep "$REST_DURATION"
    systemd-notify WATCHDOG=1
}

log "Stress loop started"

systemd-notify --ready --status="Stress loop running"

while true; do
    run_test "CPU" 30 --cpu 2 --cpu-load 80
    run_test "Memory"  20 --vm 1 --vm-bytes 25% --vm-keep
    run_test "Disk I/O" 15 --io 2
    run_test "Filesystem" 10 --hdd 1 --hdd-bytes 128M
    run_test "Process"  15 --fork 4

    log "All tests complete, starting next cycle"
done
