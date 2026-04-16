#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from moveit_msgs.action import MoveGroup
from moveit_msgs.msg import MotionPlanRequest, WorkspaceParameters, Constraints, JointConstraint
from rclpy.action import ActionClient
from sensor_msgs.msg import JointState
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from control_msgs.action import FollowJointTrajectory
import builtin_interfaces.msg
import os

import json

data = []
with open(os.path.expanduser('~/ros2_ws/src/AZ_demo/trajectory.json'), 'r') as f:
    data = json.load(f)

TRAJECTORY = data["trajectory"]
WAYPOINT_TIMES = data["waypoint_times"]

# Define your trajectory here as a list of joint positions (radians)
# Each entry is one waypoint: [joint_1, joint_2, joint_3, joint_4, joint_5, joint_6, joint_7]
# TRAJECTORY = [
#     [0.0,    0.0,    0.0,   0.0,   0.0,   0.0,   0.0],
#     [0.3,   -0.3,    0.3,  -0.5,   0.3,  -0.3,   0.3],
#     [0.6,   -0.6,    0.6,  -1.0,   0.6,  -0.6,   0.6],
#     [0.3,   -0.3,    0.3,  -0.5,   0.3,  -0.3,   0.3],
#     [0.0,    0.0,    0.0,   0.0,   0.0,   0.0,   0.0],
# ]

# Time in seconds to reach each waypoint
# WAYPOINT_TIMES = [0.0, 3.0, 6.0, 9.0, 12.0]

JOINT_NAMES = [
    'joint_1', 'joint_2', 'joint_3', 'joint_4',
    'joint_5', 'joint_6', 'joint_7'
]


class TrajectoryExecutor(Node):

    def __init__(self):
        super().__init__('trajectory_executor')

        self._action_client = ActionClient(
            self,
            FollowJointTrajectory,
            '/joint_trajectory_controller/follow_joint_trajectory'
        )

        self.get_logger().info('Waiting for action server...')
        self._action_client.wait_for_server()
        self.get_logger().info('Action server found. Sending trajectory...')
        self.send_trajectory()

    def send_trajectory(self):
        trajectory = JointTrajectory()
        trajectory.joint_names = JOINT_NAMES

        for i, positions in enumerate(TRAJECTORY):
            point = JointTrajectoryPoint()
            point.positions = positions
            point.velocities = [0.0] * len(JOINT_NAMES)
            point.accelerations = [0.0] * len(JOINT_NAMES)
            point.time_from_start = builtin_interfaces.msg.Duration(
                sec=int(WAYPOINT_TIMES[i]),
                nanosec=int((WAYPOINT_TIMES[i] % 1) * 1e9)
            )
            trajectory.points.append(point)

        goal = FollowJointTrajectory.Goal()
        goal.trajectory = trajectory

        self.get_logger().info(f'Sending trajectory with {len(TRAJECTORY)} waypoints...')
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
    rclpy.init(args=args)
    node = TrajectoryExecutor()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()


if __name__ == '__main__':
    main()