from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():

    input_file_arg = DeclareLaunchArgument(
        'input_file',
        default_value='~/ros2_ws/src/AZ_demo/recorded_trajectories/trajectory.json',
        description='Path to the trajectory JSON file to execute'
    )

    robot_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('kinova_gen3_7dof_robotiq_2f_85_moveit_config'),
                'launch',
                'robot.launch.py'
            )
        ),
        launch_arguments={
            'use_fake_hardware': 'true',
            'robot_ip': 'yyy.yyy.yyy.yyy'
        }.items()
    )

    trajectory_executor = Node(
        package='AZ_demo',
        executable='execute_trajectory',
        name='execute_trajectory',
        output='screen',
        arguments=[LaunchConfiguration('input_file')]
    )

    return LaunchDescription([
        input_file_arg,
        robot_launch,
        trajectory_executor,
    ])