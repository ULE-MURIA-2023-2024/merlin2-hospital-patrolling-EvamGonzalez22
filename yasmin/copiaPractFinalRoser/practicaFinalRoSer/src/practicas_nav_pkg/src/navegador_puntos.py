#!/usr/bin/env python3

"""
Navegador de Waypoints por Voz
Script principal que orquesta la navegación autónoma de un robot entre waypoints
usando Nav2, con interacción por voz y selección automática de controlador.
"""

import rclpy
from rclpy.node import Node
# BasicNavigator: API de alto nivel para enviar órdenes a Nav2 (navegación autónoma)
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
from geometry_msgs.msg import PoseStamped
import yaml
import os
import random
import sys  # Para leer argumentos de línea de comandos
from ament_index_python.packages import get_package_share_directory

# Importación de los módulos de funcionalidad dividida
from controlador_voz import ControladorVoz
from analizador_camino import AnalizadorCamino

# Librerías para el servicio de cambio de parámetros 
from rcl_interfaces.srv import SetParameters

class WaypointNavigator:
    """
    Clase principal encargada de gestionar la navegación por waypoints utilizando Nav2.
    Coordina la interacción por voz, el análisis de caminos y la ejecución de movimientos.
    """

    def __init__(self):
        """
        Constructor: Inicializa Nav2, carga los waypoints desde YAML, 
        y prepara los módulos de voz y análisis de caminos.
        """
        # Inicializar el Simple Commander (inicia un nodo ROS2 implícitamente)
        self.nav = BasicNavigator()

        # Instanciamos el controlador de voz para interacción hombre-máquina
        self.voz = ControladorVoz()

        # Instanciamos el analizador de caminos para selección automática de controlador
        self.analizador = AnalizadorCamino(self.nav)

        # Creamos un nodo auxiliar solo para llamar al servicio de cambio de parámetros
        self.service_node = rclpy.create_node('change_controller_client')
        self.client_param = self.service_node.create_client(SetParameters, '/controller_server/set_parameters')
        
        # --- Lectura de Waypoints desde el Archivo YAML ---
        # Obtenemos la ruta absoluta del paquete para localizar el archivo de configuración
        pkg_path = get_package_share_directory('practicas_nav_pkg')
        yaml_path = os.path.join(pkg_path, 'config', 'waypoints.yaml')
        
        # Convertir el contenido del YAML a una lista de diccionarios Python
        with open(yaml_path, 'r') as f:
            data = yaml.safe_load(f)
            self.waypoints = data['waypoints']
        
        # Bloqueante: Esperar a que la pila de navegación (Nav2) esté operativa
        self.nav.waitUntilNav2Active()


    def decir(self, texto):
        """
        Delega el habla al controlador de voz.
        
        Args:
            texto (str): Texto a pronunciar.
        """
        self.voz.decir(texto)

    def escuchar(self):
        """
        Delega la escucha al controlador de voz.
        
        Returns:
            str: Texto reconocido en minúsculas.
        """
        return self.voz.escuchar()
            
    def seleccionar_controlador(self, start_pose, goal_pose):
        """
        Delega el análisis de caminos al analizador para seleccionar el controlador adecuado.
        
        Args:
            start_pose (PoseStamped): Pose inicial del movimiento.
            goal_pose (PoseStamped): Pose destino del movimiento.
            
        Returns:
            str: Nombre del controlador ("PurePursuit" o "FollowPath").
        """
        return self.analizador.seleccionar_controlador(start_pose, goal_pose)

    def cambiar_controlador_servicio(self, nuevo_controlador):
        """
        Solicita el cambio de controlador mediante el servicio set_parameters.
        
        Args:
            nuevo_controlador (str): Nombre del controlador a activar.
        """
        self.analizador.cambiar_controlador_por_servicio(
            self.client_param, 
            nuevo_controlador, 
            self.service_node
        )

    def create_pose(self, wp):
        """
        Convierte un diccionario de coordenadas (del YAML) al formato PoseStamped de ROS2.
        
        Args:
            wp (dict): Diccionario con claves 'x' e 'y'.
            
        Returns:
            PoseStamped: Mensaje listo para ser enviado a Nav2.
        """
        pose = PoseStamped() 
        pose.header.frame_id = 'map' # Referencia global del mapa
        pose.header.stamp = self.nav.get_clock().now().to_msg() # Marca de tiempo actual

        # Asignación de posición
        pose.pose.position.x = float(wp['x'])
        pose.pose.position.y = float(wp['y'])
        # Orientación fija (w=1.0 indica rotación nula/neutra en cuaterniones)
        pose.pose.orientation.w = 1.0 
        return pose

    def buscar_destino_en_voz(self, texto_usuario, lista_puntos):
        """
        Busca si el usuario ha mencionado el nombre de algún waypoint en su frase.
        Devuelve el índice del waypoint en la lista si lo encuentra, o -1 si no.
        
        Args:
            texto_usuario (str): Texto pronunciado por el usuario.
            lista_puntos (list): Lista de waypoints a buscar.
            
        Returns:
            int: Índice del waypoint encontrado, o -1 si no se encuentra.
        """
        for i, wp in enumerate(lista_puntos):
            # Comparamos en minúsculas para evitar errores (ej: "ve al gimnasio")
            if wp['name'].lower() in texto_usuario:
                return i
        return -1

    def ejecutar_navegacion(self, modo="secuencial", es_ultima_fase=False):
        """
        Lógica principal de navegación. Itera sobre los puntos, gestiona el movimiento
        y maneja el diálogo con el usuario al llegar a cada destino.
        
        Args:
            modo (str): "secuencial" (orden del YAML) o "aleatorio" (barajar lista).
            es_ultima_fase (bool): Indica si tras terminar esta lista, el programa debe finalizar.
            
        Returns:
            str: Estado final ("completada", "cancelada").
        """
        # Copiamos la lista para no modificar la original en memoria
        puntos = self.waypoints.copy()
        
        if modo == "aleatorio":
            random.shuffle(puntos)
            self.decir("Iniciando modo aleatorio")
        else:
            self.decir("Iniciando navegación secuencial")

        # --- CAMBIO: Usamos WHILE e ÍNDICE MANUAL para poder saltar puntos ---
        i = 0
        
        # Variable para guardar donde estábamos antes de un desvío. -1 significa "sin desvío pendiente"
        indice_pendiente = -1 
        
        while i < len(puntos):
            wp = puntos[i]
            
            # 1. Configurar y enviar objetivo
            goal_pose = self.create_pose(wp)

            # Lógica de Cambio de Planificador Local 
            # Determinamos qué controlador usar según el análisis de geometría del camino
            # Analizamos la geometría del camino antes de empezar el movimiento
            if i == 0:
                # Caso especial: Primer punto. No tenemos un "punto anterior" fácil.
                # Usamos el modo seguro por defecto.
                controlador_elegido = "FollowPath"
            else:
                # Caso normal: Calculamos el camino desde el punto ANTERIOR al ACTUAL
                # Creamos la pose del punto previo (Usamos i-1 siempre, aunque vengamos de un salto)
                start_pose = self.create_pose(puntos[i-1]) if i > 0 else self.create_pose(puntos[0])
                # Llamamos al analizador para determinar el controlador más apropiado
                controlador_elegido = self.seleccionar_controlador(start_pose, goal_pose)

            # Llamamos al servicio para cambiar el controlador
            self.cambiar_controlador_servicio(controlador_elegido)

            # Informamos y enviamos la orden con el controlador específico
            self.decir(f"Siguiente destino: {wp['name']}... (Modo {controlador_elegido})")
            
            # Iniciamos navegacion hacia el waypoint
            self.nav.goToPose(goal_pose)

            # 2. Bucle de espera mientras el robot se mueve
            while not self.nav.isTaskComplete():
                feedback = self.nav.getFeedback()
                if feedback:
                    pass

            # 3. Evaluar el resultado al finalizar el movimiento
            result = self.nav.getResult()
            
            if result == TaskResult.SUCCEEDED:
                # Al llegar, informamos y esperamos instrucciones (Continuar o Saltar a otro sitio)
                self.decir(f"He llegado a {wp['name']}. ¿Qué hago ahora? (Continúo o voy a un lugar concreto)")

                # Bucle para esperar confirmación de voz o cambio de ruta
                confirmado = False
                while not confirmado:
                    orden = self.escuchar()
                    
                    # A. Comprobar si el usuario dijo un LUGAR ESPECÍFICO (Salto de índice con memoria)
                    idx_destino = self.buscar_destino_en_voz(orden, puntos)
                    
                    if idx_destino != -1:
                        # Si NO teníamos ya un desvío pendiente, guardamos el siguiente paso lógico
                        if indice_pendiente == -1:
                            indice_pendiente = i + 1
                            
                        # Si encontramos el nombre (ej: "ve al gimnasio"), actualizamos el índice 'i'
                        self.decir(f"Entendido, cambio de ruta temporal. Voy a {puntos[idx_destino]['name']}.")
                        i = idx_destino
                        confirmado = True # Salimos del bucle de escucha y el while principal va al nuevo 'i'
                    
                    # B. Confirmación positiva estándar ("sí", "sigue")
                    elif self.voz.contiene_palabra_clave_si(orden):
                        
                        # --- Recuperar ruta si estábamos de desvío ---
                        if indice_pendiente != -1:
                             self.decir(f"Terminado el desvío. Vuelvo a la ruta original hacia {puntos[indice_pendiente]['name'] if indice_pendiente < len(puntos) else 'fin'}.")
                             i = indice_pendiente
                             indice_pendiente = -1 # Reseteamos la memoria
                             confirmado = True
                        
                        else:
                            # Comportamiento normal (sin desvíos pendientes)
                            es_ultimo_punto = (i == len(puntos) - 1)
                            if es_ultimo_punto and es_ultima_fase:
                                self.decir("Era el último punto. Navegación completada.")
                                return "completada"
                            else:
                                self.decir("Entendido, prosigo al siguiente punto.")
                                i += 1 # Incremento normal
                                confirmado = True
                    
                    # C. Orden de detención
                    elif self.voz.contiene_palabra_clave_no(orden):
                        self.decir("Entendido, me detengo aquí. Misión cancelada.")
                        return "cancelada"
                    
                    # D. No entendido
                    else:
                        self.decir("No te he entendido. ¿Deseas que continúe o vaya a otro sitio?")
            else:
                # Si Nav2 falla al planificar o llegar
                self.decir(f"No he podido llegar a {wp['name']}")
                # Si falla, pasamos al siguiente automáticamente 
                i += 1


def main():
    # --- GESTIÓN DE ARGUMENTOS ---
    # Por defecto 'secuencial' si no se pone nada
    modo_seleccionado = "secuencial"
    if len(sys.argv) > 1:
        # Si se pone argumento, tomamos ese
        modo_seleccionado = sys.argv[1].lower()

    # Inicialización del sistema ROS2
    rclpy.init()
    
    # Instanciamos nuestra clase controladora
    navigator = WaypointNavigator()
    
    # --- EJECUCIÓN ÚNICA ---
    # Ejecuta el modo elegido y marca es_ultima_fase=True para que termine al acabar la lista
    navigator.ejecutar_navegacion(modo=modo_seleccionado, es_ultima_fase=True)

    navigator.service_node.destroy_node()
    
    # Cierre limpio de ROS2
    rclpy.shutdown()

if __name__ == '__main__':
    main()