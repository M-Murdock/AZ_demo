#!/usr/bin/env python3
"""
set_cartesian_admittance.py

Enables Cartesian admittance mode on a Kinova Gen3 robot.

IMPORTANT: ros2_kortex runs the robot in LOW_LEVEL_SERVOING mode by default.
SetAdmittance only works in SINGLE_LEVEL_SERVOING (high-level) mode.
This script switches to high-level mode first, enables admittance, then on
exit restores low-level mode so ros2_kortex can resume normally.

WARNING: While admittance mode is active, ros2_kortex loses control of the
arm. Stop any active ROS2 controllers before running this script.

Prerequisites:
  PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python must be set, or add it below.
  pip3 install --break-system-packages kortex_api  (or the .whl)

Usage:
  PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python python3 set_cartesian_admittance.py
  PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python ros2 run AZ_demo cartesian_admittance
"""

import os
import argparse
import sys
import time

# Must be set before any kortex_api import
os.environ.setdefault("PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION", "python")

from kortex_api.autogen.client_stubs.BaseClientRpc import BaseClient
from kortex_api.autogen.messages import Base_pb2
from kortex_api.RouterClient import RouterClient
from kortex_api.SessionManager import SessionManager
from kortex_api.autogen.messages import Session_pb2
from kortex_api.TCPTransport import TCPTransport


def connect(ip: str, username: str, password: str):
    transport = TCPTransport()
    router = RouterClient(transport, lambda kException: print(f"Router error: {kException}"))
    transport.connect(ip, 10000)

    session_info = Session_pb2.CreateSessionInfo()
    session_info.username = username
    session_info.password = password
    session_info.session_inactivity_timeout    = 60000  # ms
    session_info.connection_inactivity_timeout = 2000   # ms

    session_manager = SessionManager(router)
    session_manager.CreateSession(session_info)
    print(f"Connected to robot at {ip}")

    return transport, router, session_manager


def get_servoing_mode(base: BaseClient) -> int:
    return base.GetServoingMode().servoing_mode


def set_servoing_mode(base: BaseClient, mode: int):
    servoing_mode = Base_pb2.ServoingModeInformation()
    servoing_mode.servoing_mode = mode
    base.SetServoingMode(servoing_mode)
    print(f"Servoing mode set to: {Base_pb2.ServoingMode.Name(mode)}")


def set_admittance(base: BaseClient, mode: int):
    admittance = Base_pb2.Admittance()
    admittance.admittance_mode = mode
    base.SetAdmittance(admittance)


def main():
    parser = argparse.ArgumentParser(description="Enable Cartesian admittance mode on Kinova Gen3")
    parser.add_argument("--ip",       default="192.168.1.10", help="Robot IP address")
    parser.add_argument("--username", default="admin",        help="Robot username")
    parser.add_argument("--password", default="admin",        help="Robot password")
    args = parser.parse_args()

    transport, router, session_manager = connect(args.ip, args.username, args.password)
    base = BaseClient(router)

    # Remember original servoing mode so we can restore it on exit
    original_mode = get_servoing_mode(base)
    print(f"Current servoing mode: {Base_pb2.ServoingMode.Name(original_mode)}")

    try:
        # SetAdmittance requires SINGLE_LEVEL_SERVOING (high-level) mode
        if original_mode != Base_pb2.SINGLE_LEVEL_SERVOING:
            print("Switching to SINGLE_LEVEL_SERVOING mode...")
            set_servoing_mode(base, Base_pb2.SINGLE_LEVEL_SERVOING)
            time.sleep(0.5)  # brief settle time after mode switch

        print("Enabling CARTESIAN admittance mode...")
        set_admittance(base, Base_pb2.CARTESIAN)
        print(
            "Admittance mode ACTIVE.\n"
            "You can now physically push/guide the end-effector.\n"
            "Press Ctrl+C to disable admittance and restore the original servoing mode."
        )

        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nDisabling admittance mode...")
        set_admittance(base, Base_pb2.DISABLED)

    finally:
        # Always restore original servoing mode so ros2_kortex can resume
        print(f"Restoring servoing mode to: {Base_pb2.ServoingMode.Name(original_mode)}")
        set_servoing_mode(base, original_mode)

        session_manager.CloseSession()
        router.SetActivationStatus(False)
        transport.disconnect()
        print("Disconnected.")


if __name__ == "__main__":
    main()