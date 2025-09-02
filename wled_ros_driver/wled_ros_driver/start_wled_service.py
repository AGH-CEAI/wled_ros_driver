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

    async def scene_1(self, _):
        async with WLED(WLED_URL) as led:
            await led.segment(
                on=True,
                brightness=255,
                segment_id=0,
                start=0,
                stop=72,
                color_primary=(255, 255, 255),
                transition=1,
            )
            await led.master(on=True)
        return "Scene '1' complete"

    async def scene_2(self, _):
        async with WLED(WLED_URL) as led:
            await led.segment(
                on=True,
                brightness=127,
                segment_id=0,
                start=0,
                stop=72,
                color_primary=(255, 255, 255),
                transition=1,
            )
            await led.master(on=True)
        return "Scene '2' complete"

    async def scene_3(self, _):
        async with WLED(WLED_URL) as led:
            await led.segment(
                on=True,
                brightness=63,
                segment_id=0,
                start=0,
                stop=72,
                color_primary=(255, 255, 255),
                transition=1,
            )
            await led.master(on=True)
        return "Scene '3' complete"

    async def scene_4(self, _):
        async with WLED(WLED_URL) as led:
            await led.segment(
                on=True,
                brightness=31,
                segment_id=0,
                start=0,
                stop=72,
                color_primary=(255, 255, 255),
                transition=1,
            )
            await led.master(on=True)
        return "Scene '4' complete"

    async def scene_off(self, _):
        async with WLED(WLED_URL) as led:
            await led.master(on=False)
        return "Scene 'OFF' complete"

    async def scene_custom(self, pars):
        async with WLED(WLED_URL) as led:
            await led.segment(
                on=True,
                brightness=63,
                segment_id=0,
                start=15,
                stop=55,
                color_primary=(255, 0, 0),
                transition=1,
            )
            await led.master(on=True)
        return "Scene 'Custom' complete"

    async def process_request(self, request):
        # Simulate reading input for which action to execute
        action_map = {
            "scene_1": self.scene_1,
            "scene_2": self.scene_2,
            "scene_3": self.scene_3,
            "scene_4": self.scene_4,
            "scene_off": self.scene_off,
            "scene_custom": self.scene_custom,
        }

        # print(f"Requested action: {request.action} | params: {request.optional_params}")
        self.get_logger().info(
            f"Requested action: {request.action} | params: {request.optional_params}"
        )
        action_key = (
            request.action.lower() if hasattr(request, "action") else "scene_custom"
        )
        action = action_map.get(action_key, self.scene_1)
        result = await action(request.action.lower())
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
