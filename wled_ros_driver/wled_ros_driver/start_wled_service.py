import asyncio
from wled import WLED

import rclpy
from rclpy.node import Node
from wled_interfaces.srv import ChangeScene

# TODO(issue#3): move hardcoded IP to a YAML config
WLED_URL = "192.168.0.220"


class AsyncServiceWledNode(Node):
    _scene_map_template = {
        "scene_1": ("scene_x", "255"),
        "scene_2": ("scene_x", "127"),
        "scene_3": ("scene_x", "63"),
        "scene_4": ("scene_x", "31"),
        "scene_off": ("scene_off", None),
        "scene_custom": ("scene_x", None),  # Params set dynamically
    }

    def __init__(self):
        super().__init__("wled_service_node")
        self.srv = self.create_service(
            ChangeScene, "wled_scene_change", self._handle_service
        )
        self.get_logger().info("Async service node started")

    async def wled_info(self):
        async with WLED(WLED_URL) as led:
            device = await led.update()
            self.get_logger().info(f"WLED firmware version: {device.info.version}")

    async def scene_x(self, pars):
        params = pars.split()
        self.get_logger().info(f"Custom params: {params}, brightness is: {params[0]}")

        brightness, start, stop, color = self._parse_params(params)

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
        return "Scene complete"

    async def scene_off(self, _):
        async with WLED(WLED_URL) as led:
            await led.master(on=False)
        return "Scene 'OFF' complete"

    async def process_request(self, request):
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
        # Use asyncio to run the async handler
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(self.process_request(request))
        response.success = True
        response.message = result
        return response

    def _parse_request_to_scene(self, request) -> str:
        scene_key = (
            request.scene.lower()
            if hasattr(request, "scene") and request.scene
            else "scene_off"
        )
        if scene_key not in self._scene_map_template:
            scene_key = "scene_off"

        return scene_key

    def _parse_params(self, params_list):
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
    rclpy.init(args=args)
    node = AsyncServiceWledNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
