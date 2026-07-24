# Changelog

All notable changes to the `wled_ros_driver` package will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
* [PR-18](https://github.com/AGH-CEAI/wled_ros_driver/pull/18) Added support for displaying effects form WLED controller.
* [PR-16](https://github.com/AGH-CEAI/wled_ros_driver/pull/16) - New ROS 2 services in `wled_interfaces/srv`: `DefineScene.srv`, `GetScenes.srv` and `GetSections.srv` for interaction with the WLED server.
* [PR-13](https://github.com/AGH-CEAI/wled_ros_driver/pull/13) - ROS 2 launch file (`wled_service.launch.py`) to automate node startup and parameters injection.
* [PR-1](https://github.com/AGH-CEAI/wled_ros_driver/pull/1) - Basic scene functionalities in ROS2 node.

### Changed
* [PR-15](https://github.com/AGH-CEAI/wled_ros_driver/pull/15) - Separated led control into sections and scenes.
* [PR-14](https://github.com/AGH-CEAI/wled_ros_driver/pull/14) - Fixed errors that prevented from changing scenes after setting custom scene.
* [PR-13](https://github.com/AGH-CEAI/wled_ros_driver/pull/13) - Updated installation setup (`setup.py`) to correctly install launch and configuration files into the ROS 2 workspace share directory, updated `README.md` with instructions on how to use the new launch file
* [PR-9](https://github.com/AGH-CEAI/wled_ros_driver/pull/9) - Moved hardcoded scene and ip variables to .yaml file.

### Deprecated
### Removed
### Fixed
### Security
