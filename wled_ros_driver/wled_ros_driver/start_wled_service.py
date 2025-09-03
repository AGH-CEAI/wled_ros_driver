import asyncio
from wled import WLED

import rclpy
from rclpy.node import Node
from wled_interfaces.srv import Action

WLED_URL = "192.168.0.220"


class AsyncServiceWledNode(Node):
    def __init__(self):
        super().__init__("wled_service_node")
        self.srv = self.create_service(Action, "do_action", self.handle_service)
        self.get_logger().info("Async service node started")

    async def wled_info(self):
        async with WLED(WLED_URL) as led:
            device = await led.update()
            print(device.info.version)

    async def scene_x(self, pars):
        params = pars.split()
        print(f"Custom params: {params}, brightness is: {params[0]}")

        if len(params) > 0:
            brightness = int(params[0])
        else:
            brightness = 255

        if len(params) > 1:
            start = int(params[1])
            stop = int(params[2])
            color = tuple(map(int, params[3:6]))
        else:
            start = 0
            stop = 72
            color = (255, 255, 255)

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
        # Simulate reading input for which action to execute
        action_map = {
            "scene_1": (self.scene_x, "255"),
            "scene_2": (self.scene_x, "127"),
            "scene_3": (self.scene_x, "63"),
            "scene_4": (self.scene_x, "31"),
            "scene_off": (self.scene_off, None),
            "scene_custom": (self.scene_x, request.optional_params),
        }

        self.get_logger().info(
            f"Requested action: {request.action} | params: {request.optional_params}"
        )
        action_key = (
            request.action.lower() if hasattr(request, "action") else "scene_off"
        )
        action = action_map.get(action_key, self.scene_x)[0]
        pars = action_map.get(action_key, self.scene_x)[1]
        result = await action(pars)
        return result

    def handle_service(self, request, response):
        # Use asyncio to run the async handler
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(self.process_request(request))
        response.success = True
        response.message = result
        return response


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
