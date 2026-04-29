#!/usr/bin/env python3

import rclpy
import sys
from rclpy.node import Node
from rclpy.action import ActionClient
from std_msgs.msg import String
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

    # 👍  Thumbs up
    # Arm sweeps up and forward, wrist rotates to orient "thumb skyward",
    # holds the pose proudly, then lowers back to home.
    'thumbs_up': {
        'description': 'Raises arm and tilts wrist into a proud thumbs-up pose',
        'waypoints': [
            [0.0,  -0.10,  0.0,  -1.80,  0.0,  -1.40,  1.57],  # lift & extend
            [0.0,   0.10,  0.0,  -1.90,  0.0,  -1.55,  0.80],  # rotate wrist — thumb up
            [0.0,   0.10,  0.0,  -1.90,  0.0,  -1.55,  0.80],  # hold the pose
            [0.0,   0.10,  0.0,  -1.90,  0.0,  -1.55,  0.80],  # hold a bit longer
            HOME,                                                 # return home
        ],
        'times': [5.0, 8.5, 12.0, 15.5, 20.0],
    },

    # 😩  Uggghh
    # Slow forward slump, wrist droops, hangs heavily, slight sway of despair,
    # then reluctantly lifts back to home.
    'uggh': {
        'description': 'Slow defeated forward droop with a limp wrist flop',
        'waypoints': [
            [0.0,   0.10,  0.0,  -1.20,  0.0,  -0.70,  1.57],  # begin to droop forward
            [0.0,   0.35,  0.0,  -0.80,  0.0,  -0.30,  1.57],  # slump further
            [0.0,   0.50,  0.0,  -0.50,  0.0,  -0.10,  2.20],  # wrist flops outward
            [0.0,   0.55,  0.0,  -0.40,  0.0,  -0.05,  2.40],  # dead hang
            [0.0,   0.55,  0.0,  -0.40,  0.0,  -0.05,  2.40],  # linger in despair
            [0.0,   0.45,  0.0,  -0.55,  0.0,  -0.15,  2.10],  # sway slightly
            [0.0,   0.55,  0.0,  -0.40,  0.0,  -0.05,  2.40],  # slump back
            HOME,                                                 # reluctant recovery
        ],
        'times': [6.0, 11.0, 16.0, 20.0, 24.0, 27.0, 30.5, 37.0],
    },

    # 🙂‍↔️ Head Shake
    # Arm holds an upright flickering pose; wrist oscillations left-right
    # and small elbow pulses mimic a dancing flame.
    'head-shake': {
        'description': 'Arm holds raised pose while wrist flickers like a flame',
        'waypoints': [
            [0.0,  -0.40,  0.0,  -1.70,  0.0,  -1.30,  1.57],  # rise to flame-ready
            [0.10, -0.45,  0.0,  -1.75,  0.10, -1.10,  1.20],  # flicker right-lean
            [-.10, -0.50,  0.0,  -1.80,  -.10, -1.50,  1.90],  # flicker left-lean
            [0.10, -0.42,  0.0,  -1.72,  0.10, -1.08,  1.15],  # flicker right
            [-.10, -0.48,  0.0,  -1.78,  -.10, -1.48,  1.95],  # flicker left
            [0.10, -0.44,  0.0,  -1.73,  0.10, -1.10,  1.20],  # flicker right
            [-.10, -0.50,  0.0,  -1.80,  -.10, -1.50,  1.90],  # flicker left
            [0.0,  -0.45,  0.0,  -1.75,  0.0,  -1.30,  1.57],  # settle centre
            HOME,                                                 # return home
        ],
        'times': [5.0, 7.0, 9.0, 11.0, 13.0, 15.0, 17.0, 20.0, 25.0],
    },

    # 😂  Laugh
    # Rocks between leaning back (j2 more negative) and lurching forward
    # (j2 less negative / toward home) — like a body shaking with laughter.
    'laugh': {
        'description': 'Bouncy torso-like rocking to mimic laughter',
        'waypoints': [
            [0.0,  -0.55,  0.0,  -1.40,  0.0,  -1.05,  1.57],  # lean back
            [0.0,  -0.20,  0.0,  -1.70,  0.0,  -1.05,  1.57],  # lurch forward
            [0.0,  -0.55,  0.0,  -1.40,  0.0,  -1.05,  1.57],  # lean back
            [0.0,  -0.20,  0.0,  -1.70,  0.0,  -1.05,  1.57],  # lurch forward
            [0.0,  -0.55,  0.0,  -1.40,  0.0,  -1.05,  1.57],  # lean back
            [0.0,  -0.20,  0.0,  -1.70,  0.0,  -1.05,  1.57],  # lurch forward
            [0.0,  -0.55,  0.0,  -1.40,  0.0,  -1.05,  1.57],  # lean back
            HOME,                                                 # return home
        ],
        'times': [4.0, 6.5, 9.0, 11.5, 14.0, 16.5, 19.0, 23.0],
    },

    # 😭  Sobbing
    # Arm raises to cover-face height, then heaves with deep irregular sobs —
    # big slow drops forward (j2 positive = hunching over) punctuated by
    # gasping lifts (j2 back negative). j7 drifts loose and wobbly throughout.
    # Sobs get slightly smaller as energy drains. Ends fully hunched, then
    # slowly, miserably straightens home.
    'sobbing': {
        'description': 'Deep heaving sobs — hunches forward, gasps back, collapses, repeats',
        'waypoints': [
            # Raise arm to face-cover height, wrist turning inward
            [ 0.0,  -0.90,  0.0,  -0.90,  0.0,  -0.85,  1.00],  # lift to face
            [ 0.0,  -0.90,  0.0,  -0.90,  0.0,  -0.85,  1.00],  # hold — moment before sob
            # Sob 1 — big heave forward and down
            [ 0.0,   0.30,  0.0,  -1.10,  0.0,  -0.60,  1.80],  # heave forward (sob)
            # Gasp back up
            [ 0.0,  -0.80,  0.0,  -0.85,  0.0,  -0.85,  1.10],  # gasp upward
            # Sob 2 — heave forward again, slightly deeper
            [ 0.0,   0.40,  0.0,  -1.15,  0.0,  -0.55,  1.90],  # heave deeper
            # Gasp back up, less recovery this time
            [ 0.0,  -0.65,  0.0,  -0.90,  0.0,  -0.80,  1.20],  # weaker gasp
            # Sob 3 — biggest heave, nearly collapsed
            [ 0.0,   0.50,  0.0,  -1.20,  0.0,  -0.45,  2.10],  # biggest sob
            # Barely recovers
            [ 0.0,  -0.45,  0.0,  -1.00,  0.0,  -0.75,  1.40],  # feeble lift
            # Sob 4 — smaller now, energy spent
            [ 0.0,   0.35,  0.0,  -1.10,  0.0,  -0.50,  1.85],  # smaller sob
            # Collapses into final slump, stays there
            [ 0.0,   0.45,  0.0,  -1.15,  0.0,  -0.45,  2.00],  # final slump
            [ 0.0,   0.45,  0.0,  -1.15,  0.0,  -0.45,  2.00],  # hold, spent
            HOME,                                                  # slow, heavy return
        ],
        'times': [5.0, 8.5, 12.0, 15.5, 19.0, 22.5, 26.0, 29.5, 33.0, 36.5, 41.0, 48.0],
    },


    # 😱  Shocked
    # Arm snaps backward (recoil), freezes in wide-open pose, then
    # trembles slightly before settling back to home.
    'shocked': {
        'description': 'Recoil snap, freeze, then a startled tremble',
        'waypoints': [
            [0.0,  -0.70,  0.0,  -1.00,  0.0,  -0.70,  1.57],  # snap back
            [0.0,  -0.68,  0.0,  -1.02,  0.0,  -0.72,  1.57],  # tremble 1
            [0.0,  -0.72,  0.0,  -0.98,  0.0,  -0.68,  1.57],  # tremble 2
            [0.0,  -0.68,  0.0,  -1.02,  0.0,  -0.72,  1.57],  # tremble 3
            [0.0,  -0.72,  0.0,  -0.98,  0.0,  -0.68,  1.57],  # tremble 4
            [0.0,  -0.70,  0.0,  -1.00,  0.0,  -0.70,  1.57],  # hold still
            HOME,                                                 # recover to home
        ],
        'times': [3.0, 5.0, 7.0, 9.0, 11.0, 14.5, 19.0],
    },

    # 😤  Angry fuming
    # Short sharp jabs forward (j2 pushes positive = lunging) alternating with
    # a tense pulled-back coil (j2 snaps negative). j1 swings the base side to
    # side so the whole arm thrashes. j7 stays rigid throughout — no limp wrist
    # here, pure clenched tension. Ends with one big held-forward glare, then a
    # slow reluctant return to home.
    'angry': {
        'description': 'Tense coiling and sharp forward jabs with side-to-side thrashing',
        'waypoints': [
            # Coil back — arm pulls up and tight, ready to explode
            [ 0.0,  -0.80,  0.0,  -1.40,  0.0,  -1.05,  1.57],  # coil up, tense
            # Jab 1 — lunge forward-right
            [ 0.25,  0.20,  0.0,  -1.00,  0.0,  -0.80,  1.57],  # jab right
            # Snap back left
            [-0.25, -0.75,  0.0,  -1.35,  0.0,  -1.05,  1.57],  # recoil left
            # Jab 2 — lunge forward-left
            [-0.25,  0.20,  0.0,  -1.00,  0.0,  -0.80,  1.57],  # jab left
            # Snap back right
            [ 0.25, -0.75,  0.0,  -1.35,  0.0,  -1.05,  1.57],  # recoil right
            # Jab 3 — hard lunge center
            [ 0.0,   0.30,  0.0,  -0.90,  0.0,  -0.75,  1.57],  # jab center hard
            # Snap back center, even more coiled
            [ 0.0,  -0.90,  0.0,  -1.45,  0.0,  -1.05,  1.57],  # coil back hard
            # Final glare — extend forward and hold, seething
            [ 0.0,   0.15,  0.0,  -1.05,  0.0,  -0.85,  1.57],  # hold forward glare
            [ 0.0,   0.15,  0.0,  -1.05,  0.0,  -0.85,  1.57],  # seethe...
            HOME,                                                  # reluctant stand-down
        ],
        'times': [4.0, 6.5, 9.0, 11.5, 14.0, 16.5, 19.0, 22.0, 27.0, 33.0],
    },


    # 💀  Dead
    # Arm snaps immediately to full upright (j2 very negative, j4 near 0),
    # holds briefly, then droops in slow progressive stages — wrist rolls
    # first (j7), then elbow buckles (j4), then shoulder tips forward (j2
    # goes positive) until the arm hangs completely limp.
    'dead': {
        'description': 'Arm snaps upright then droops progressively until fully limp',
        'waypoints': [
            [0.0,  -1.30,  0.0,  -0.20,  0.0,  -0.80,  1.57],  # snap to full upright
            [0.0,  -1.30,  0.0,  -0.20,  0.0,  -0.80,  1.57],  # hold at peak — last moment
            [0.0,  -1.30,  0.0,  -0.20,  0.0,  -0.80,  2.80],  # wrist rolls limp (j7)
            [0.0,  -1.30,  0.0,  -0.55,  0.0,  -0.80,  2.80],  # elbow starts to buckle (j4)
            [0.0,  -1.00,  0.0,  -0.90,  0.0,  -0.80,  2.80],  # shoulder begins to drop (j2)
            [0.0,  -0.60,  0.0,  -1.10,  0.0,  -0.50,  2.80],  # continuing to slump
            [0.0,   0.10,  0.0,  -0.80,  0.0,  -0.20,  2.80],  # shoulder tips forward
            [0.0,   0.40,  0.0,  -0.40,  0.0,   0.00,  2.60],  # full dead hang
            [0.0,   0.40,  0.0,  -0.40,  0.0,   0.00,  2.60],  # hold, lifeless
            HOME,                                                 # fade out / reset
        ],
        'times': [2.5, 6.0, 10.0, 14.5, 19.0, 23.5, 28.0, 32.5, 37.0, 43.0],
    },


    #  😳 flushed-face
    # Big sweeping raise overhead, wrist spins with joy, arm pumps up and down
    # twice in triumph, then glides back to home.
    'flushed-face': {
        'description': 'Triumphant overhead raise, joyful wrist spin, double victory pump',
        'waypoints': [
            [0.0,  -0.80,  0.0,  -1.80,  0.0,  -1.30,  1.57],  # sweep upward
            [0.0,  -0.90,  0.0,  -2.00,  0.0,  -1.30,  0.50],  # spin wrist (start)
            [0.0,  -0.90,  0.0,  -2.00,  0.0,  -1.30,  3.20],  # spin wrist (end)
            [0.0,  -0.75,  0.0,  -1.85,  0.0,  -1.30,  1.57],  # pump down
            [0.0,  -0.95,  0.0,  -2.00,  0.0,  -1.30,  1.57],  # pump up
            [0.0,  -0.75,  0.0,  -1.85,  0.0,  -1.30,  1.57],  # pump down
            [0.0,  -0.95,  0.0,  -2.00,  0.0,  -1.30,  1.57],  # pump up high
            HOME,                                                 # return home
        ],
        'times': [4.5, 7.5, 10.5, 14.0, 17.5, 21.0, 24.5, 29.5],
    },

}
# ──────────────────────────────────────────────────────────────────────────────


class MotionPlayer(Node):

    def __init__(self):
        super().__init__('motion_player')

        self._action_client = ActionClient(
            self,
            FollowJointTrajectory,
            '/joint_trajectory_controller/follow_joint_trajectory'
        )

        self._busy = False  # guard so overlapping messages don't stack up

        self._subscription = self.create_subscription(
            String,
            'emoji_action',
            self._emoji_callback,
            10
        )

        self.get_logger().info(
            f'Listening on /emoji_action. Valid motions: {", ".join(MOTIONS.keys())}'
        )

    def _emoji_callback(self, msg: String):
        motion_name = msg.data.strip().lower()

        if self._busy:
            self.get_logger().warn(
                f'Motion already in progress — ignoring "{motion_name}"'
            )
            return

        if motion_name not in MOTIONS:
            self.get_logger().warn(
                f'Unknown motion: "{motion_name}". '
                f'Valid options: {", ".join(MOTIONS.keys())}'
            )
            return

        self.get_logger().info(
            f'Received "{motion_name}": {MOTIONS[motion_name]["description"]}'
        )
        self._busy = True
        self._send_trajectory(motion_name)

    def _send_trajectory(self, motion_name: str):
        motion = MOTIONS[motion_name]

        trajectory = JointTrajectory()
        trajectory.joint_names = JOINT_NAMES

        for positions, t in zip(motion['waypoints'], motion['times']):
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

        self.get_logger().info('Waiting for action server...')
        self._action_client.wait_for_server()

        future = self._action_client.send_goal_async(
            goal,
            feedback_callback=self._feedback_callback
        )
        future.add_done_callback(self._goal_response_callback)

    def _goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().error('Goal REJECTED by controller.')
            self._busy = False
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
            self.get_logger().info('Motion complete — ready for next command.')
        else:
            self.get_logger().error(
                f'Motion failed with error code: {result.error_code}'
            )
        self._busy = False  # ready for next message


def main(args=None):
    rclpy.init(args=args)
    node = MotionPlayer()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()