from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():

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

    # joint_states_listener = Node(
    #     package='AZ_demo',
    #     executable='get_joints',
    #     name='get_joints',
    #     output='screen'
    # )

    trajectory_executor = Node(
        package='AZ_demo',
        executable='execute_trajectory',
        name='execute_trajectory',
        output='screen'
    )

    return LaunchDescription([
        robot_launch,
        # joint_states_listener,
        trajectory_executor,
    ])