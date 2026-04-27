#!/usr/bin/env python3

import rclpy
import sys
from rclpy.node import Node
from rclpy.action import ActionClient
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from control_msgs.action import FollowJointTrajectory
import builtin_interfaces.msg

JOINT_NAMES = [
    'joint_1', 'joint_2', 'joint_3', 'joint_4',
    'joint_5', 'joint_6', 'joint_7'
]

# ── Home position (Gen3 7-DOF) ─────────────────────────────────────────────────
HOME = [0.0, -0.35, 0.0, -1.57, 0.0, -1.05, 1.57]

# ── Motion library ─────────────────────────────────────────────────────────────
MOTIONS = {

    'wave': {
        'description': 'Raises arm and waves wrist side to side',
        'waypoints': [
            [0.0,  -0.60,  0.0,  -1.20,  0.0,  -0.80,  1.57],  # raise to wave-ready
            [0.0,  -0.60,  0.0,  -1.20,  0.0,  -0.30,  1.57],  # wave down
            [0.0,  -0.60,  0.0,  -1.20,  0.0,  -1.20,  1.57],  # wave up
            [0.0,  -0.60,  0.0,  -1.20,  0.0,  -0.30,  1.57],  # wave down
            [0.0,  -0.60,  0.0,  -1.20,  0.0,  -1.20,  1.57],  # wave up
            [0.0,  -0.60,  0.0,  -1.20,  0.0,  -0.30,  1.57],  # wave down
            HOME,                                                 # return home
        ],
        'times': [3.0, 4.5, 6.0, 7.5, 9.0, 10.5, 13.0],
    },

    'laugh': {
        'description': 'Rapid bouncy torso-like bobbing to mimic laughter',
        'waypoints': [
            [0.0,  -0.20,  0.0,  -1.40,  0.0,  -1.05,  1.57],  # lean back slightly
            [0.0,  -0.50,  0.0,  -1.70,  0.0,  -1.05,  1.57],  # bob forward
            [0.0,  -0.20,  0.0,  -1.40,  0.0,  -1.05,  1.57],  # lean back
            [0.0,  -0.50,  0.0,  -1.70,  0.0,  -1.05,  1.57],  # bob forward
            [0.0,  -0.20,  0.0,  -1.40,  0.0,  -1.05,  1.57],  # lean back
            [0.0,  -0.50,  0.0,  -1.70,  0.0,  -1.05,  1.57],  # bob forward
            [0.0,  -0.20,  0.0,  -1.40,  0.0,  -1.05,  1.57],  # lean back
            HOME,                                                 # return home
        ],
        'times': [2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 10.5],
    },

    'sad': {
        'description': 'Slow drooping motion, hangs low then slumps to home',
        'waypoints': [
            [0.0,   0.20,  0.0,  -1.20,  0.0,  -0.50,  1.57],  # lift slightly
            [0.0,   0.40,  0.0,  -0.80,  0.0,  -0.20,  1.57],  # droop forward
            [0.0,   0.50,  0.0,  -0.60,  0.0,  -0.10,  1.57],  # slump deeper
            [0.0,   0.40,  0.0,  -0.80,  0.0,  -0.20,  1.57],  # hang there
            [0.0,   0.50,  0.0,  -0.60,  0.0,  -0.10,  1.57],  # slump again
            HOME,                                                 # slowly return
        ],
        'times': [3.0, 6.0, 9.5, 13.0, 16.5, 22.0],
    },

}
# ──────────────────────────────────────────────────────────────────────────────


class MotionPlayer(Node):

    def __init__(self, motion_name: str):
        super().__init__('motion_player')

        motion = MOTIONS[motion_name]
        self.waypoints = motion['waypoints']
        self.times = motion['times']

        assert len(self.waypoints) == len(self.times), \
            "waypoints and times must have the same length"

        self._action_client = ActionClient(
            self,
            FollowJointTrajectory,
            '/joint_trajectory_controller/follow_joint_trajectory'
        )

        self.get_logger().info('Waiting for action server...')
        self._action_client.wait_for_server()
        self.get_logger().info(
            f'Playing motion "{motion_name}": {motion["description"]}'
        )
        self._send_trajectory()

    def _send_trajectory(self):
        trajectory = JointTrajectory()
        trajectory.joint_names = JOINT_NAMES

        for positions, t in zip(self.waypoints, self.times):
            point = JointTrajectoryPoint()
            point.positions = positions
            point.velocities = [0.0] * len(JOINT_NAMES)
            point.accelerations = [0.0] * len(JOINT_NAMES)
            point.time_from_start = builtin_interfaces.msg.Duration(
                sec=int(t),
                nanosec=int((t % 1) * 1e9)
            )
            trajectory.points.append(point)

        goal = FollowJointTrajectory.Goal()
        goal.trajectory = trajectory

        future = self._action_client.send_goal_async(
            goal,
            feedback_callback=self._feedback_callback
        )
        future.add_done_callback(self._goal_response_callback)

    def _goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().error('Goal REJECTED by controller.')
            rclpy.shutdown()
            return
        self.get_logger().info('Goal accepted, executing...')
        goal_handle.get_result_async().add_done_callback(self._result_callback)

    def _feedback_callback(self, feedback_msg):
        positions = feedback_msg.feedback.desired.positions
        self.get_logger().info(
            f'Desired: {[f"{p:.3f}" for p in positions]}'
        )

    def _result_callback(self, future):
        result = future.result().result
        if result.error_code == FollowJointTrajectory.Result.SUCCESSFUL:
            self.get_logger().info('Motion complete!')
        else:
            self.get_logger().error(
                f'Motion failed with error code: {result.error_code}'
            )
        rclpy.shutdown()


def main(args=None):
    # Strip ROS args, leaving only our positional argument
    filtered = [a for a in sys.argv[1:] if not a.startswith('--ros-args')]

    if not filtered:
        print(f'Usage: motion_player.py <motion>')
        print(f'Available motions:')
        for name, data in MOTIONS.items():
            print(f'  {name:<10} — {data["description"]}')
        sys.exit(1)

    motion_name = filtered[0].lower()
    if motion_name not in MOTIONS:
        print(f'Unknown motion: "{motion_name}"')
        print(f'Available: {", ".join(MOTIONS.keys())}')
        sys.exit(1)

    rclpy.init(args=args)
    node = MotionPlayer(motion_name)
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()