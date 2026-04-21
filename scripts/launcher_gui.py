#!/usr/bin/env python3
"""
ROS2 Xbox Mode Launcher GUI

Edit LAUNCH_PACKAGE and LAUNCH_FILE below, then run:
    python3 ros2_launcher_gui.py
"""

import subprocess
import signal
import sys
import threading
import tkinter as tk

import rclpy
from rclpy.node import Node

# ── Configure your launch file here ──────────────
LAUNCH_PACKAGE = "AZ_demo"
LAUNCH_FILE    = "xbox.launch.py"
LAUNCH_ARGS    = []
# ─────────────────────────────────────────────────


class LauncherNode(Node):
    def __init__(self):
        super().__init__("xbox_launcher_node")


class App:
    BG    = "#1a1a1a"
    GREEN = "#00c853"
    RED   = "#d50000"

    def __init__(self, root: tk.Tk, node: LauncherNode):
        self.root = root
        self.node = node
        self.proc: subprocess.Popen | None = None

        root.title("ROS2 Launcher")
        root.configure(bg=self.BG)
        root.geometry("320x220")
        root.resizable(False, False)

        self._show_home()

    # ── screens ──────────────────────────────────

    def _clear(self):
        for w in self.root.winfo_children():
            w.destroy()

    def _show_home(self):
        self._clear()
        self._btn("XBOX MODE", self.GREEN, self._show_xbox).pack(expand=True)

    def _show_xbox(self):
        self._clear()
        frame = tk.Frame(self.root, bg=self.BG)
        frame.pack(expand=True)
        self._btn("START", self.GREEN, self._start, parent=frame).pack(pady=8)
        self._btn("STOP",  self.RED,   self._stop,  parent=frame).pack(pady=8)

    # ── launch control ────────────────────────────

    def _start(self):
        if self.proc and self.proc.poll() is None:
            return  # already running
        cmd = ["ros2", "launch", LAUNCH_PACKAGE, LAUNCH_FILE] + LAUNCH_ARGS
        self.proc = subprocess.Popen(cmd)

    def _stop(self):
        if self.proc and self.proc.poll() is None:
            self.proc.send_signal(signal.SIGINT)
            threading.Thread(target=self._wait_or_kill, daemon=True).start()

    def _wait_or_kill(self):
        try:
            self.proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            self.proc.kill()

    # ── helper ───────────────────────────────────

    def _btn(self, text, color, cmd, parent=None):
        parent = parent or self.root
        return tk.Button(
            parent, text=text, command=cmd,
            font=("Helvetica", 16, "bold"),
            fg=self.BG, bg=color,
            activeforeground=self.BG, activebackground=color,
            relief="flat", padx=30, pady=14, cursor="hand2",
            width=10,
        )


def main():
    rclpy.init(args=sys.argv)
    node = LauncherNode()

    root = tk.Tk()
    app  = App(root, node)

    threading.Thread(target=lambda: rclpy.spin(node), daemon=True).start()

    def _on_close():
        if app.proc and app.proc.poll() is None:
            app.proc.terminate()
        node.destroy_node()
        rclpy.try_shutdown()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", _on_close)
    root.mainloop()


if __name__ == "__main__":
    main()