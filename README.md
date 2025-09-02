# wled_ros_driver
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)


Package for controlling [WLED](https://know.wled.ge/) project using ROS 2 stack. The package was created to integrate the lights controller with experiments involving a robotic manipulator and tool cameras.

Originally developed for integration with Robotic Manipulator with tool cameras, [AEGIS_ROS](https://github.com/AGH-CEAI/aegis_ros) and ROS 2 Humble.

It is possible to modify this repository to fit your needs. **PRs are welcome!**

## Quick Start

Get you WLED controller, compatible led stripes and power supply. Connect electrically, power on and configure:
- IP address
- Number of leds
- Segment 0 in UI

Make sure the system works using UI provided by WLED Project.

### Setup

1. Download repo and build package
```bash
source /opt/ros/humble/setup.sh
git clone git@github.com:AGH-CEAI/wled_ros_driver.git
colcon build --symlink-install
source ./install/local_setup.sh
```

### Test

1. Start the server
```bash
ros2 run wled_ros_driver start_wled_service
```
2. Call the commands (another terminal)
```bash
source ./install/setup.sh
python3 src/wled_ros_driver/wled_ros_driver/wled_ros_driver/wled_client.py scene_1
python3 src/wled_ros_driver/wled_ros_driver/wled_ros_driver/wled_client.py scene_off
```

You should see LEDs turn on and off.

### Available scenes

You may pick between the following scenarios:
| Argument | Description |
| --- | --- |
| `scene_1` | All leds, white, 100% brightness |
| `scene_2` | All leds, white, 75% brightness |
| `scene_3` | All leds, white, 50% brightness |
| `scene_4` | All leds, white, 25% brightness |
| `scene_off` | Led off |
| `scene_custom`  | custom led range, custom color, custom brightness |

## License

This repository is licensed under the Apache 2.0, see LICENSE for details.
