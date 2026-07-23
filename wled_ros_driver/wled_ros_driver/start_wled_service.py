# Copyright (c) 2025-2026, AGH Center of Excellence in Artificial Intelligence
# All rights reserved.
#
# SPDX-License-Identifier: Apache-2.0

import asyncio
from wled import WLED
import rclpy
from rclpy.node import Node
from wled_interfaces.srv import ChangeScene, DefineScene, GetScenes, GetSections
from wled_ros_driver.types import (
    SceneData,
    SceneFunction,
    SectionData,
    RunLightsData,
    Color,
)
from wled_ros_driver.config.ros_params import RosParams
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
        - Creates the 'wled_change_scene' service using the ChangeScene interface.
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
            ChangeScene, RosParams.CHANGE_SCENE_SERVICE_NAME, self._handle_change_scene
        )

        self.srv_define_scene = self.create_service(
            DefineScene, RosParams.DEFINE_SCENE_SERVICE_NAME, self._handle_define_scene
        )

        self.srv_get_scenes = self.create_service(
            GetScenes, RosParams.GET_SCENES_SERVICE_NAME, self._handle_get_scenes
        )

        self.srv_get_sections = self.create_service(
            GetSections, RosParams.GET_SECTIONS_SERVICE_NAME, self._handle_get_sections
        )

        self.get_logger().info("Async service node started")
        self.get_logger().info("IP address " + self.wled_url)

    def _load_variables(self):
        """
        Loads data provided by ROS via YAML file
        """

        self.wled_url = (
            self.get_parameter(RosParams.WLED_CONTROLLER_URL)
            .get_parameter_value()
            .string_value
        )
        self.led_count = (
            self.get_parameter(RosParams.WLED_SEGMENTS_COUNT)
            .get_parameter_value()
            .integer_value
        )
        loop = asyncio.get_event_loop()
        self.sections = loop.run_until_complete(
            self._load_segments_from_wled_controller(self.wled_url)
        )

        loaded_scenes = {}
        scenes_params = self.get_parameters_by_prefix(RosParams.SCENES_YAML_NAME)
        for key, param in scenes_params.items():
            scene_name, scene_parameter = key.split(".")
            if scene_name not in loaded_scenes:
                loaded_scenes[scene_name] = {}
            if scene_parameter == RosParams.SCENES_COLOR_PARAMETER:
                loaded_scenes[scene_name][scene_parameter] = Color(
                    param.value[0], param.value[1], param.value[2]
                )
            else:
                loaded_scenes[scene_name][scene_parameter] = param.value
        self.scenes = {}
        for scene_name in loaded_scenes.keys():
            self.scenes[scene_name] = SceneData(**loaded_scenes[scene_name])

    async def _load_segments_from_wled_controller(self) -> dict:
        """
        Asynchronous method to fetch segments configuration from WLED controller.

        Returns:
            Dict<String,SectionData>
        """

        async with WLED(self.wled_url) as led:
            device = await led.update()
            loaded_sections = {}

            i = 1
            for segment in device.state.segments:
                loaded_sections[f"section_{i}"] = SectionData(
                    segment.segment_id, segment.start, segment.stop
                )
                i += 1
            return loaded_sections

    def _parameter_callback(self, params: dict) -> SetParametersResult:
        """
        Callback function triggered every time ROS parameter is changed while node is running.
        """
        for param in params:
            self.get_logger().info("param name " + param.name)

            if param.name == RosParams.WLED_CONTROLLER_URL:
                self.wled_url = param.value
                self.get_logger().info("Updated led ip: " + self.wled_url)
            if param.name == RosParams.WLED_SEGMENTS_COUNT:
                self.led_count = param.value
                self.get_logger().info("Updated led number: " + self.wled_url)

            if param.name.startswith(f"{RosParams.SCENES_YAML_NAME}."):
                values = param.name.split(".")
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
            pars (dict): Dictionary containing following parameters: brightness, start_led_id, stop_led_id, color[red, green, blue].

        Returns:
            str: Confirmation message indicating the scene was set.
        """
        self.get_logger().info(f"{pars}")
        try:
            async with WLED(self.wled_url) as led:
                await led.segment(
                    on=True,
                    brightness=pars.brightness,
                    segment_id=pars.section_id,
                    start=pars.start_led_id,
                    stop=pars.stop_led_id,
                    color_primary=pars.color,
                    transition=1,
                )
                await led.master(on=True)
            return True, "Scene complete"
        except Exception as e:
            self.get_logger().error(f"Failed to fetch WLED info: {e}")
            return False, "Failed to execute scene"

    async def scene_all(self, pars: RunLightsData) -> tuple[bool, str]:
        """
        Asynchronous method to set a custom LED scene using the WLED API.
        Runs all available leds with selected Scene.
        """

        self.get_logger().info(f"{pars}")
        try:
            async with WLED(self.wled_url) as led:
                for section in self.sections.values():
                    await led.segment(
                        on=True,
                        brightness=pars.brightness,
                        segment_id=section.section_id,
                        start=section.start_led_id,
                        stop=section.stop_led_id,
                        color_primary=pars.color,
                        transition=1,
                    )
                    await led.master(on=True)
            return True, "Scene complete"
        except Exception as e:
            self.get_logger().error(f"Failed to fetch WLED info: {e}")
            return False, "Failed to execute scene"

    async def scene_off(self, pars: RunLightsData) -> tuple[bool, str]:
        """
        Asynchronous method to turn off all LEDs using the WLED API.

        Args:
            _: Unused parameter, kept for interface consistency.

        Returns:
            str: Confirmation message indicating the scene is turned off.
        """
        try:
            async with WLED(self.wled_url) as led:
                await led.segment(on=False, segment_id=pars.section_id)
            return True, "Scene 'OFF' complete"
        except Exception as e:
            self.get_logger().error(f"Failed to fetch WLED info: {e}")
            return False, "Failed to execute scene 'OFF'"

    async def scene_off_all(self, pars: RunLightsData) -> tuple[bool, str]:
        """
        Asynchronous method to turn off all LEDs using the WLED API.

        Args:
            _: Unused parameter, kept for interface consistency.

        Returns:
            str: Confirmation message indicating the scene is turned off.
        """
        try:
            async with WLED(self.wled_url) as led:
                for section in self.sections.values():
                    await led.segment(on=False, segment_id=section.section_id)
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
    ) -> GetScenes.Response:
        """
        Synchronous service handler for ROS 2 service requests.
        Returns the lists of currently configured scenes's parameters (lists of scene names, brightnesses and separate RGB values).
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
            colors_r.append(int(data.color.R))
            colors_g.append(int(data.color.G))
            colors_b.append(int(data.color.B))

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
        Returns the lists of currently configured scetion's parameters (lists of section names, starts and stops).
        """
        self.get_logger().info("GetSections service called")

        section_names = []
        starts = []
        stops = []

        for name, data in self.sections.items():
            section_names.append(name)
            starts.append(int(data.start_led_id))
            stops.append(int(data.stop_led_id))

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
                color=Color(*list(request.color)), brightness=int(request.brightness)
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
            SceneFunction.CHANGE_ALL: self.scene_all,
            SceneFunction.SCENE_OFF_ALL: self.scene_off_all,
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
            RunLightsData: Object containing brightness, color, start_led_id, stop_led_id, segment_id and function to run leds.
        """

        scene_key = (
            request.scene.lower()
            if hasattr(request, RosParams.REQUEST_SCENE_KEY) and request.scene
            else RosParams.SCENE_OFF_KEY
        )
        section_key = (
            request.section.lower()
            if hasattr(request, RosParams.REQUEST_SECTION_KEY) and request.section
            else RosParams.SECTION_ALL_KEY
        )
        section_data = {}
        scene_data = {}

        if scene_key == RosParams.SCENE_CUSTOM_KEY:
            scene_function = SceneFunction.CHANGE_SCENE
            scene_data = self._parse_scene_params(request.optional_params.split())

        elif scene_key == RosParams.SCENE_OFF_KEY:
            scene_function = SceneFunction.SCENE_OFF
        # preset scene
        elif scene_key in self.scenes.keys():
            scene_function = SceneFunction.CHANGE_SCENE
            scene_data = asdict(self.scenes[scene_key])
        # default behaviour
        else:
            scene_function = SceneFunction.SCENE_OFF

        # select section from preset
        if section_key in self.sections.keys():
            section_data = asdict(self.sections[section_key])

        # select all sections
        else:
            if scene_function == SceneFunction.SCENE_OFF:
                scene_function = SceneFunction.SCENE_OFF_ALL
            else:
                scene_function = SceneFunction.CHANGE_ALL

        return RunLightsData(
            scene_function=scene_function, **scene_data, **section_data
        )

    def _parse_scene_params(self, params_list: list) -> dict:
        """
        Parse a list of string parameters to create scene data.

        Parameters (all optional, default values used if missing or invalid):
            params_list[0]: brightness (int, default 255)
            params_list[1]: red color value (int, default 255)
            params_list[2]: green color value (int, default 255)
            params_list[3]: blue color value (int, default 255)

        Returns:
        {
            brightness: (int),
            color: (array of 3 ints: (red, green, blue))
        }

        """
        return {
            "brightness": int(params_list[0]) if len(params_list) > 0 else 255,
            "color": Color(
                R=int(params_list[1]) if len(params_list) > 1 else 255,
                G=int(params_list[2]) if len(params_list) > 2 else 255,
                B=int(params_list[3]) if len(params_list) > 3 else 255,
            ),
        }


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
