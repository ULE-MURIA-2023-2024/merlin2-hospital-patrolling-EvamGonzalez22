import rclpy
from rclpy.node import Node

class MissionNode(Node):
    def __init__(self):
        super().__init__('mission_node')
        self.get_logger().info("Iniciando misión de patrullaje en MERLIN2...")
        # Aquí nos conectaremos a KANT y YASMIN para ejecutar el plan

def main(args=None):
    rclpy.init(args=args)
    node = MissionNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
