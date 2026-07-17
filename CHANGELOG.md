# Changelog

All notable changes to the `wled_ros_driver` package will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

* [PR-13](https://github.com/AGH-CEAI/wled_ros_driver/pull/13) Added ROS 2 launch file (`wled_service.launch.py`) to automate node startup and parameters injection.
* [PR-1](https://github.com/AGH-CEAI/wled_ros_driver/pull/1) - Basic scene functionalities in ROS2 node.

### Changed

* Updated installation setup (`setup.py`) to correctly install launch and configuration files into the ROS 2 workspace share directory.
* Updated `README.md` with instructions on how to use the new launch file
* [PR-9](https://github.com/AGH-CEAI/wled_ros_driver/pull/9) - Moved hardcoded scene and ip variables to .yaml file.
* [PR-4](https://github.com/AGH-CEAI/wled_ros_driver/pull/4) - Separated led control into sections and scenes.

### Deprecated
### Removed
### Fixed
### Security
