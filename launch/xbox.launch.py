from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument, TimerAction
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
            'robot_ip': '192.168.1.10',
            'gripper': 'robotiq_2f_85',
            'robot_controller': 'twist_controller',
            'launch_rviz': 'false',
        }.items()
    )

    controller_arg = DeclareLaunchArgument('controller', default_value='xbox')

    # Deactivate joint_trajectory_controller and activate twist_controller
    switch_controller = TimerAction(
        period=5.0,  # wait for ros2_control to finish loading
        actions=[
            Node(
                package='controller_manager',
                executable='spawner',
                arguments=[
                    'twist_controller',
                    '--activate-as-group',
                    '--deactivate',
                    'joint_trajectory_controller',
                ],
                output='screen',
            )
        ]
    )

    joy_teleop = Node(
        package='AZ_demo',
        executable='joy_teleop',
        arguments=[LaunchConfiguration('controller')],
        name='joy_teleop',
        output='screen'
    )

    return LaunchDescription([
        controller_arg,
        robot_launch,
        switch_controller,
        joy_teleop,
    ])