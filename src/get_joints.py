#!/usr/bin/env python3

import rclpy
import json
import os
import sys
from rclpy.node import Node
from sensor_msgs.msg import JointState

# Number of joints to record
NUM_JOINTS = 7

# Default output file path
DEFAULT_OUTPUT_FILE = os.path.expanduser('~/ros2_ws/src/AZ_demo/recorded_trajectories/trajectory.json')

# How many times per second to record a waypoint (Hz)
RECORD_RATE = 10


class JointStatesListener(Node):

    def __init__(self, output_file):
        super().__init__('joint_states_listener')

        self.output_file = output_file
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

        self.get_logger().info(f"Recording joint states to {self.output_file} ...")
        self.get_logger().info("Press Ctrl+C to stop and save.")

    def joint_states_callback(self, msg):
        if len(msg.position) < NUM_JOINTS:
            return

        now = self.get_clock().now()
        elapsed = (now - self.last_record_time).nanoseconds / 1e9
        if elapsed < self.record_interval:
            return
        self.last_record_time = now

        if self.start_time is None:
            self.start_time = now

        time_from_start = round((now - self.start_time).nanoseconds / 1e9, 6)
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
        with open(self.output_file, 'w') as f:
            json.dump(data, f, indent=4)
        self.get_logger().info(f"Saved {len(self.trajectory)} waypoints to {self.output_file}")


def main(args=None):
    # Parse output file from command line, stripping ROS args first
    filtered_args = [a for a in sys.argv[1:] if not a.startswith('--ros-args')]
    if filtered_args:
        output_file = os.path.expanduser(filtered_args[0])
    else:
        output_file = DEFAULT_OUTPUT_FILE

    rclpy.init(args=args)
    node = JointStatesListener(output_file)
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