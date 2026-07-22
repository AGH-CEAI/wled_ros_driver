# Copyright (c) 2025-2026, AGH Center of Excellence in Artificial Intelligence
# All rights reserved.
#
# SPDX-License-Identifier: Apache-2.0

import asyncio
from wled import WLED
import rclpy
from rclpy.node import Node
from wled_interfaces.srv import ChangeScene
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
from time import sleep


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

        self.srv = self.create_service(
            ChangeScene, RosParams.SERVICE_NAME, self._handle_service
        )

        self.get_logger().info("Async service node started")
        self.get_logger().info(f"IP address {self.wled_url}")

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

        while rclpy.ok():
            try:
                loop = asyncio.get_event_loop()
                self.sections = loop.run_until_complete(
                    self._load_data_from_wled_controller()
                )
                break
            except Exception as e:
                self.get_logger().error(f"{e}. Retrying in 2 seconds...")
                sleep(2.0)

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

    async def _load_data_from_wled_controller(self) -> dict:
        """
        Asynchronous method to fetch configuration from WLED controller.

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
            self.effects = {}

            for effect in device.effects:
                self.effects[int(effect.effect_id)] = effect.name
            return loaded_sections

    def _parameter_callback(self, params: list) -> SetParametersResult:
        """
        Callback function triggered every time ROS parameter is changed while node is running.
        """
        for param in params:
            if param.name == RosParams.WLED_CONTROLLER_URL:
                self.wled_url = param.value
                self.get_logger().info(f"Updated led ip: {self.wled_url}")
            if param.name == RosParams.WLED_SEGMENTS_COUNT:
                self.led_count = param.value
                self.get_logger().info(f"Updated led number: {self.led_count}")

            if param.name.startswith(f"{RosParams.SCENES_YAML_NAME}."):
                self.get_logger().info("Updated scenes")

                values = param.name.split(".")
                if len(values) == 3:
                    _, scene_name, param_name = values
                    if scene_name not in self.scenes:
                        return SetParametersResult(successful=False)
                    edited_scene = asdict(self.scenes[scene_name])
                    if param_name == RosParams.SCENES_COLOR_PARAMETER:
                        edited_scene[param_name] = Color(
                            param.value[0], param.value[1], param.value[2]
                        )
                    else:
                        edited_scene[param_name] = param.value

                    self.scenes[scene_name] = SceneData(**edited_scene)

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
            pars (RunLightsData): Object containing following parameters: brightness, start_led_id, stop_led_id, color[red, green, blue].

        Returns:
            bool, str: Confirmation message indicating the scene was set.
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
                    color_primary=pars.color.as_list,
                    transition=1,
                    effect=pars.effect,
                )
                await led.master(on=True)
            return True, "Scene complete"
        except Exception as e:
            self.get_logger().error(f"Failed to execute scene_x: {e}")
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
                        color_primary=pars.color.as_list,
                        transition=1,
                        effect=pars.effect,
                    )
                await led.master(on=True)
            return True, "Scene complete"
        except Exception as e:
            self.get_logger().error(f"Failed to execute scene_all: {e}")
            return False, "Failed to execute scene"

    async def scene_off(self, pars: RunLightsData) -> tuple[bool, str]:
        """
        Asynchronous method to turn off selected LEDs using the WLED API.

        Args:
            pars (RunLightsData): Object containing following parameters: brightness, start_led_id, stop_led_id, color[red, green, blue].

        Returns:
            bool, str: Confirmation message indicating the scene was set.
        """
        try:
            async with WLED(self.wled_url) as led:
                await led.segment(on=False, segment_id=pars.section_id)
            return True, "Scene 'OFF' complete"
        except Exception as e:
            self.get_logger().error(f"Failed to execute scene_off: {e}")
            return False, "Failed to execute scene 'OFF'"

    async def scene_off_all(self, _pars: RunLightsData) -> tuple[bool, str]:
        """
        Asynchronous method to turn off all LEDs using the WLED API.

        Args:
            _pars (RunLightsData): Unused parameter kept for interface consistency.

        Returns:
            bool, str: Confirmation message indicating the scene was set.
        """
        try:
            async with WLED(self.wled_url) as led:
                for section in self.sections.values():
                    await led.segment(on=False, segment_id=section.section_id)
                await led.master(on=False)

            return True, "Scene 'OFF' complete"
        except Exception as e:
            self.get_logger().error(f"Failed to fetch WLED info: {e}")
            return False, "Failed to execute scene 'OFF'"

    async def do_nothing(self, _pars):
        """
        Empty method to be executed on wrong parameter entry.
        Args:
            _pars (RunLightsData): Unused parameter kept for interface consistency.

        Returns:
            bool, str: Error message indicating that scene key was not recognized.

        """
        return False, "Failed to recognize section"

    def _handle_service(
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
            SceneFunction.NO_CHANGE: self.do_nothing,
        }

        self.get_logger().info(
            f"Requested scene: {request.scene} | section:{request.section} |  effect_id:{request.effect_id} |params: {request.optional_params}"
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
        section_data = SectionData()
        scene_data = SceneData()

        if scene_key == RosParams.SCENE_CUSTOM_KEY:
            scene_function = SceneFunction.CHANGE_SCENE
            scene_data = self._parse_scene_params(request.optional_params.split())

        elif scene_key == RosParams.SCENE_OFF_KEY:
            scene_function = SceneFunction.SCENE_OFF
        # preset scene
        elif scene_key in self.scenes.keys():
            scene_function = SceneFunction.CHANGE_SCENE
            scene_data = self.scenes[scene_key]

        # default behaviour
        else:
            scene_function = SceneFunction.SCENE_OFF

        # select section from preset
        if section_key in self.sections.keys():
            section_data = self.sections[section_key]

        elif section_key == RosParams.SECTION_ALL_KEY:
            if scene_function == SceneFunction.SCENE_OFF:
                scene_function = SceneFunction.SCENE_OFF_ALL
            else:
                scene_function = SceneFunction.CHANGE_ALL

        # behaviour when section key not recognized
        else:
            scene_function = SceneFunction.NO_CHANGE

        effect = self.effects.get(int(request.effect_id), "Solid")
        return RunLightsData(
            scene_function=scene_function,
            effect=effect,
            color=scene_data.color,
            brightness=scene_data.brightness,
            **asdict(section_data),
        )

    def _parse_scene_params(self, params_list: list) -> SceneData:
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
        try:
            return SceneData(
                brightness=int(params_list[0]) if len(params_list) > 0 else 255,
                color=Color(
                    R=int(params_list[1]) if len(params_list) > 1 else 255,
                    G=int(params_list[2]) if len(params_list) > 2 else 255,
                    B=int(params_list[3]) if len(params_list) > 3 else 255,
                ),
            )
        except ValueError:
            self.get_logger().error("failed to parse custom data")
            return SceneData(
                brightness=255,
                color=Color(
                    R=255,
                    G=255,
                    B=255,
                ),
            )


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
