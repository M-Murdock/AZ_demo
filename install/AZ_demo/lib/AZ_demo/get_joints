#!/usr/bin/env python3

import rclpy
import json
import os
from rclpy.node import Node
from sensor_msgs.msg import JointState

# Number of joints to record
NUM_JOINTS = 7

# Output file path
OUTPUT_FILE = os.path.expanduser('~/ros2_ws/src/AZ_demo/trajectory.json')

# How many times per second to record a waypoint (Hz)
RECORD_RATE = 10


class JointStatesListener(Node):

    def __init__(self):
        super().__init__('joint_states_listener')

        self.trajectory = []
        self.waypoint_times = []
        self.start_time = None
        self.last_record_time = self.get_clock().now()
        self.record_interval = 1.0 / RECORD_RATE

        self.subscription = self.create_subscription(
            JointState,
            '/joint_states',
            self.joint_states_callback,
            10
        )

        self.get_logger().info(f"Recording joint states to {OUTPUT_FILE} ...")
        self.get_logger().info("Press Ctrl+C to stop and save.")

    def joint_states_callback(self, msg):
        # Only record the first 7 joints
        if len(msg.position) < NUM_JOINTS:
            return

        # Throttle recording to RECORD_RATE Hz
        now = self.get_clock().now()
        elapsed = (now - self.last_record_time).nanoseconds / 1e9
        if elapsed < self.record_interval:
            return
        self.last_record_time = now

        # Record start time on first waypoint
        if self.start_time is None:
            self.start_time = now

        # Time in seconds since recording started
        time_from_start = round((now - self.start_time).nanoseconds / 1e9, 6)

        # Extract first 7 joint positions
        waypoint = [round(msg.position[i], 6) for i in range(NUM_JOINTS)]
        self.trajectory.append(waypoint)
        self.waypoint_times.append(time_from_start)

        self.get_logger().info(
            f"Waypoint {len(self.trajectory)} at t={time_from_start:.2f}s: {waypoint}"
        )

    def save_trajectory(self):
        data = {
            "trajectory": self.trajectory,
            "waypoint_times": self.waypoint_times
        }
        with open(OUTPUT_FILE, 'w') as f:
            json.dump(data, f, indent=4)
        self.get_logger().info(f"Saved {len(self.trajectory)} waypoints to {OUTPUT_FILE}")


def main(args=None):
    rclpy.init(args=args)
    node = JointStatesListener()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.save_trajectory()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()