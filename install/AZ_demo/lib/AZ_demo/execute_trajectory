#!/usr/bin/env python3

import rclpy
import json
import os
import sys
from rclpy.node import Node
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from control_msgs.action import FollowJointTrajectory
from rclpy.action import ActionClient
import builtin_interfaces.msg

# Default trajectory file
DEFAULT_INPUT_FILE = os.path.expanduser('~/ros2_ws/src/AZ_demo/recorded_trajectories/trajectory.json')

JOINT_NAMES = [
    'joint_1', 'joint_2', 'joint_3', 'joint_4',
    'joint_5', 'joint_6', 'joint_7'
]


class TrajectoryExecutor(Node):

    def __init__(self, input_file):
        super().__init__('trajectory_executor')

        self.input_file = input_file
        self.trajectory, self.waypoint_times = self.load_trajectory()

        self._action_client = ActionClient(
            self,
            FollowJointTrajectory,
            '/joint_trajectory_controller/follow_joint_trajectory'
        )

        self.get_logger().info('Waiting for action server...')
        self._action_client.wait_for_server()
        self.get_logger().info(f'Loaded {len(self.trajectory)} waypoints from {self.input_file}')
        self.get_logger().info('Sending trajectory...')
        self.send_trajectory()

    def load_trajectory(self):
        if not os.path.exists(self.input_file):
            self.get_logger().error(f'File not found: {self.input_file}')
            raise FileNotFoundError(f'Trajectory file not found: {self.input_file}')

        with open(self.input_file, 'r') as f:
            data = json.load(f)

        trajectory = data['trajectory']
        waypoint_times = data['waypoint_times']
        return trajectory, waypoint_times

    def send_trajectory(self):
        trajectory = JointTrajectory()
        trajectory.joint_names = JOINT_NAMES

        for i, positions in enumerate(self.trajectory):
            point = JointTrajectoryPoint()
            point.positions = positions
            point.velocities = [0.0] * len(JOINT_NAMES)
            point.accelerations = [0.0] * len(JOINT_NAMES)
            point.time_from_start = builtin_interfaces.msg.Duration(
                sec=int(self.waypoint_times[i]),
                nanosec=int((self.waypoint_times[i] % 1) * 1e9)
            )
            trajectory.points.append(point)

        goal = FollowJointTrajectory.Goal()
        goal.trajectory = trajectory

        send_goal_future = self._action_client.send_goal_async(
            goal,
            feedback_callback=self.feedback_callback
        )
        send_goal_future.add_done_callback(self.goal_response_callback)

    def goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().error('Trajectory was REJECTED by the controller')
            return
        self.get_logger().info('Trajectory accepted, executing...')
        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(self.result_callback)

    def feedback_callback(self, feedback_msg):
        feedback = feedback_msg.feedback
        self.get_logger().info(
            f'Progress - desired: {[f"{p:.3f}" for p in feedback.desired.positions]}'
        )

    def result_callback(self, future):
        result = future.result().result
        if result.error_code == FollowJointTrajectory.Result.SUCCESSFUL:
            self.get_logger().info('Trajectory completed successfully!')
        else:
            self.get_logger().error(f'Trajectory failed with error code: {result.error_code}')
        rclpy.shutdown()


def main(args=None):
    # Parse input file from command line, stripping ROS args first
    filtered_args = [a for a in sys.argv[1:] if not a.startswith('--ros-args')]
    if filtered_args:
        input_file = os.path.expanduser(filtered_args[0])
    else:
        input_file = DEFAULT_INPUT_FILE

    rclpy.init(args=args)
    node = TrajectoryExecutor(input_file)
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()