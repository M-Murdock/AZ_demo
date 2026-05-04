#!/usr/bin/env python3
"""
Continuous ROS2 rosbag recorder with timestamped, rotating bag files.

Each bag file records for a configurable duration, then a new one starts
automatically. Files are named with an ISO-8601 timestamp so they sort
chronologically and are easy to trace back to wall-clock time.

Usage
-----
    python3 rosbag_recorder.py [OPTIONS]

Options (all have defaults, so the script works out of the box):
    --topics       Space-separated list of topics to record (default: all  →  -a)
    --duration     Seconds per bag file (default: 60)
    --output-dir   Directory to write bags into (default: ~/rosbags)
    --prefix       Optional prefix prepended to every filename

Examples
--------
    # Record everything, rotate every 5 minutes:
    python3 rosbag_recorder.py --duration 300

    # Record two specific topics, rotate every 30 s, custom directory:
    python3 rosbag_recorder.py \
        --topics /camera/image_raw /imu/data \
        --duration 30 \
        --output-dir /data/bags \
        --prefix robot1_
"""

import argparse
import logging
import os
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# ── Logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
log = logging.getLogger("rosbag_recorder")


# ── Helpers ────────────────────────────────────────────────────────────────────

def timestamp() -> str:
    """Return a UTC timestamp string: 2024_05_01_12_34"""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d_%H:%M")


def bag_path(output_dir: Path, prefix: str) -> Path:
    """Build a full path for the next bag file."""
    name = f"{prefix}{timestamp()}"
    return output_dir / name          # ros2 bag record adds the directory itself



def build_command(bag_dir: Path, topics: list[str]) -> list[str]:
    """Assemble the ros2 bag record command."""
    cmd = ["ros2", "bag", "record", "-o", str(bag_dir)]
    if topics:
        cmd.extend(topics)
    else:
        cmd.append("-a")              # record all topics
    return cmd


# ── Recorder ──────────────────────────────────────────────────────────────────

class ContinuousRecorder:
    """Starts, monitors, and rotates ros2 bag record processes."""

    def __init__(
        self,
        output_dir: Path,
        topics: list[str],
        duration: float,
        prefix: str,
    ) -> None:
        self.output_dir = output_dir
        self.topics = topics
        self.duration = duration
        self.prefix = prefix

        self._proc: subprocess.Popen | None = None
        self._running = True

        # Graceful shutdown on Ctrl-C / SIGTERM
        signal.signal(signal.SIGINT, self._shutdown)
        signal.signal(signal.SIGTERM, self._shutdown)

    # ── Public ────────────────────────────────────────────────────────────────

    def run(self) -> None:
        log.info(
            "Starting continuous recorder — duration=%ss, output=%s, topics=%s",
            self.duration,
            self.output_dir,
            self.topics or ["<all>"],
        )
        self.output_dir.mkdir(parents=True, exist_ok=True)

        while self._running:
            self._start_bag()
            self._wait_or_stop()
            self._stop_bag()

        log.info("Recorder stopped cleanly.")

    # ── Private ───────────────────────────────────────────────────────────────

    def _start_bag(self) -> None:
        bag_dir = bag_path(self.output_dir, self.prefix)
        cmd = build_command(bag_dir, self.topics)
        log.info("Starting bag → %s", bag_dir.name)
        log.debug("Command: %s", " ".join(cmd))
        self._proc = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )

    def _wait_or_stop(self) -> None:
        """Sleep for *duration* seconds, waking early if shutdown is requested."""
        deadline = time.monotonic() + self.duration
        while self._running:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            time.sleep(min(remaining, 0.5))   # check _running every 0.5 s

    def _stop_bag(self) -> None:
        if self._proc is None:
            return
        if self._proc.poll() is not None:
            # Process already exited — log any stderr output.
            _, err = self._proc.communicate()
            if err:
                log.warning("bag record stderr: %s", err.decode().strip())
            self._proc = None
            return

        log.info("Stopping current bag…")
        self._proc.send_signal(signal.SIGINT)
        try:
            self._proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            log.warning("Process did not exit in time — sending SIGKILL")
            self._proc.kill()
            self._proc.wait()
        self._proc = None

    def _shutdown(self, signum, frame) -> None:  # noqa: ANN001
        log.info("Shutdown signal received — finishing current bag…")
        self._running = False


# ── CLI ───────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Continuous ROS2 rosbag recorder with timestamped rotating files."
    )
    parser.add_argument(
        "--topics",
        nargs="*",
        default=[],
        metavar="TOPIC",
        help="Topics to record. Omit to record all topics (-a).",
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=60.0,
        metavar="SECONDS",
        help="Length of each bag file in seconds (default: 60).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path.home() / "rosbags",
        metavar="DIR",
        help="Directory to write bag files into (default: ~/rosbags).",
    )
    parser.add_argument(
        "--prefix",
        default="",
        metavar="STR",
        help="Optional prefix for every bag filename.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    # Sanity-check: make sure ros2 is on PATH before we start looping.
    if subprocess.call(
        ["which", "ros2"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ) != 0:
        log.error(
            "'ros2' not found on PATH. "
            "Source your ROS2 workspace first:  source /opt/ros/<distro>/setup.bash"
        )
        sys.exit(1)

    recorder = ContinuousRecorder(
        output_dir=args.output_dir,
        topics=args.topics,
        duration=args.duration,
        prefix=args.prefix,
    )
    recorder.run()


if __name__ == "__main__":
    main()