# wled_ros_driver

[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Licence](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)
[![prek](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/j178/prek/master/docs/assets/badge-v0.json)](https://github.com/j178/prek)


Package for controlling [WLED](https://know.wled.ge/) project using ROS 2 stack. The package was created to integrate the lights controller with experiments involving a robotic manipulator and tool cameras.

Originally developed for integration with Robotic Manipulator with tool cameras, [AEGIS_ROS](https://github.com/AGH-CEAI/aegis_ros) and ROS 2 Humble.

It is possible to modify this repository to fit your needs. **PRs are welcome!**

## Quick Start

Get you WLED controller, compatible led stripes and power supply. Connect electrically, power on and configure:
- IP address
- Number of leds
- All segments you want to control separately

Make sure the system works using UI provided by WLED Project.

### Setup

1. Download repo and build package
```bash
source /opt/ros/humble/setup.sh
git clone git@github.com:AGH-CEAI/wled_ros_driver.git
colcon build --symlink-install
source ./install/setup.bash
```

### Test

1.Configure your WLED IP address and scene parameters in the configuration file:
```
wled_ros_driver/config/scenes.yaml
```
2. Start the server using the launch file:
```bash
ros2 launch wled_ros_driver wled_service.launch.py
```
3. Call the commands (another terminal)
```bash
source ./install/setup.sh
```
Usage examples:
```bash
python3 src/wled_ros_driver/wled_ros_driver/wled_ros_driver/wled_client.py <scene> <section> <effect_id> <params (optional, only fi scene_custom selected)>

python3 src/wled_ros_driver/wled_ros_driver/wled_ros_driver/wled_client.py scene_1 section_1 0
python3 src/wled_ros_driver/wled_ros_driver/wled_ros_driver/wled_client.py scene_custom section_1 1 "255 255 127 127" (brightness red green blue)
python3 src/wled_ros_driver/wled_ros_driver/wled_ros_driver/wled_client.py scene_off section_1
```
or by using ros2 service:
```bash
source ./install/setup.sh
```
Usage examples:
```bash
ros2 service call /wled_scene_change wled_interfaces/srv/ChangeScene "{scene: 'scene_1', section: 'section_1' effect_id: 0}"
ros2 service call /wled_scene_change wled_interfaces/srv/ChangeScene "{scene: 'scene_custom', section: 'section_1', effect_id: 1, optional_params: '255 127 127 63'}"

ros2 service call /wled_scene_change wled_interfaces/srv/ChangeScene "{scene: 'scene_off', section: 'section_1'}"
```

You should see LEDs turn on and off.

### Available scenes

You may pick between the following scenarios:
| Argument | Description |
| --- | --- |
| `scene_1` | Led red, 100% brightness |
| `scene_2` | Led green, 100% brightness |
| `scene_3` | Led blue, 50% brightness |
| `scene_4` | Led yellow, 50% brightness |
| `scene_off` | Led off |
| `scene_custom`  | custom color, custom brightness |

### Custom scene parameters

For `scene_custom`, pass the parameters as space-separated values:

```
brightness color_red color_green color_blue
```

**Example:**
```
255 127 127 63
```

---

## Development notes

### pre-commit
This project uses various tools for aiding the quality of the source code. Currently most of them are executed by the `pre-commit`. As a faster alternative it is suggested to use `prek`. Please make sure to enable its hooks:

```bash
# In case of pre-commit
pre-commit install
# In case of prek
prek install
```

## License

This repository is licensed under the Apache 2.0, see LICENSE for details.
