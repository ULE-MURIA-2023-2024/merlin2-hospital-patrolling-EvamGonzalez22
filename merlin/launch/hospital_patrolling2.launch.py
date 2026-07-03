import os
from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    pkg_dir = get_package_share_directory('merlin2_hospital_patrolling')
    waypoints_file = os.path.join(pkg_dir, 'params', 'stretcher_room_waypoints.yaml')

    return LaunchDescription([
        Node(package="merlin2_hospital_patrolling", executable="patrol_action_node", name="patrol_action_node", output="screen"),
        Node(package="merlin2_hospital_patrolling", executable="mission_node", name="mission_node", parameters=[waypoints_file], output="screen")
    ])
