import os
from launch import LaunchDescription
from launch.actions import ExecuteProcess, IncludeLaunchDescription
from launch.launch_description_sources import AnyLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    rosbridge_launch = IncludeLaunchDescription(
        AnyLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('rosbridge_server'),
                'launch',
                'rosbridge_websocket_launch.xml'
            )
        ),
        launch_arguments={
            'address': '0.0.0.0',
            'port': '9090'
        }.items()
    )

    web_server = ExecuteProcess(
        cmd=['python3', '-m', 'http.server', '8000', '--bind', '0.0.0.0'],
        cwd='/home/mavis/ros2_ws/src/AZ_demo/emojis',
        output='screen'
    )

    return LaunchDescription([
        rosbridge_launch,
        web_server,
    ])