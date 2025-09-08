import sys
import rclpy
from rclpy.node import Node
from wled_interfaces.srv import ChangeScene


class AsyncServiceWledClient(Node):
    """
    ROS 2 client node for interacting with the WLED service.

    - Connects to the 'wled_scene_change' service.
    - Sends requests to change LED scenes and parameters.
    - Handles asynchronous responses from the service.
    - Logs service availability, requests, and responses for debugging.
    """

    def __init__(self):
        """
        Initializes the AsyncServiceWledClient node.

        - Sets the node name to 'wled_service_client'.
        - Creates a client for the 'wled_scene_change' service using the ChangeScene interface.
        - Waits for the service to become available, logging status messages.
        - Initializes a ChangeScene request object for sending service requests.
        """
        super().__init__("wled_service_client")
        self.client = self.create_client(ChangeScene, "wled_scene_change")
        while not self.client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info("Service not available, waiting...")
        self.req = ChangeScene.Request()

    def send_request(self, scene_name, optional_params=""):
        """
        Sends an asynchronous service request to change the WLED scene.

        - Sets the scene name and optional parameters in the request object.
        - Calls the 'wled_scene_change' service asynchronously.
        - Registers a callback to handle the service response.

        Args:
            scene_name (str): Name of the scene to set.
            optional_params (str): Space-separated parameters for custom scenes (optional).
        """
        self.req.scene = scene_name
        self.req.optional_params = optional_params
        self.future = self.client.call_async(self.req)
        self.future.add_done_callback(self.response_callback)

    def response_callback(self, future):
        """
        Callback function to handle the response from the asynchronous service request.

        - Logs the service response message if successful.
        - Logs an error message if the service call fails.

        Args:
            future: The Future object representing the asynchronous service call.
        """
        try:
            response = future.result()
            self.get_logger().info(f"Response from service: {response.message}")
        except Exception as e:
            self.get_logger().error(f"Service call failed: {e}")


def main(args=None):
    """
    Entry point for the WLED ROS 2 client node.

    - Initializes the ROS 2 Python client library.
    - Creates an instance of AsyncServiceWledClient.
    - Reads the scene name and optional parameters from command line arguments (defaults if not provided).
    - Sends a service request to change the WLED scene.
    - Spins the node to process incoming responses.
    - Handles node shutdown and cleanup.
    """
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
    # Executes the main function when the script is run directly
    main()
