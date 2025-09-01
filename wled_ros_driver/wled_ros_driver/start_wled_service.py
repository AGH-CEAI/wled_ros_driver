import asyncio
from wled import WLED

WLED_URL = "192.168.0.220"

import asyncio
import rclpy
from rclpy.node import Node
from wled_interfaces.srv import Action

BRIGHTNESS_SCENE_1 = 255
BRIGHTNESS_SCENE_2 = 127
BRIGHTNESS_SCENE_3 = 63
BRIGHTNESS_SCENE_4 = 31

SEGMENT_ID_SCENE_X = 0
START_LED_SCENE_X = 0
STOP_LED_SCENE_X = 72
COLOR_PRIMARY_SCENE_X = (255, 255, 255)
TRANSITION = 1


class AsyncServiceWledNode(Node):

    def __init__(self):
        super().__init__('async_service_node')
        self.srv = self.create_service(Action, 'do_action', self.handle_service)
        self.get_logger().info("Async service node started")
        
    async def wled_info(self):
        async with WLED(WLED_URL) as led:
            device = await led.update()
            print(device.info.version)
        
    async def scene_1(self):
        async with WLED(WLED_URL) as led:
            await led.segment(on=True, brightness=255, segment_id=0, start=0, stop=72, color_primary=(255, 255, 255), transition=1)
            await led.master(on=True)
        return "Scene '1' complete"

    async def scene_2(self):
        async with WLED(WLED_URL) as led:
            await led.segment(on=True, brightness=127, segment_id=0, start=0, stop=72, color_primary=(255, 255, 255), transition=1)
            await led.master(on=True)
        return "Scene '2' complete"

    async def scene_3(self):
        async with WLED(WLED_URL) as led:
            await led.segment(on=True, brightness=63, segment_id=0, start=0, stop=72, color_primary=(255, 255, 255), transition=1)
            await led.master(on=True)
        return "Scene '3' complete"

    async def scene_4(self):
        async with WLED(WLED_URL) as led:
            await led.segment(on=True, brightness=31, segment_id=0, start=0, stop=72, color_primary=(255, 255, 255), transition=1)
            await led.master(on=True)
        return "Scene '4' complete"
    
    async def scene_off(self):
        # await asyncio.sleep(4)
        async with WLED(WLED_URL) as led:
            await led.master(on=False)
        return "Scene 'OFF' complete"
    
    async def scene_custom(self):
        # await asyncio.sleep(4)
        async with WLED(WLED_URL) as led:
            await led.segment(on=True, brightness=63, segment_id=0, start=15, stop=55, color_primary=(255, 0, 0), transition=1)
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
        action_key = request.action.lower() if hasattr(request, 'action') else "scene_1"
        action = action_map.get(action_key, self.scene_1)
        result = await action()
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

if __name__ == '__main__':
    main()
