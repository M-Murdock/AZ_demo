from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
from moveit_configs_utils import MoveItConfigsBuilder
import os

def generate_launch_description():
    moveit_config = (
        MoveItConfigsBuilder('gen3', package_name='kinova_gen3_7dof_robotiq_2f_85_moveit_config')
        .robot_description()
        .robot_description_semantic()
        .robot_description_kinematics()
        .to_moveit_configs()
    )

    robot_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('kortex_bringup'),
                'launch',
                'gen3.launch.py'
            )
        ),
        launch_arguments={
            'use_fake_hardware': 'false',
            'robot_ip': '192.168.1.10',  # fixed
            'gripper': 'robotiq_2f_85',
            'robot_controller': 'twist_controller',
            'launch_rviz': 'false',
        }.items()
    )


    emoji = Node(
        package='AZ_demo',
        executable='emoji_listener',
        name='emoji_listener',
        output='screen'
    )

    return LaunchDescription([
        robot_launch,
        emoji_listener,
    ])