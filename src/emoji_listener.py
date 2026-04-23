#!/usr/bin/env python3
"""emoji_action_server.py — listens on /emoji_action and dispatches pre-recorded actions."""

import rospy
from std_msgs.msg import String

# Map action_id strings → your actual execution functions
ACTION_REGISTRY = {}

def register(action_id):
    """Decorator to register a function as a named action."""
    def decorator(fn):
        ACTION_REGISTRY[action_id] = fn
        return fn
    return decorator

# ── Register your pre-recorded actions here ──────────────────────────────────

@register("wave")
def action_wave():
    rospy.loginfo("Executing: wave")
    # e.g. call your MoveIt / Kortex action client here

@register("handshake")
def action_handshake():
    rospy.loginfo("Executing: handshake")

@register("high_five")
def action_high_five():
    rospy.loginfo("Executing: high_five")

@register("clap")
def action_clap():
    rospy.loginfo("Executing: clap")

@register("point_down")
def action_point_down():
    rospy.loginfo("Executing: point_down")

@register("point_up")
def action_point_up():
    rospy.loginfo("Executing: point_up")

@register("home")
def action_home():
    rospy.loginfo("Executing: home")

@register("reset")
def action_reset():
    rospy.loginfo("Executing: reset")

@register("pick_box")
def action_pick_box():
    rospy.loginfo("Executing: pick_box")

@register("pour_drink")
def action_pour_drink():
    rospy.loginfo("Executing: pour_drink")

@register("write")
def action_write():
    rospy.loginfo("Executing: write")

@register("trash_toss")
def action_trash_toss():
    rospy.loginfo("Executing: trash_toss")

# ── Subscriber callback ───────────────────────────────────────────────────────

def on_emoji_action(msg):
    action_id = msg.data.strip()
    fn = ACTION_REGISTRY.get(action_id)
    if fn:
        rospy.loginfo(f"[emoji_action] Dispatching '{action_id}'")
        fn()
    else:
        rospy.logwarn(f"[emoji_action] Unknown action_id: '{action_id}'")

if __name__ == "__main__":
    rospy.init_node("emoji_action_server")
    rospy.Subscriber("/emoji_action", String, on_emoji_action)
    rospy.loginfo("emoji_action_server ready — waiting for actions…")
    rospy.spin()