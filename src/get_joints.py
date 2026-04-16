#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState


class JointStatesListener(Node):

    def __init__(self):
        super().__init__('joint_states_listener')
        self.subscription = self.create_subscription(
            JointState,
            '/joint_states',
            self.joint_states_callback,
            10  # QoS queue depth
        )
        self.get_logger().info("Listening on /joint_states ...")

    def joint_states_callback(self, msg):
        self.get_logger().info("--- Joint States ---")
        for i, name in enumerate(msg.name):
            position = msg.position[i] if i < len(msg.position) else "N/A"
            velocity = msg.velocity[i] if i < len(msg.velocity) else "N/A"
            effort   = msg.effort[i]   if i < len(msg.effort)   else "N/A"
            self.get_logger().info(
                f"  {name}: pos={position:.4f}, vel={velocity:.4f}, eff={effort:.4f}"
            )


def main(args=None):
    print("HELLO WORLD")
    rclpy.init(args=args)
    node = JointStatesListener()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()