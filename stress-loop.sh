#!/bin/bash

set -u

LOG_FILE="/var/log/stress-loop.log"
STRESS_DURATION=30
REST_DURATION=15

log() {
    echo "$(date '+%F %T') - $1" >> "$LOG_FILE"
}

run_test() {
    local category="$1"
    shift

    log "Starting ${category} stress test"

    stress-ng "$@" --timeout "${STRESS_DURATION}s" \
        --metrics-brief >> "$LOG_FILE" 2>&1
    local result=$?

    log "Finished ${category} stress test (exit code: ${result})"
    sleep "$REST_DURATION"
    systemd-notify WATCHDOG=1
}

log "Stress loop started"

systemd-notify --ready --status="Stress loop running"

while true; do
    run_test "CPU" --cpu 2 --cpu-load 80
    run_test "Memory" --vm 1 --vm-bytes 25% --vm-keep
    run_test "Disk I/O" --io 2
    run_test "Filesystem" --hdd 1 --hdd-bytes 128M
    run_test "Process" --fork 4

    log "All tests complete, starting next cycle"
done
