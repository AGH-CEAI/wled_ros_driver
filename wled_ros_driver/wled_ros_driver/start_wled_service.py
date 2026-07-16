# Copyright (c) 2025-2026, AGH Center of Excellence in Artificial Intelligence
# All rights reserved.
#
# SPDX-License-Identifier: Apache-2.0

import asyncio
from wled import WLED
import rclpy
from rclpy.node import Node
from wled_interfaces.srv import ChangeScene
from wled_ros_driver.scene_data import SceneData
from wled_ros_driver.scene_function import SceneFunction
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

        self.srv = self.create_service(
            ChangeScene, "wled_scene_change", self._handle_service
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

    def _parameter_callback(self, params: dict) -> SetParametersResult:
        """
        Callback function triggered every time ROS parameter is changed while node is running.
        """
        for param in params:
            self.get_logger().info("param name " + param.name)

            if param.name == "wled_url":
                self.wled_url = param.value
                self.get_logger().info("Updated led ip: " + self.wled_url)

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

    async def scene_x(self, pars: SceneData) -> tuple[bool, str]:
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
        self.get_logger().info(f"brightness is: {pars.brightness}")
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

    async def scene_off(self, _pars: SceneData) -> tuple[bool, str]:
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
            SceneFunction.TURN_OFF: self.scene_off,
        }

        self.get_logger().info(
            f"Requested scene: {request.scene} | params: {request.optional_params}"
        )

        method_enum, params = self._prepare_request_params(request)

        return await METHODS_MAP[method_enum](params)

    def _prepare_request_params(
        self, request: ChangeScene.Request
    ) -> tuple[SceneFunction, SceneData]:
        """
        Extracts and normalizes the requested scene name from the service request.
        If the scene is not specified or not recognized, defaults to 'scene_off'.
        It also creates params dict, with all data needed by led control based on either on data provided in request or selected form availibile presets.

        Args:
            request: The service request object containing the 'scene' attribute.

        Returns:
            function_name (str): name of a function to run in order to get desired led behaviour.
            params (dict): Dictionary containing all parameters describing desired led behaviour (brightness,start,stop,color).
        """

        scene_key = (
            request.scene.lower()
            if hasattr(request, "scene") and request.scene
            else "scene_off"
        )

        if scene_key == "scene_custom":
            return SceneFunction.CHANGE_SCENE, self._parse_params_from_array(
                request.optional_params.split()
            )
        if scene_key == "scene_off":
            return SceneFunction.SCENE_OFF, {}

        if scene_key in self.scenes.keys():
            return SceneFunction.CHANGE_SCENE, self.scenes[scene_key]
        else:
            return SceneFunction.SCENE_OFF, {}

    def _parse_params_from_array(self, params_list: list) -> SceneData:
        """
        Parse a list of string parameters for custom WLED scene control.

        Parameters (all optional, default values used if missing or invalid):
            params_list[0]: brightness (int, default 255)
            params_list[1]: start LED index (int, default 0)
            params_list[2]: stop LED index (int, default 72)
            params_list[3]: red color value (int, default 255)
            params_list[4]: green color value (int, default 255)
            params_list[5]: blue color value (int, default 255)

        Returns:
        {
            brightness: (int),
            start: (int),
            stop: (int),
            color: (array of 3 ints: (red, green, blue))
        }

        """
        result = SceneData
        try:
            result.brightness = int(params_list[0]) if len(params_list) > 0 else 255
            result.start = int(params_list[1]) if len(params_list) > 1 else 0
            result.stop = int(params_list[2]) if len(params_list) > 2 else 72
            color_red = int(params_list[3]) if len(params_list) > 3 else 255
            color_green = int(params_list[4]) if len(params_list) > 4 else 255
            color_blue = int(params_list[5]) if len(params_list) > 5 else 255
            result.color = [color_red, color_green, color_blue]

        except ValueError as e:
            self.get_logger().error(f"Invalid parameter value: {e}")
            result = SceneData(
                brightness=255,
                start=0,
                stop=72,
                color=[127, 127, 63],
            )

        return result


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
