# Copyright (c) 2025-2026, AGH Center of Excellence in Artificial Intelligence
# All rights reserved.
#
# SPDX-License-Identifier: Apache-2.0

import asyncio
from wled import WLED
import rclpy
from rclpy.node import Node
from wled_interfaces.srv import ChangeScene, DefineScene, GetScenes, GetSections
from wled_ros_driver.scene_data import SceneData
from wled_ros_driver.scene_function import SceneFunction
from wled_ros_driver.section_data import SectionData
from wled_ros_driver.run_lights_data import RunLightsData

from rcl_interfaces.msg import SetParametersResult
from dataclasses import asdict


class AsyncServiceWledNode(Node):
    """
    ROS 2 node providing an asynchronous service interface for controlling WLED devices.

    - Handles requests to change LED scenes and parameters via the 'wled_scene_change' service.
    - Supports predefined and custom scenes with adjustable brightness, color, and LED range.
    - Communicates with WLED devices using the WLED Python API.
    - Provides utility methods for parsing requests, parameters, and fetching device info.
    """

    def __init__(self):
        """
        Initializes the AsyncServiceWledNode.

        - Sets the node name to 'wled_service_node'.
        - Calls function to get parameters provided in .yaml file
        - Sets callback function meant to update function internal variables when ros parameter is changed
        - Creates the 'wled_scene_change' service using the ChangeScene interface.
        - Registers the _handle_service method as the service callback.
        - Logs a message indicating the service node has started.
        """

        super().__init__(
            "wled_service_node",
            allow_undeclared_parameters=True,
            automatically_declare_parameters_from_overrides=True,
        )

        self._load_variables()
        self.add_on_set_parameters_callback(self._parameter_callback)

        self.srv_change_scene = self.create_service(
            ChangeScene, "wled_scene_change", self._handle_change_scene
        )

        self.srv_define_scene = self.create_service(
            DefineScene, "wled_define_scene", self._handle_define_scene
        )

        self.srv_get_scenes = self.create_service(
            GetScenes, "wled_get_scenes", self._handle_get_scenes
        )

        self.srv_get_sections = self.create_service(
            GetSections, "wled_get_sections", self._handle_get_sections
        )

        self.get_logger().info("Async service node started")
        self.get_logger().info("IP address " + self.wled_url)

    def _load_variables(self):
        """
        Loads data provided by ROS via YAML file
        """
        self.wled_url = (
            self.get_parameter("wled_url").get_parameter_value().string_value
        )
        self.led_count = (
            self.get_parameter("led_count").get_parameter_value().integer_value
        )

        loaded_scenes = {}
        scenes_params = self.get_parameters_by_prefix("scenes")
        for key, param in scenes_params.items():
            scene_name, scene_parameter = key.split(".")
            if scene_name not in loaded_scenes:
                loaded_scenes[scene_name] = {}
            loaded_scenes[scene_name][scene_parameter] = param.value
        self.scenes = {}
        for scene_name in loaded_scenes.keys():
            self.scenes[scene_name] = SceneData(**loaded_scenes[scene_name])

        loaded_sections = {}
        sections_params = self.get_parameters_by_prefix("sections")
        for key, param in sections_params.items():
            section_name, section_parameter = key.split(".")
            if section_name not in loaded_sections:
                loaded_sections[section_name] = {}
            loaded_sections[section_name][section_parameter] = param.value
        self.sections = {}
        for section_name in loaded_sections.keys():
            self.sections[section_name] = SectionData(**loaded_sections[section_name])

    def _parameter_callback(self, params: dict) -> SetParametersResult:
        """
        Callback function triggered every time ROS parameter is changed while node is running.
        """
        for param in params:
            self.get_logger().info("param name " + param.name)

            if param.name == "wled_url":
                self.wled_url = param.value
                self.get_logger().info("Updated led ip: " + self.wled_url)
            if param.name == "led_count":
                self.led_count = param.value
                self.get_logger().info("Updated led number: " + self.wled_url)

            if param.name.startswith("scenes."):
                values = param.name.split(".")
                self.get_logger().info(f"values : {values}")

                if len(values) == 3:
                    _, scene_name, param_name = values
                    if scene_name not in self.scenes:
                        return SetParametersResult(successful=False)
                    edited_scene = asdict(self.scenes[scene_name])
                    edited_scene[param_name] = param.value
                    self.scenes[scene_name] = SceneData(**edited_scene)

                else:
                    return SetParametersResult(successful=False)

            if param.name.startswith("sections."):
                values = param.name.split(".")
                self.get_logger().info(f"values : {values}")

                if len(values) == 3:
                    _, section_name, param_name = values
                    if section_name not in self.sections:
                        return SetParametersResult(successful=False)
                    edited_section = asdict(self.sections[section_name])
                    edited_section[param_name] = param.value
                    self.sections[section_name] = SectionData(**edited_section)

                else:
                    return SetParametersResult(successful=False)

        return SetParametersResult(successful=True)

    async def wled_info(self):
        """
        Asynchronous method to fetch and log WLED device information.

        - Connects to the WLED device using the provided URL.
        - Retrieves the latest device state and information.
        - Logs the firmware version for debugging and verification.

        Returns:
            None
        """
        try:
            async with WLED(self.wled_url) as led:
                device = await led.update()
                self.get_logger().info(f"WLED firmware version: {device.info.version}")
        except Exception as e:
            self.get_logger().error(f"Failed to fetch WLED info: {e}")

    async def scene_x(self, pars: RunLightsData) -> tuple[bool, str]:
        """
        Asynchronous method to set a custom LED scene using the WLED API.

        - Logs the received parameters for debugging.
        - Sends the segment configuration to the WLED device.
        - Turns on the master switch for LEDs.

        Args:
            pars (dict): Dictionary containing following parameters: brightness, start, stop, color[red, green, blue].

        Returns:
            str: Confirmation message indicating the scene was set.
        """
        self.get_logger().info(f"{pars}")
        try:
            async with WLED(self.wled_url) as led:
                await led.segment(
                    on=True,
                    brightness=pars.brightness,
                    segment_id=0,
                    start=pars.start,
                    stop=pars.stop,
                    color_primary=pars.color,
                    transition=1,
                )
                await led.master(on=True)
            return True, "Scene complete"
        except Exception as e:
            self.get_logger().error(f"Failed to fetch WLED info: {e}")
            return False, "Failed to execute scene"

    async def scene_off(self, _pars: RunLightsData) -> tuple[bool, str]:
        """
        Asynchronous method to turn off all LEDs using the WLED API.

        Args:
            _: Unused parameter, kept for interface consistency.

        Returns:
            str: Confirmation message indicating the scene is turned off.
        """
        try:
            async with WLED(self.wled_url) as led:
                await led.master(on=False)
            return True, "Scene 'OFF' complete"
        except Exception as e:
            self.get_logger().error(f"Failed to fetch WLED info: {e}")
            return False, "Failed to execute scene 'OFF'"

    def _handle_change_scene(
        self, request: ChangeScene.Request, response: ChangeScene.Response
    ) -> object:
        """
        Synchronous service handler for ROS 2 service requests.
        Runs the asynchronous process_request method using the event loop,
        sets the response fields, and returns the response.

        Args:
            request: The incoming service request object.
            response: The service response object to populate.

        Returns:
            response: The populated response object with success and message.
        """
        # Use asyncio to run the async handler
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(self._process_request(request))
        response.success = result[0]
        response.message = result[1]
        return response

    def _handle_get_scenes(
        self, request: GetScenes.Request, response: GetScenes.Response
    ) -> object:
        """
        Synchronous service handler for ROS 2 service requests.
        Returns the lists of currently configured scenes's parmeters (lists of scene names, brightnesses and separate RGB values).
        """
        self.get_logger().info("GetScenes service called")

        scene_names = []
        brightnesses = []
        colors_r = []
        colors_g = []
        colors_b = []

        for name, data in self.scenes.items():
            scene_names.append(name)
            brightnesses.append(int(data.brightness))
            colors_r.append(int(data.color[0]))
            colors_g.append(int(data.color[1]))
            colors_b.append(int(data.color[2]))

        response.scene_names = scene_names
        response.brightnesses = brightnesses
        response.colors_r = colors_r
        response.colors_g = colors_g
        response.colors_b = colors_b

        return response

    def _handle_get_sections(
        self, request: GetSections.Request, response: GetSections.Response
    ) -> object:
        """
        Synchronous service handler for ROS 2 service requests.
        Returns the lists of currently configured scetion's parmeters (lists of section names, starts and stops).
        """
        self.get_logger().info("GetSections service called")

        section_names = []
        starts = []
        stops = []

        for name, data in self.sections.items():
            section_names.append(name)
            starts.append(int(data.start))
            stops.append(int(data.stop))

        response.section_names = section_names
        response.starts = starts
        response.stops = stops

        return response

    def _handle_define_scene(
        self, request: DefineScene.Request, response: DefineScene.Response
    ) -> object:
        """
        Synchronous service handler for ROS 2 service requests.
        Dynamically registers or redefines a scene configuration during runtime.
        """
        name = request.scene_name
        self.get_logger().info(f"DefineScene called for scene: {name}")

        try:
            self.scenes[name] = SceneData(
                color=list(request.color), brightness=int(request.brightness)
            )
            response.success = True
            response.message = f"Scene '{name}' successfully defined/updated."
            self.get_logger().info(response.message)
        except Exception as e:
            response.success = False
            response.message = f"Failed to define/update scene: {str(e)}"
            self.get_logger().error(response.message)
        return response

    async def _process_request(self, request: ChangeScene.Request) -> tuple[bool, str]:
        """
        Asynchronous handler for processing incoming service requests.

        - Logs the requested scene and parameters.
        - Determines the correct scene method and parameters using the _prepare_request_params function.
        - Calls the appropriate async scene method with the parameters.
        - Returns the result from the scene method.

        Args:
            request: The service request object containing 'scene' and 'optional_params'.

        Returns:
            result: The result string from the executed scene method.
        """
        METHODS_MAP = {
            SceneFunction.CHANGE_SCENE: self.scene_x,
            SceneFunction.SCENE_OFF: self.scene_off,
        }

        self.get_logger().info(
            f"Requested scene: {request.scene} | section:{request.section} | params: {request.optional_params}"
        )

        params = self._prepare_request_params(request)

        return await METHODS_MAP[params.scene_function](params)

    def _prepare_request_params(self, request: ChangeScene.Request) -> RunLightsData:
        """
        Extracts and normalizes the requested scene and section name from the service request.
        If not recognized, default values are scene_off and section_all.
        It returns RunLightsData object that contains all necessary data to run selected led configuration

        Args:
            request: The service request object containing the 'scene' attribute.

        Returns:
            RunLightsData: Object containing brightness, color, start, stop, and function to run leds.
        """

        scene_key = (
            request.scene.lower()
            if hasattr(request, "scene") and request.scene
            else "scene_off"
        )
        section_key = (
            request.section.lower()
            if hasattr(request, "section") and request.section
            else "section_all"
        )
        self.get_logger().info(f"section_key: {section_key}")

        if scene_key == "scene_custom":
            scene_function = SceneFunction.CHANGE_SCENE
            scene_data = self._parse_scene_params(request.optional_params.split())

        elif scene_key == "scene_off":
            scene_function = SceneFunction.SCENE_OFF
            scene_data = {"brightness": 0, "color": [0, 0, 0]}

        elif scene_key in self.scenes.keys():
            scene_function = SceneFunction.CHANGE_SCENE
            scene_data = asdict(self.scenes[scene_key])
        else:
            scene_function = SceneFunction.SCENE_OFF
            scene_data = asdict(self.scenes[scene_key])

        if section_key == "section_custom":
            section_data = self._parse_section_params(request.optional_params.split())
        elif section_key == "section_all":
            section_data = {"start": 0, "stop": self.led_count}
        elif section_key in self.sections.keys():
            section_data = asdict(self.sections[section_key])
        else:
            section_data = {"start": 0, "stop": self.led_count}

        return RunLightsData(
            scene_function=scene_function, **scene_data, **section_data
        )

    def _parse_scene_params(self, params_list: list) -> dict:
        """
        Parse a list of string parameters to create scene data.

        Parameters (all optional, default values used if missing or invalid):
            params_list[0]: brightness (int, default 255)
            params_list[3]: red color value (int, default 255)
            params_list[4]: green color value (int, default 255)
            params_list[5]: blue color value (int, default 255)

        Returns:
        {
            brightness: (int),
            color: (array of 3 ints: (red, green, blue))
        }

        """

        scene_params = {}

        # placeholder function to allow for custom scene with lower number of parameters
        # to be replaces with custom service
        if len(params_list) == 4:
            params_list.extend([None] * (6 - len(params_list)))

            params_list[5] = params_list[3]
            params_list[4] = params_list[2]
            params_list[3] = params_list[1]

        try:
            scene_params["brightness"] = (
                int(params_list[0]) if len(params_list) > 0 else 255
            )
            color_red = int(params_list[3]) if len(params_list) > 3 else 255
            color_green = int(params_list[4]) if len(params_list) > 4 else 255
            color_blue = int(params_list[5]) if len(params_list) > 5 else 255
            scene_params["color"] = [color_red, color_green, color_blue]
        except ValueError:
            return {"brightness": 255, "color": [127, 127, 63]}

        return scene_params

    def _parse_section_params(self, params_list: list) -> dict:
        """
        Parse a list of string parameters to create section data.

        Parameters (all optional, default values used if missing or invalid):
            params_list[1]: start LED index (int, default 0)
            params_list[2]: stop LED index (int, default self.led_count)

        Returns:
        {
            start: (int),
            stop: (int)
        }

        """

        # placeholder function to allow for custom section with lower number of parameters
        # to be replaces with custom service
        if len(params_list) == 2:
            params_list.extend([None] * (6 - len(params_list)))

            params_list[2] = params_list[1]
            params_list[1] = params_list[0]

        section_params = {}

        try:
            section_params["start"] = (
                int(params_list[1])
                if len(params_list) > 1 and int(params_list[1]) > 0
                else 0
            )
            section_params["stop"] = (
                int(params_list[2])
                if len(params_list) > 2 and int(params_list[2]) < self.led_count
                else self.led_count
            )
        except ValueError:
            self.get_logger().info("err0r")

            return {"start": 0, "stop": self.led_count}

        return section_params


def main(args=None):
    """
    Entry point for the ROS 2 node.

    - Initializes the ROS 2 Python client library.
    - Creates an instance of AsyncServiceWledNode.
    - Spins the node to process incoming service requests.
    - Handles graceful shutdown on keyboard interrupt.
    """
    rclpy.init(args=args)
    node = AsyncServiceWledNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    # Executes the main function when the script is run directly
    main()
