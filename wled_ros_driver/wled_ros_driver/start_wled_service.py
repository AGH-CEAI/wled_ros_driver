import asyncio
from wled import WLED

WLED_URL = "192.168.0.220"


# async def main() -> None:
#     """Show example on controlling your WLED device."""
#     async with WLED("192.168.0.220") as led:
#         device = await led.update()
#         print(device.info.version)

#         # Turn strip on, full brightness
#         await led.master(on=True, brightness=255)


# if __name__ == "__main__":
#     asyncio.run(main())


import asyncio
import rclpy
from rclpy.node import Node
from example_interfaces.srv import Trigger  # Using Trigger as a simple example service
from wled_interfaces.srv import Action

class AsyncServiceWledNode(Node):

    def __init__(self):
        super().__init__('async_service_node')
        self.srv = self.create_service(Action, 'do_action', self.handle_service)
        self.get_logger().info("Async service node started")

    async def action_one(self):
        # await asyncio.sleep(1)
        async with WLED(WLED_URL) as led:
            device = await led.update()
            print(device.info.version)

            # Turn strip on, full brightness
            await led.master(on=True, brightness=255)
        return "Action one completed"

    async def action_two(self):
        # await asyncio.sleep(2)
        async with WLED(WLED_URL) as led:
            device = await led.update()
            print(device.info.version)

            # Turn strip on, full brightness
            await led.master(on=True, brightness=127)
        return "Action two completed"

    async def action_three(self):
        # await asyncio.sleep(3)
        async with WLED(WLED_URL) as led:
            device = await led.update()
            print(device.info.version)

            # Turn strip on, full brightness
            await led.master(on=True, brightness=63)
        return "Action three completed"

    async def action_four(self):
        # await asyncio.sleep(4)
        async with WLED(WLED_URL) as led:
            device = await led.update()
            print(device.info.version)

            # Turn strip on, full brightness
            await led.master(on=True, brightness=31)
        return "Action four completed"
    
    async def action_five(self):
        # await asyncio.sleep(4)
        async with WLED(WLED_URL) as led:
            device = await led.update()
            print(device.info.version)

            # Turn strip on, full brightness
            await led.master(on=True, brightness=0)
        return "Action five completed"

    async def process_request(self, request):
        # Simulate reading input for which action to execute
        action_map = {
            "one": self.action_one,
            "two": self.action_two,
            "three": self.action_three,
            "four": self.action_four,
            "five": self.action_five,
        }
        action_key = request.action.lower() if hasattr(request, 'action') else "one"
        action = action_map.get(action_key, self.action_one)
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
