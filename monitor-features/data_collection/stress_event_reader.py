import os
import stat
from pathlib import Path

#This part of the path connects the stress script to this reader using a named pipe.
FIFO_PATH = Path("/run/unix-monitor/stress-events.fifo")

#This part of the code reads a file that relays the latest event available to the monitoring API.
STATUS_PATH = Path("/run/unix-monitor/current-stress.txt")

VALID_EVENTS = {
    "CPU",
    "Memory",
    "Disk I/O",
    "Filesystem",
    "Process",
    "IDLE"
}

def setup_fifo():
    FIFO_PATH.parent.mkdir(parents = True, exist_ok = True)

    if not FIFO_PATH.exists():
        os.mkfifo(FIFO_PATH, 0o620)
    elif not stat.S_ISFIFO(FIFO_PATH.stat().st_mode):
        raise RuntimeError("Stress Event Path Exists, But It Is Not A FIFO.")

    os.chmod(FIFO_PATH, 0o620)
    STATUS_PATH.write_text("IDLE\n")
    os.chmod(STATUS_PATH, 0o644)

def listen_for_events():
    print("Stress event reader started.", flush = True)

    while True:
        with FIFO_PATH.open("r") as pipe:
            for line in pipe:
                event = line.strip()

                if event in VALID_EVENTS:
                    STATUS_PATH.write_text(event + "\n")
                    print(f"Stress Event Received: {event}", flush = True)


if __name__ == "__main__":
    setup_fifo()
    listen_for_events()