import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, SetEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource

def generate_launch_description():
    """
    Función principal de lanzamiento.
    Configura el entorno de simulación, las rutas de los modelos 3D y lanza
    la simulación de Nav2 completa (Gazebo + AMCL + Navigation Stack).
    """
    
    # --- 1. Obtención de directorios de paquetes ---
    # Buscamos la ruta de instalación de los paquetes necesarios
    pkg_practica = get_package_share_directory('practicas_nav_pkg')  # Paquete rpincipal
    pkg_nav2_bringup = get_package_share_directory('nav2_bringup')   # Paquete estándar de Nav2
    pkg_tb3_gazebo = get_package_share_directory('turtlebot3_gazebo') # Paquete del robot
    
    # --- 2. Definición de rutas de archivos de configuración ---
    # Mapa (.yaml): Define los obstáculos estáticos y resolución
    map_file = os.path.join(pkg_practica, 'maps', 'aws_house.yaml')
    # Mundo (.world): El entorno 3D que cargará Gazebo
    world_file = os.path.join(pkg_practica, 'worlds', 'small_house.world') 
    # Params (.yaml): Configuración de costes, planificadores y comportamiento de Nav2
    params_file = os.path.join(pkg_practica, 'config', 'nav2_params.yaml')
    
    # --- 3. Configuración del GAZEBO_MODEL_PATH ---
    # Gazebo necesita saber dónde buscar las mallas 3D (meshes/dae/stl).
    # Si no se configura bien, los objetos aparecen invisibles o dan error.
    
    user_home = os.path.expanduser('~') # Obtiene la ruta al directorio home (/home/usuario)
    
    # Ruta absoluta manual a tus modelos personalizados (AWS RoboMaker models).
    # Se usa ruta absoluta para evitar problemas si el paquete no exporta los modelos correctamente.
    aws_models_path = os.path.join(user_home, 'Documents/MASTER/RS/laboratorio-1-EvamGonzalez22/practicaFinalRoSer/src/practicas_nav_pkg/models')
    
    # Ruta a los modelos estándar del Turtlebot3
    tb3_models_path = os.path.join(pkg_tb3_gazebo, 'models')
    
    # Concatenamos todas las rutas separadas por dos puntos (:), sintaxis estándar de Linux.
    # Orden de búsqueda: 1. Modelos -> 2. Modelos TB3 -> 3. Modelos del sistema
    combined_models_path = f"{aws_models_path}:{tb3_models_path}:/usr/share/gazebo-11/models"

    # --- 4. Descripción del Lanzamiento ---
    return LaunchDescription([
        # Configuramos la variable de entorno ANTES de lanzar Gazebo
        SetEnvironmentVariable('GAZEBO_MODEL_PATH', combined_models_path),
        # Definimos qué modelo de robot usar (burger, waffle, waffle_pi)
        SetEnvironmentVariable('TURTLEBOT3_MODEL', 'burger'),

        # Incluimos el launch file estándar "tb3_simulation_launch.py".
        # Este script de Nav2 ya se encarga de levantar Gazebo, Rviz, AMCL y el Navigation Stack.
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(pkg_nav2_bringup, 'launch', 'tb3_simulation_launch.py')
            ),
            # Pasamos nuestros parámetros personalizados al launch hijo
            launch_arguments={
                'map': map_file,            # Nuestro mapa
                'world': world_file,        # Nuestro mundo
                'params_file': params_file, # Nuestra configuración de navegación
                'use_sim_time': 'True',     # Obligatorio en simulación para sincronizar relojes
                'headless': 'False',        # 'False' para mostrar la ventana gráfica de Gazebo
                
                # Coordenadas de aparición inicial (Spawning)
                # Se ajustan para evitar que el robot nazca dentro de un obstáculo (ej. sofá)
                'x_pose': '-3.5',
                'y_pose': '1.0',
                'z_pose': '0.05' 
            }.items(),
        ),
    ])