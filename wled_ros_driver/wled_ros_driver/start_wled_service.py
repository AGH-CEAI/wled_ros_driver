import asyncio
from wled import WLED

import rclpy
from rclpy.node import Node
from wled_interfaces.srv import ChangeScene

# TODO(issue#3): move hardcoded IP to a YAML config
WLED_URL = "192.168.0.220"


class AsyncServiceWledNode(Node):
    """
    ROS 2 node providing an asynchronous service interface for controlling WLED devices.

    - Handles requests to change LED scenes and parameters via the 'wled_scene_change' service.
    - Supports predefined and custom scenes with adjustable brightness, color, and LED range.
    - Communicates with WLED devices using the WLED Python API.
    - Provides utility methods for parsing requests, parameters, and fetching device info.
    """

    _scene_map_template = {
        "scene_1": ("scene_x", "255"),
        "scene_2": ("scene_x", "127"),
        "scene_3": ("scene_x", "63"),
        "scene_4": ("scene_x", "31"),
        "scene_off": ("scene_off", None),
        "scene_custom": ("scene_x", None),  # Params set dynamically
    }

    def __init__(self):
        """
        Initializes the AsyncServiceWledNode.

        - Sets the node name to 'wled_service_node'.
        - Creates the 'wled_scene_change' service using the ChangeScene interface.
        - Registers the _handle_service method as the service callback.
        - Logs a message indicating the service node has started.
        """
        super().__init__("wled_service_node")
        self.srv = self.create_service(
            ChangeScene, "wled_scene_change", self._handle_service
        )
        self.get_logger().info("Async service node started")

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
            async with WLED(WLED_URL) as led:
                device = await led.update()
                self.get_logger().info(f"WLED firmware version: {device.info.version}")
        except Exception as e:
            self.get_logger().error(f"Failed to fetch WLED info: {e}")

    async def scene_x(self, pars):
        """
        Asynchronous method to set a custom LED scene using the WLED API.

        - Parses space-separated parameters for brightness, start/stop LED indices, and RGB color.
        - Logs the received parameters for debugging.
        - Sends the segment configuration to the WLED device.
        - Turns on the master switch for LEDs.

        Args:
            pars (str): Space-separated string of parameters (brightness, start, stop, red, green, blue).

        Returns:
            str: Confirmation message indicating the scene was set.
        """
        params = pars.split()
        self.get_logger().info(f"Custom params: {params}, brightness is: {params[0]}")

        brightness, start, stop, color = self._parse_params(params)

        try:
            async with WLED(WLED_URL) as led:
                await led.segment(
                    on=True,
                    brightness=brightness,
                    segment_id=0,
                    start=start,
                    stop=stop,
                    color_primary=color,
                    transition=1,
                )
                await led.master(on=True)
            return True, "Scene complete"
        except Exception as e:
            self.get_logger().error(f"Failed to fetch WLED info: {e}")
            return False, "Failed to execute scene"

    async def scene_off(self, _):
        """
        Asynchronous method to turn off all LEDs using the WLED API.

        Args:
            _: Unused parameter, kept for interface consistency.

        Returns:
            str: Confirmation message indicating the scene is turned off.
        """
        try:
            async with WLED(WLED_URL) as led:
                await led.master(on=False)
            return True, "Scene 'OFF' complete"
        except Exception as e:
            self.get_logger().error(f"Failed to fetch WLED info: {e}")
            return False, "Failed to execute scene 'OFF'"

    async def process_request(self, request):
        """
        Asynchronous handler for processing incoming service requests.

        - Logs the requested scene and parameters.
        - Determines the correct scene method and parameters using the scene map.
        - Calls the appropriate async scene method with the parameters.
        - Returns the result from the scene method.

        Args:
            request: The service request object containing 'scene' and 'optional_params'.

        Returns:
            result: The result string from the executed scene method.
        """
        self.get_logger().info(
            f"Requested scene: {request.scene} | params: {request.optional_params}"
        )

        scene_key = self._parse_request_to_scene(request)
        method_name, param = self._scene_map_template[scene_key]
        param = request.optional_params if param is None else param

        method = getattr(self, method_name, None)
        result = await method(param)

        return result

    def _handle_service(self, request, response):
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
        result = loop.run_until_complete(self.process_request(request))
        response.success = result[0]
        response.message = result[1]
        return response

    def _parse_request_to_scene(self, request) -> str:
        """
        Extracts and normalizes the requested scene name from the service request.
        If the scene is not specified or not recognized, defaults to 'scene_off'.

        Args:
            request: The service request object containing the 'scene' attribute.

        Returns:
            scene_key (str): Valid scene key from _scene_map_template.
        """
        scene_key = (
            request.scene.lower()
            if hasattr(request, "scene") and request.scene
            else "scene_off"
        )
        if scene_key not in self._scene_map_template:
            scene_key = "scene_off"

        return scene_key

    def _parse_params(self, params_list):
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
            brightness (int)
            start (int)
            stop (int)
            color (tuple of 3 ints: (red, green, blue))
        """
        try:
            brightness = int(params_list[0]) if len(params_list) > 0 else 255
            start = int(params_list[1]) if len(params_list) > 1 else 0
            stop = int(params_list[2]) if len(params_list) > 2 else 72
            color_red = int(params_list[3]) if len(params_list) > 3 else 255
            color_green = int(params_list[4]) if len(params_list) > 4 else 255
            color_blue = int(params_list[5]) if len(params_list) > 5 else 255
            color = (color_red, color_green, color_blue)
        except ValueError as e:
            self.get_logger().error(f"Invalid parameter value: {e}")
            brightness, start, stop, color = 255, 0, 72, (127, 127, 63)
        return brightness, start, stop, color


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
