#include <iostream>
#include <rclcpp/rclcpp.hpp>
#include <behaviortree_cpp_v3/bt_factory.h>

using namespace BT;

class DetectaObstaculo : public ConditionNode {
public:
    DetectaObstaculo(const std::string& name) : ConditionNode(name, {}) {}
    NodeStatus tick() override {
        std::cout << "[Sensor] Comprobando obstáculo. No hay obstáculo." << std::endl;
        return NodeStatus::FAILURE; 
    }
};

class Detenerse : public SyncActionNode {
public:
    Detenerse(const std::string& name) : SyncActionNode(name, {}) {}
    NodeStatus tick() override {
        std::cout << "[Acción] Frenos activados. Robot detenido." << std::endl;
        return NodeStatus::SUCCESS;
    }
};

class Girar : public SyncActionNode {
public:
    Girar(const std::string& name) : SyncActionNode(name, {}) {}
    NodeStatus tick() override {
        std::cout << "[Acción] Girando para esquivar..." << std::endl;
        return NodeStatus::SUCCESS;
    }
};

class Avanzar : public SyncActionNode {
public:
    Avanzar(const std::string& name) : SyncActionNode(name, {}) {}
    NodeStatus tick() override {
        std::cout << "[Acción] Motores en marcha. Avanzando." << std::endl;
        return NodeStatus::SUCCESS;
    }
};

int main(int argc, char **argv) {
    rclcpp::init(argc, argv);
    std::cout << "--- Iniciando Sistema de Control (Behavior Tree) ---" << std::endl;

    BehaviorTreeFactory factory;
    factory.registerNodeType<DetectaObstaculo>("DetectaObstaculo");
    factory.registerNodeType<Detenerse>("Detenerse");
    factory.registerNodeType<Girar>("Girar");
    factory.registerNodeType<Avanzar>("Avanzar");

    try {
        // AQUÍ ESTÁ LA MAGIA: Tu ruta absoluta
        auto tree = factory.createTreeFromFile("/home/evagonz/Documents/MASTER/CUATRI2/ROCOG/p2/comportamientoEj2.xml");
        tree.tickRoot();
    } catch (const std::exception& e) {
        std::cerr << "Error al cargar el XML: " << e.what() << std::endl;
    }

    rclcpp::shutdown();
    return 0;
}
