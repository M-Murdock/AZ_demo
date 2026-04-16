#!/usr/bin/env python3
"""
GUI for executing pre-recorded trajectories on the Kinova arm.
Scans the recorded_trajectories directory and shows a button for each trajectory.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import os
import subprocess
import threading
import glob


TRAJECTORIES_DIR = os.path.expanduser('~/ros2_ws/src/AZ_demo/recorded_trajectories')
EXECUTOR_SCRIPT = os.path.expanduser('~/ros2_ws/src/AZ_demo/src/execute_trajectory.py')


class TrajectoryGUI:
    def __init__(self, root):
        self.root = root
        self.root.title('Kinova Trajectory Executor')
        self.root.geometry('500x600')
        self.root.resizable(True, True)
        self.running_process = None

        self._build_ui()
        self._scan_trajectories()

    def _build_ui(self):
        # Title
        title = tk.Label(
            self.root,
            text='Kinova Arm Trajectory Executor',
            font=('Helvetica', 16, 'bold'),
            pady=10
        )
        title.pack()

        # Directory label
        dir_label = tk.Label(
            self.root,
            text=f'Trajectories: {TRAJECTORIES_DIR}',
            font=('Helvetica', 9),
            fg='gray',
            wraplength=480
        )
        dir_label.pack()

        # Refresh button
        refresh_btn = tk.Button(
            self.root,
            text='↻ Refresh',
            command=self._scan_trajectories,
            bg='#4a90d9',
            fg='white',
            font=('Helvetica', 10),
            padx=10,
            pady=4,
            relief='flat',
            cursor='hand2'
        )
        refresh_btn.pack(pady=(5, 10))

        # Scrollable frame for trajectory buttons
        container = tk.Frame(self.root)
        container.pack(fill='both', expand=True, padx=20)

        canvas = tk.Canvas(container, bg='#f5f5f5', highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient='vertical', command=canvas.yview)
        self.scroll_frame = tk.Frame(canvas, bg='#f5f5f5')

        self.scroll_frame.bind(
            '<Configure>',
            lambda e: canvas.configure(scrollregion=canvas.bbox('all'))
        )

        canvas.create_window((0, 0), window=self.scroll_frame, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # Bind mousewheel
        canvas.bind_all('<MouseWheel>', lambda e: canvas.yview_scroll(-1 * (e.delta // 120), 'units'))

        # Status bar
        self.status_var = tk.StringVar(value='Ready')
        status_bar = tk.Label(
            self.root,
            textvariable=self.status_var,
            font=('Helvetica', 10),
            bg='#e0e0e0',
            anchor='w',
            padx=10,
            pady=5
        )
        status_bar.pack(fill='x', side='bottom')

        # Stop button
        self.stop_btn = tk.Button(
            self.root,
            text='■ Stop Execution',
            command=self._stop_execution,
            bg='#e74c3c',
            fg='white',
            font=('Helvetica', 11, 'bold'),
            padx=10,
            pady=6,
            relief='flat',
            cursor='hand2',
            state='disabled'
        )
        self.stop_btn.pack(pady=8, side='bottom')

    def _scan_trajectories(self):
        # Clear existing buttons
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        # Make directory if it doesn't exist
        os.makedirs(TRAJECTORIES_DIR, exist_ok=True)

        # Find all JSON files
        files = sorted(glob.glob(os.path.join(TRAJECTORIES_DIR, '*.json')))

        if not files:
            empty_label = tk.Label(
                self.scroll_frame,
                text='No trajectory files found.\nRecord some trajectories first.',
                font=('Helvetica', 12),
                fg='gray',
                bg='#f5f5f5',
                pady=30
            )
            empty_label.pack()
            self.status_var.set(f'No trajectories found in {TRAJECTORIES_DIR}')
            return

        for filepath in files:
            filename = os.path.basename(filepath)
            name = os.path.splitext(filename)[0]
            self._create_trajectory_button(name, filepath)

        self.status_var.set(f'Found {len(files)} trajectory file(s)')

    def _create_trajectory_button(self, name, filepath):
        frame = tk.Frame(self.scroll_frame, bg='#f5f5f5', pady=4)
        frame.pack(fill='x', padx=10)

        btn = tk.Button(
            frame,
            text=f'▶  {name}',
            command=lambda p=filepath, n=name: self._execute_trajectory(p, n),
            bg='#2ecc71',
            fg='white',
            font=('Helvetica', 12),
            anchor='w',
            padx=15,
            pady=8,
            relief='flat',
            cursor='hand2',
            width=35
        )
        btn.pack(fill='x')

        # Hover effects
        btn.bind('<Enter>', lambda e, b=btn: b.config(bg='#27ae60'))
        btn.bind('<Leave>', lambda e, b=btn: b.config(bg='#2ecc71'))

    def _execute_trajectory(self, filepath, name):
        if self.running_process and self.running_process.poll() is None:
            messagebox.showwarning(
                'Already Running',
                'A trajectory is already executing. Stop it first.'
            )
            return

        self.status_var.set(f'Executing: {name}...')
        self.stop_btn.config(state='normal')

        def run():
            try:
                cmd = ['python3', EXECUTOR_SCRIPT, filepath]
                self.running_process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                stdout, stderr = self.running_process.communicate()

                if self.running_process.returncode == 0:
                    self.root.after(0, lambda: self.status_var.set(f'✓ Completed: {name}'))
                else:
                    self.root.after(0, lambda: self.status_var.set(f'✗ Failed: {name}'))
                    if stderr:
                        self.root.after(0, lambda: messagebox.showerror('Execution Error', stderr[:500]))
            except Exception as e:
                self.root.after(0, lambda: self.status_var.set(f'Error: {str(e)}'))
                self.root.after(0, lambda: messagebox.showerror('Error', str(e)))
            finally:
                self.root.after(0, lambda: self.stop_btn.config(state='disabled'))

        thread = threading.Thread(target=run, daemon=True)
        thread.start()

    def _stop_execution(self):
        if self.running_process and self.running_process.poll() is None:
            self.running_process.terminate()
            self.status_var.set('Execution stopped by user')
            self.stop_btn.config(state='disabled')


def main():
    # Make sure trajectories directory exists
    os.makedirs(TRAJECTORIES_DIR, exist_ok=True)

    root = tk.Tk()
    app = TrajectoryGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()