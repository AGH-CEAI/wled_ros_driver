# Copyright (c) 2025-2026, AGH Center of Excellence in Artificial Intelligence
# All rights reserved.
#
# SPDX-License-Identifier: Apache-2.0
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description() -> LaunchDescription:

    config_file_arg = DeclareLaunchArgument(
        "config",
        default_value=PathJoinSubstitution(
            [FindPackageShare("wled_ros_driver"), "config", "scenes.yaml"]
        ),
        description="Path to the custom YAML configuration file for WLED service.",
    )

    config_file = LaunchConfiguration("config")

    wled_service_node = Node(
        package="wled_ros_driver",
        executable="start_wled_service",
        name="wled_service_node",
        output="screen",
        parameters=[config_file],
    )

    return LaunchDescription(
        [
            config_file_arg,
            wled_service_node,
        ]
    )
