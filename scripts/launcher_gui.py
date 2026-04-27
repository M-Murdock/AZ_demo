#!/usr/bin/env python3
"""
ROS2 Launcher GUI — Xbox Mode, Force Control Mode & Web Mode

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

FC_NODE_PACKAGE = "AZ_demo"
FC_NODE_NAME    = "cartesian_admittance"
FC_NODE_ARGS    = []

FC_PACKAGE    = "AZ_demo"
FC_FILE       = "force_control.launch.py"
FC_ARGS       = []

WEB_PACKAGE   = "AZ_demo"
WEB_FILE      = "web_interface.launch.py"
WEB_ARGS      = []

ROBOT_PACKAGE = "AZ_demo"
ROBOT_FILE    = "start_robot.launch.py"
ROBOT_ARGS    = []

EMOJIS_PACKAGE = "AZ_demo"
EMOJIS_FILE    = "emoji.launch.py"
EMOJIS_ARGS    = []

TRAJ_PACKAGE = "AZ_demo"
TRAJ_FILE = "execute_trajectory.py"
TRAJ_ARGS = []
# ─────────────────────────────────────────────────

FC_NODE_DELAY  = 2.0   # seconds to wait after launch before starting the node
SHUTDOWN_TIMEOUT = 5.0  # seconds to wait for processes to die before force-killing


class LauncherNode(Node):
    def __init__(self):
        super().__init__("launcher_node")


class App:
    BG      = "#1a1a1a"
    GREEN   = "#00c853"
    RED     = "#d50000"
    BLUE    = "#1565c0"
    AMBER   = "#ff6f00"
    PURPLE  = "#6a1b9a"

    def __init__(self, root: tk.Tk, node: LauncherNode):
        self.root = root
        self.node = node

        # All tracked processes in one place
        self.proc: subprocess.Popen | None = None           # main launch (xbox / robot)
        self.fc_proc: subprocess.Popen | None = None        # robot launch for xbox mode
        self.fc_node_proc: subprocess.Popen | None = None  # cartesian_admittance run node
        self.web_proc: subprocess.Popen | None = None
        self.robot_proc: subprocess.Popen | None = None
        self.emojis_proc: subprocess.Popen | None = None
        self.exec_proc: subprocess.Popen | None = None      # execute_trajectory

        self._spinner_job = None

        root.title("ROS2 Launcher")
        root.configure(bg=self.BG)
        root.geometry("320x300")
        root.resizable(False, False)

        self._show_home()

    # ── screens ──────────────────────────────────

    def _clear(self):
        self._stop_spinner()
        for w in self.root.winfo_children():
            w.destroy()

    def _show_home(self):
        self._clear()
        frame = tk.Frame(self.root, bg=self.BG)
        frame.pack(expand=True)
        self._btn("XBOX MODE",          self.GREEN,  self._show_xbox, parent=frame).pack(pady=8)
        self._btn("FORCE CONTROL MODE", self.BLUE,   self._show_fc,   parent=frame).pack(pady=8)
        self._btn("WEB",                self.PURPLE, self._show_web,  parent=frame).pack(pady=8)

    def _show_xbox(self):
        self._clear()
        frame = tk.Frame(self.root, bg=self.BG)
        frame.pack(expand=True)

        status_var = tk.StringVar(value="")

        def on_start():
            if self.proc and self.proc.poll() is None:
                return
            self._start(XBOX_PACKAGE, XBOX_FILE, ['controller:=xbox'])
            self._set_status(status_lbl, status_var, "● RUNNING", self.GREEN)

        def on_stop():
            self._stop_all()
            self._show_home()

        self._btn("START", self.GREEN, on_start, parent=frame).pack(pady=8)
        self._btn("STOP",  self.RED,   on_stop,  parent=frame).pack(pady=8)

        status_lbl = tk.Label(
            frame, textvariable=status_var,
            font=("Helvetica", 11, "bold"),
            fg=self.BG, bg=self.BG,
            width=18,
        )
        status_lbl.pack(pady=(4, 0))

    def _show_fc(self):
        self._clear()
        frame = tk.Frame(self.root, bg=self.BG)
        frame.pack(expand=True)

        status_var = tk.StringVar(value="")

        def on_start():
            if self.proc and self.proc.poll() is None:
                return
            self._start_fc(status_var, status_lbl)

        def on_stop():
            self._stop_all()
            self._show_home()

        self._btn("START", self.GREEN, on_start, parent=frame).pack(pady=8)
        self._btn("STOP",  self.RED,   on_stop,  parent=frame).pack(pady=8)

        status_lbl = tk.Label(
            frame, textvariable=status_var,
            font=("Helvetica", 11, "bold"),
            fg=self.BG, bg=self.BG,
            width=18,
        )
        status_lbl.pack(pady=(4, 0))

    def _show_web(self):
        self._clear()
        frame = tk.Frame(self.root, bg=self.BG)
        frame.pack(expand=True)

        self._btn("ARROWS", self.GREEN, self._launch_web_arrows, parent=frame).pack(pady=8)
        self._btn("EMOJIS", self.AMBER, self._show_emojis,       parent=frame).pack(pady=8)

        back_btn = tk.Button(
            frame, text="← BACK", command=self._show_home,
            font=("Helvetica", 10, "bold"),
            fg="#888888", bg=self.BG,
            activeforeground="#aaaaaa", activebackground=self.BG,
            relief="flat", cursor="hand2", bd=0,
        )
        back_btn.pack(pady=(12, 0))

    def _show_emojis(self):
        self._clear()
        frame = tk.Frame(self.root, bg=self.BG)
        frame.pack(expand=True)

        status_var = tk.StringVar(value="")

        def on_start():
            if self.emojis_proc and self.emojis_proc.poll() is None:
                return
            self.emojis_proc = subprocess.Popen(
                ["ros2", "launch", EMOJIS_PACKAGE, EMOJIS_FILE] + EMOJIS_ARGS
            )
            self.web_proc = subprocess.Popen(
                ["ros2", "launch", WEB_PACKAGE, WEB_FILE] + WEB_ARGS
            )
            self._start_spinner(status_lbl, status_var)
            threading.Thread(
                target=self._delayed_start_traj,
                args=(status_var, status_lbl),
                daemon=True,
            ).start()

        def on_stop():
            self._stop_all()
            self._show_web()

        import webbrowser, pathlib
        index = pathlib.Path(__file__).parent / "emojis.html"
        webbrowser.open(index.as_uri())

        self._btn("START", self.GREEN, on_start, parent=frame).pack(pady=8)
        self._btn("STOP",  self.RED,   on_stop,  parent=frame).pack(pady=8)

        status_lbl = tk.Label(
            frame, textvariable=status_var,
            font=("Helvetica", 11, "bold"),
            fg=self.BG, bg=self.BG,
            width=18,
        )
        status_lbl.pack(pady=(4, 0))

        back_btn = tk.Button(
            frame, text="← BACK", command=self._show_web,
            font=("Helvetica", 10, "bold"),
            fg="#888888", bg=self.BG,
            activeforeground="#aaaaaa", activebackground=self.BG,
            relief="flat", cursor="hand2", bd=0,
        )
        back_btn.pack(pady=(12, 0))

    # ── web launch helpers ────────────────────────

    def _launch_web_arrows(self):
        if self.web_proc and self.web_proc.poll() is None:
            return
        self.web_proc = subprocess.Popen(
            ["ros2", "launch", WEB_PACKAGE, WEB_FILE] + WEB_ARGS
        )
        self.proc = subprocess.Popen(
            ["ros2", "launch", XBOX_PACKAGE, XBOX_FILE] + ['controller:=web']
        )

        import webbrowser, pathlib
        index = pathlib.Path(__file__).parent / "index.html"
        webbrowser.open(index.as_uri())

    # ── status label helpers ──────────────────────

    def _set_status(self, lbl: tk.Label, var: tk.StringVar, text: str, color: str):
        try:
            var.set(text)
            lbl.config(fg=color, bg=self.BG)
        except tk.TclError:
            pass

    def _start_spinner(self, lbl: tk.Label, var: tk.StringVar):
        frames = ["◐ Starting…", "◓ Starting…", "◑ Starting…", "◒ Starting…"]
        idx = [0]

        def _tick():
            try:
                var.set(frames[idx[0] % len(frames)])
                lbl.config(fg=self.AMBER, bg=self.BG)
                idx[0] += 1
                self._spinner_job = self.root.after(200, _tick)
            except tk.TclError:
                pass

        _tick()

    def _stop_spinner(self):
        if self._spinner_job is not None:
            try:
                self.root.after_cancel(self._spinner_job)
            except tk.TclError:
                pass
            self._spinner_job = None

    # ── xbox launch control ───────────────────────

    def _start(self, package, file, args):
        if self.proc and self.proc.poll() is None:
            return
        self.proc    = subprocess.Popen(["ros2", "launch", package, file] + args)
        self.fc_proc = subprocess.Popen(["ros2", "launch", ROBOT_PACKAGE, ROBOT_FILE] + ROBOT_ARGS)

    # ── fc launch + node control ──────────────────

    def _start_fc(self, status_var: tk.StringVar, status_lbl: tk.Label):
        self.proc = subprocess.Popen(["ros2", "launch", ROBOT_PACKAGE, ROBOT_FILE] + ROBOT_ARGS)
        self._start_spinner(status_lbl, status_var)
        threading.Thread(
            target=self._delayed_start_fc_node,
            args=(status_var, status_lbl),
            daemon=True,
        ).start()

    def _delayed_start_fc_node(self, status_var: tk.StringVar, status_lbl: tk.Label):
        time.sleep(FC_NODE_DELAY)
        if self.proc and self.proc.poll() is None:
            self.fc_node_proc = subprocess.Popen(
                ["ros2", "run", FC_NODE_PACKAGE, FC_NODE_NAME] + FC_NODE_ARGS
            )
            self.root.after(0, lambda: (
                self._stop_spinner(),
                self._set_status(status_lbl, status_var, "● RUNNING", self.GREEN),
            ))

    # ── emojis trajectory delayed start ──────────

    def _delayed_start_traj(self, status_var: tk.StringVar, status_lbl: tk.Label):
        time.sleep(FC_NODE_DELAY)
        if self.emojis_proc and self.emojis_proc.poll() is None:
            self.exec_proc = subprocess.Popen(
                ["ros2", "run", TRAJ_PACKAGE, TRAJ_FILE] + TRAJ_ARGS
            )
            self.root.after(0, lambda: (
                self._stop_spinner(),
                self._set_status(status_lbl, status_var, "● RUNNING", self.GREEN),
            ))

    # ── unified stop ──────────────────────────────

    def _stop_all(self):
        """Send SIGINT to every tracked process, then wait for all to exit."""
        all_procs = [
            self.proc,
            self.fc_proc,
            self.fc_node_proc,
            self.web_proc,
            self.robot_proc,
            self.emojis_proc,
            self.exec_proc,
        ]
        live = [p for p in all_procs if p and p.poll() is None]

        # Signal all at once so they shut down in parallel
        for p in live:
            try:
                p.send_signal(signal.SIGINT)
            except (ProcessLookupError, OSError):
                pass

        # Wait up to SHUTDOWN_TIMEOUT for each; force-kill stragglers
        deadline = time.monotonic() + SHUTDOWN_TIMEOUT
        for p in live:
            remaining = deadline - time.monotonic()
            try:
                p.wait(timeout=max(remaining, 0.1))
            except subprocess.TimeoutExpired:
                try:
                    p.kill()
                    p.wait(timeout=2)
                except (ProcessLookupError, OSError):
                    pass

        # Clear all references
        self.proc = None
        self.fc_proc = None
        self.fc_node_proc = None
        self.web_proc = None
        self.robot_proc = None
        self.emojis_proc = None
        self.exec_proc = None

    # ── button helper ─────────────────────────────

    def _btn(self, text, color, cmd, parent=None):
        parent = parent or self.root
        return tk.Button(
            parent, text=text, command=cmd,
            font=("Helvetica", 14, "bold"),
            fg=self.BG,
            bg=color,
            activeforeground=self.BG,
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
        # Disable the close button to prevent double-calls while shutting down
        root.protocol("WM_DELETE_WINDOW", lambda: None)
        # Kill all ROS processes synchronously before tearing down rclpy/tk
        app._stop_all()
        node.destroy_node()
        rclpy.try_shutdown()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", _on_close)
    root.mainloop()


if __name__ == "__main__":
    main()