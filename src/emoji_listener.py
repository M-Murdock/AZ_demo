#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class EmojiActionSubscriber(Node):

    def __init__(self):
        super().__init__('emoji_action_subscriber')
        self.subscription = self.create_subscription(
            String,
            '/emoji_action',
            self.callback,
            10
        )

    def callback(self, msg):
        print(f'Received action: {msg.data}')


def main(args=None):
    rclpy.init(args=args)
    node = EmojiActionSubscriber()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()