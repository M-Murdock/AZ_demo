#!/usr/bin/env python3
"""
ROS2 Launcher GUI — Xbox Mode & Force Control Mode

Edit the config block below, then run:
    python3 ros2_launcher_gui.py
"""

import subprocess
import signal
import sys
import threading
import time
import tkinter as tk

import rclpy
from rclpy.node import Node

# ── Configure your launch files here ─────────────
XBOX_PACKAGE  = "AZ_demo"
XBOX_FILE     = "xbox.launch.py"
XBOX_ARGS     = []

FC_PACKAGE    = "AZ_demo"
FC_FILE       = "force_control.launch.py"
FC_ARGS       = []

FC_NODE_PACKAGE = "AZ_demo"
FC_NODE_NAME    = "cartesian_admittance"
FC_NODE_ARGS    = []
# ─────────────────────────────────────────────────

FC_NODE_DELAY = 2.0   # seconds to wait after launch before starting the node


class LauncherNode(Node):
    def __init__(self):
        super().__init__("launcher_node")


class App:
    BG    = "#1a1a1a"
    GREEN = "#00c853"
    RED   = "#d50000"
    BLUE  = "#1565c0"
    MUTED = "#444444"

    def __init__(self, root: tk.Tk, node: LauncherNode):
        self.root = root
        self.node = node
        self.proc: subprocess.Popen | None = None       # launch file process
        self.fc_node_proc: subprocess.Popen | None = None  # cartesian_admittance node

        root.title("ROS2 Launcher")
        root.configure(bg=self.BG)
        root.geometry("320x300")
        root.resizable(False, False)

        self._show_home()

    # ── screens ──────────────────────────────────

    def _clear(self):
        for w in self.root.winfo_children():
            w.destroy()

    def _show_home(self):
        self._clear()
        frame = tk.Frame(self.root, bg=self.BG)
        frame.pack(expand=True)
        self._btn("XBOX MODE",          self.GREEN, self._show_xbox, parent=frame).pack(pady=8)
        self._btn("FORCE CONTROL MODE", self.BLUE,  self._show_fc,   parent=frame).pack(pady=8)

    def _show_xbox(self):
        self._clear()
        frame = tk.Frame(self.root, bg=self.BG)
        frame.pack(expand=True)
        self._btn("START",  self.GREEN, lambda: self._start(XBOX_PACKAGE, XBOX_FILE, XBOX_ARGS), parent=frame).pack(pady=8)
        self._btn("STOP",   self.RED,   self._stop,       parent=frame).pack(pady=8)
        self._btn("← BACK", self.MUTED, self._show_home,  parent=frame).pack(pady=8)

    def _show_fc(self):
        self._clear()
        frame = tk.Frame(self.root, bg=self.BG)
        frame.pack(expand=True)
        self._btn("START",  self.GREEN, self._start_fc,  parent=frame).pack(pady=8)
        self._btn("STOP",   self.RED,   self._stop_fc,   parent=frame).pack(pady=8)
        self._btn("← BACK", self.MUTED, self._show_home, parent=frame).pack(pady=8)

    # ── xbox launch control ───────────────────────

    def _start(self, package, file, args):
        if self.proc and self.proc.poll() is None:
            return
        self.proc = subprocess.Popen(["ros2", "launch", package, file] + args)

    def _stop(self):
        self._kill_proc(self.proc)

    # ── fc launch + node control ──────────────────

    def _start_fc(self):
        if self.proc and self.proc.poll() is None:
            return
        self.proc = subprocess.Popen(["ros2", "launch", FC_PACKAGE, FC_FILE] + FC_ARGS)
        # wait briefly then start the node in a background thread
        threading.Thread(target=self._delayed_start_fc_node, daemon=True).start()

    def _delayed_start_fc_node(self):
        time.sleep(FC_NODE_DELAY)
        if self.proc and self.proc.poll() is None:  # only if launch is still running
            self.fc_node_proc = subprocess.Popen(
                ["ros2", "run", FC_NODE_PACKAGE, FC_NODE_NAME] + FC_NODE_ARGS
            )

    def _stop_fc(self):
        self._kill_proc(self.fc_node_proc)
        self.fc_node_proc = None
        self._kill_proc(self.proc)

    # ── shared kill helper ────────────────────────

    def _kill_proc(self, proc: subprocess.Popen | None):
        if proc and proc.poll() is None:
            proc.send_signal(signal.SIGINT)
            threading.Thread(target=self._wait_or_kill, args=(proc,), daemon=True).start()

    def _wait_or_kill(self, proc: subprocess.Popen):
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()

    # ── button helper ─────────────────────────────

    def _btn(self, text, color, cmd, parent=None):
        parent = parent or self.root
        return tk.Button(
            parent, text=text, command=cmd,
            font=("Helvetica", 14, "bold"),
            fg="#ffffff" if color == self.MUTED else self.BG,
            bg=color,
            activeforeground="#ffffff" if color == self.MUTED else self.BG,
            activebackground=color,
            relief="flat", padx=30, pady=12, cursor="hand2",
            width=18,
        )


def main():
    rclpy.init(args=sys.argv)
    node = LauncherNode()

    root = tk.Tk()
    app  = App(root, node)

    threading.Thread(target=lambda: rclpy.spin(node), daemon=True).start()

    def _on_close():
        app._kill_proc(app.fc_node_proc)
        app._kill_proc(app.proc)
        node.destroy_node()
        rclpy.try_shutdown()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", _on_close)
    root.mainloop()


if __name__ == "__main__":
    main()