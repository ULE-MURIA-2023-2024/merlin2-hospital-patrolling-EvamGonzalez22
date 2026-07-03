cmake_minimum_required(VERSION 3.8)
project(bt_robot)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# 1. Buscar las dependencias de ROS 2 y Behavior Trees
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(behaviortree_cpp_v3 REQUIRED)

# 2. Crear el ejecutable a partir de nuestro main.cpp
add_executable(bt_robot_node src/main.cpp)

# 3. Enlazar el ejecutable con las librerías
ament_target_dependencies(bt_robot_node rclcpp behaviortree_cpp_v3)

# 4. Regla de instalación para que ROS 2 encuentre el nodo al hacer 'ros2 run'
install(TARGETS
  bt_robot_node
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()