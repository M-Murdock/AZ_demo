#!/usr/bin/env python3
"""
ROS2 node: continuous rosbag recorder with timestamped, rotating bag files.

Each bag records for a configurable duration, then a new one starts
automatically. Files are named  YYYY_MM_DD_HH_MM  (UTC).

Parameters (set via ros2 param / launch file)
---------------------------------------------
    topics      string[]  Topics to record. Empty list → record all (-a).
                          Default: []
    duration    double    Seconds per bag file. Default: 60.0
    output_dir  string    Directory for bags. Default: ~/rosbags
    prefix      string    Optional filename prefix.  Default: ""

Launch file usage
-----------------
    from launch import LaunchDescription
    from launch_ros.actions import Node

    def generate_launch_description():
        return LaunchDescription([
            Node(
                package="your_package",
                executable="rosbag_recorder_node",
                name="rosbag_recorder",
                parameters=[{
                    "topics":     ["/camera/image_raw", "/imu/data"],
                    "duration":   300.0,
                    "output_dir": "/data/bags",
                    "prefix":     "robot1_",
                }],
            )
        ])
"""

import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from threading import Thread

import rclpy
from rclpy.node import Node
from rclpy.parameter import Parameter


# ── Helpers ────────────────────────────────────────────────────────────────────

def timestamp() -> str:
    """Return a UTC timestamp string: 2024_05_01_12_34"""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d_%H:%M:%S")


def bag_path(output_dir: Path, prefix: str) -> Path:
    """Build a full output path for the next bag."""
    return output_dir / f"{prefix}{timestamp()}"


def build_command(bag_dir: Path, topics: list[str]) -> list[str]:
    """Assemble the ros2 bag record shell command."""
    cmd = ["ros2", "bag", "record", "-o", str(bag_dir)]
    cmd.extend(topics if topics else ["-a"])
    return cmd


# ── Node ──────────────────────────────────────────────────────────────────────

class RosbagRecorderNode(Node):
    """ROS2 lifecycle-friendly node that continuously rotates rosbag files."""

    def __init__(self) -> None:
        super().__init__("rosbag_recorder")

        # Declare parameters (makes them visible to ros2 param / launch files)
        self.declare_parameter("topics",     value=rclpy.Parameter.Type.STRING_ARRAY)
        self.declare_parameter("duration",   60.0)
        self.declare_parameter("output_dir", str(Path.home() / "rosbags"))
        self.declare_parameter("prefix",     "")

        self._proc: subprocess.Popen | None = None
        self._running = False
        self._worker: Thread | None = None

        # Start recording once the node is fully constructed.
        # Using a one-shot timer keeps the constructor non-blocking.
        self.create_timer(0.0, self._on_start)

    # ── ROS callbacks ─────────────────────────────────────────────────────────

    def _on_start(self) -> None:
        """Called once after the first spin tick — begins the recorder loop."""
        # Destroy the one-shot timer immediately.
        # (create_timer returns the timer; we stash it just to cancel it.)
        self.destroy_timer(self._start_timer)

        topics     = self._get_topics()
        duration   = self.get_parameter("duration").value
        output_dir = Path(self.get_parameter("output_dir").value)
        prefix     = self.get_parameter("prefix").value

        self.get_logger().info(
            f"Recorder starting — duration={duration}s, "
            f"output_dir={output_dir}, "
            f"topics={topics or ['<all>']}"
        )

        output_dir.mkdir(parents=True, exist_ok=True)
        self._running = True

        # Run the blocking record loop in a background thread so the ROS
        # executor (and therefore parameter updates, shutdown, etc.) keeps
        # spinning on the main thread.
        self._worker = Thread(
            target=self._record_loop,
            args=(output_dir, topics, duration, prefix),
            daemon=True,
        )
        self._worker.start()

    # ── Recording loop (runs in background thread) ─────────────────────────────

    def _record_loop(
        self,
        output_dir: Path,
        topics: list[str],
        duration: float,
        prefix: str,
    ) -> None:
        while self._running:
            self._start_bag(output_dir, topics, prefix)
            self._wait(duration)
            self._stop_bag()

        self.get_logger().info("Recorder loop exited cleanly.")

    def _start_bag(self, output_dir: Path, topics: list[str], prefix: str) -> None:
        dest = bag_path(output_dir, prefix)
        cmd  = build_command(dest, topics)
        self.get_logger().info(f"Starting bag → {dest.name}")
        self._proc = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )

    def _wait(self, duration: float) -> None:
        """Sleep for *duration* seconds, waking every 0.5 s to check shutdown."""
        deadline = time.monotonic() + duration
        while self._running:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            time.sleep(min(remaining, 0.5))

    def _stop_bag(self) -> None:
        if self._proc is None:
            return

        if self._proc.poll() is not None:
            _, err = self._proc.communicate()
            if err:
                self.get_logger().warn(f"bag record stderr: {err.decode().strip()}")
            self._proc = None
            return

        self.get_logger().info("Stopping current bag…")
        self._proc.send_signal(signal.SIGINT)
        try:
            self._proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.get_logger().warn("Process did not stop — sending SIGKILL")
            self._proc.kill()
            self._proc.wait()
        self._proc = None

    # ── Shutdown ──────────────────────────────────────────────────────────────

    def stop(self) -> None:
        """Signal the recorder loop to stop and wait for it to finish."""
        self.get_logger().info("Shutdown requested — finishing current bag…")
        self._running = False
        if self._worker is not None:
            self._worker.join(timeout=15)

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _get_topics(self) -> list[str]:
        try:
            val = self.get_parameter("topics").value
            return list(val) if val else []
        except Exception:
            return []

    # Override create_timer so we can stash the one-shot timer handle.
    def create_timer(self, timer_period_sec, callback, **kwargs):
        t = super().create_timer(timer_period_sec, callback, **kwargs)
        # Stash only the very first timer (the one-shot start timer).
        if not hasattr(self, "_start_timer"):
            self._start_timer = t
        return t


# ── Entry point ───────────────────────────────────────────────────────────────

def main(args=None) -> None:
    rclpy.init(args=args)

    # Verify ros2 CLI is available before we spin.
    if subprocess.call(
        ["which", "ros2"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ) != 0:
        print(
            "[rosbag_recorder] ERROR: 'ros2' not found on PATH. "
            "Source your workspace first.",
            file=sys.stderr,
        )
        sys.exit(1)

    node = RosbagRecorderNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.stop()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()