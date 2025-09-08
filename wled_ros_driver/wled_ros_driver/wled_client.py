import sys
import rclpy
from rclpy.node import Node
from wled_interfaces.srv import ChangeScene


class AsyncServiceWledClient(Node):
    def __init__(self):
        super().__init__("wled_service_client")
        self.client = self.create_client(ChangeScene, "wled_scene_change")
        while not self.client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info("Service not available, waiting...")
        self.req = ChangeScene.Request()

    def send_request(self, scene_name, optional_params=""):
        self.req.scene = scene_name
        self.req.optional_params = optional_params
        self.future = self.client.call_async(self.req)
        self.future.add_done_callback(self.response_callback)

    def response_callback(self, future):
        try:
            response = future.result()
            self.get_logger().info(f"Response from service: {response.message}")
        except Exception as e:
            self.get_logger().error(f"Service call failed: {e}")


def main(args=None):
    rclpy.init(args=args)
    client = AsyncServiceWledClient()

    # Provide the scene name as a command line argument or default to "one"
    scene = sys.argv[1] if len(sys.argv) > 1 else "scene_1"
    optional_params = sys.argv[2] if len(sys.argv) > 2 else "None"
    client.get_logger().info(f"Sending request for scene: {scene} | {optional_params}")
    client.send_request(scene, optional_params)

    # Spin until response received
    rclpy.spin(client)
    client.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
