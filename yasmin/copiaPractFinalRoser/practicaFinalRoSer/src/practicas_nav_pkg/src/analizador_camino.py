#!/usr/bin/env python3

"""
Módulo Analizador de Caminos
Proporciona herramientas para analizar la geometría de los caminos calculados por Nav2
y seleccionar automáticamente el controlador (PurePursuit o FollowPath) más adecuado.
"""

import math
from rcl_interfaces.srv import SetParameters
from rcl_interfaces.msg import Parameter, ParameterType, ParameterValue
import rclpy


class AnalizadorCamino:
    """
    Clase encargada de analizar los caminos generados por Nav2 y decidir
    qué controlador (local planner) es más adecuado según la geometría del camino.
    
    Criterios de decisión:
    - Caminos rectos (ratio > 0.75): Usa PurePursuit (rápido y suave)
    - Caminos con muchas curvas (ratio <= 0.75): Usa FollowPath (preciso y seguro)
    """

    def __init__(self, nav):
        """
        Constructor: Almacena una referencia al navegador para acceder a getPath().
        
        Args:
            nav: Instancia de BasicNavigator de Nav2.
        """
        self.nav = nav

    def calcular_indice_rectitud(self, start_pose, goal_pose):
        """
        Calcula el índice de rectitud del camino entre dos puntos.
        Este índice es un ratio que compara la distancia en línea recta
        con la longitud real del camino planificado.
        
        Fórmula:
        ratio = distancia_linea_recta / longitud_camino_real
        
        Un ratio cercano a 1.0 indica un camino casi perfectamente recto.
        Un ratio bajo (ej: 0.5) indica muchas curvas y rodeos.
        
        Args:
            start_pose (PoseStamped): Pose inicial del movimiento.
            goal_pose (PoseStamped): Pose destino del movimiento.
            
        Returns:
            tuple: (ratio, distancia_linea_recta, longitud_camino_real)
                Si no se puede calcular, retorna (1.0, 0, 0) por seguridad.
        """
        # Obtenemos el path planificado desde start hasta goal
        path = self.nav.getPath(start_pose, goal_pose)
        
        # Validación: Si el path es inválido o vacío, asumimos camino recto por defecto
        if not path or not path.poses:
            print("[Analizador] No se pudo calcular path previo. Usando ratio=1.0 (recto por defecto).")
            return 1.0, 0, 0

        # Extraemos la lista de poses del path
        poses = path.poses
        
        # === CÁLCULO 1: Longitud real del camino ===
        # Sumamos la distancia euclídea entre cada par de puntos consecutivos
        longitud_camino_real = 0.0
        
        for i in range(len(poses) - 1):
            # Obtenemos las posiciones de dos puntos consecutivos
            p1 = poses[i].pose.position
            p2 = poses[i + 1].pose.position
            
            # Distancia euclídea: sqrt((x2-x1)^2 + (y2-y1)^2)
            dist_segmento = math.hypot(p2.x - p1.x, p2.y - p1.y)
            longitud_camino_real += dist_segmento

        # === CÁLCULO 2: Distancia en línea recta (inicio -> fin) ===
        # Esta es la menor distancia posible entre dos puntos
        start_pos = poses[0].pose.position
        end_pos = poses[-1].pose.position
        distancia_linea_recta = math.hypot(end_pos.x - start_pos.x, end_pos.y - start_pos.y)

        # === CÁLCULO 3: Índice de Rectitud (Ratio) ===
        # Evitamos división por cero en caso de estar en el mismo sitio
        if longitud_camino_real == 0:
            return 1.0, 0, 0

        # ratio = distancia_recta / distancia_real
        # Rango: [0, 1]
        ratio = distancia_linea_recta / longitud_camino_real

        return ratio, distancia_linea_recta, longitud_camino_real

    def seleccionar_controlador(self, start_pose, goal_pose, umbral=0.75):
        """
        Selecciona automáticamente el controlador local más adecuado según la geometría.
        
        Lógica:
        - Si ratio > umbral (default 0.75): El camino es bastante recto -> PurePursuit
        - Si ratio <= umbral: Hay muchas curvas -> FollowPath (más preciso)
        
        Args:
            start_pose (PoseStamped): Pose inicial.
            goal_pose (PoseStamped): Pose destino.
            umbral (float): Valor de ratio a partir del cual se considera "recto".
                Por defecto 0.75 (75% de la línea recta).
                
        Returns:
            str: Nombre del controlador ("PurePursuit" o "FollowPath").
        """
        # Calculamos el índice de rectitud del camino
        ratio, dist_recta, dist_camino = self.calcular_indice_rectitud(start_pose, goal_pose)

        # Imprimimos análisis detallado para debugging y auditoría
        print(f"[Análisis de Camino] Dist.Recta: {dist_recta:.2f}m | "
              f"Dist.Camino: {dist_camino:.2f}m | Ratio: {ratio:.2f}")

        # Aplicamos el umbral para decidir el controlador
        # Si el camino es suficientemente recto, usamos PurePursuit (más rápido)
        if ratio > umbral:
            print(f"[Decisión] Ratio {ratio:.2f} > {umbral} -> Usando PurePursuit (rápido/suave)")
            return "PurePursuit"
        else:
            # Si hay muchas curvas, usamos FollowPath (más preciso)
            print(f"[Decisión] Ratio {ratio:.2f} <= {umbral} -> Usando FollowPath (preciso)")
            return "FollowPath"

    def cambiar_controlador_por_servicio(self, cliente_servicio, nuevo_controlador, nodo_auxiliar):
        """
        Cambia el controlador local mediante una llamada al servicio set_parameters.
        Este método implementa la lógica requerida por el examen para cambiar dinámicamente
        los parámetros del controlador del servidor de Nav2.
        
        Args:
            cliente_servicio: Cliente de ROS2 para el servicio set_parameters.
            nuevo_controlador (str): Nombre del controlador a activar.
            nodo_auxiliar: Nodo auxiliar para hacer spin temporal (rclpy.Node).
        """
        # Verificamos que el servicio esté disponible antes de intentar contactarlo
        if not cliente_servicio.service_is_ready():
            print("[Cambio Controlador] Servicio set_parameters no disponible aún.")
            return

        # Preparamos la petición al servicio
        req = SetParameters.Request()
        
        # Creamos el parámetro que queremos cambiar
        param = Parameter()
        param.name = 'FollowPath.plugin'  # Nombre teórico del parámetro a cambiar
        
        # Asignamos el nuevo valor (string con el nombre del controlador)
        param.value = ParameterValue(
            type=ParameterType.PARAMETER_STRING,
            string_value=nuevo_controlador
        )
        
        # Agregamos el parámetro a la petición
        req.parameters = [param]

        # Hacemos la llamada asíncrona al servicio
        future = cliente_servicio.call_async(req)
        
        # Hacemos un spin corto del nodo auxiliar para enviar la petición
        # Con timeout de 0.1s para no bloquear demasiado
        try:
            rclpy.spin_until_future_complete(nodo_auxiliar, future, timeout_sec=0.1)
            print(f"[Cambio Controlador] Solicitado cambio a: {nuevo_controlador}")
        except Exception as e:
            print(f"[Cambio Controlador] Error en la petición: {e}")

    def calcular_distancia_euclidea(self, pose1, pose2):
        """
        Utilidad: Calcula la distancia euclídea entre dos posiciones.
        
        Args:
            pose1 (PoseStamped): Primera pose.
            pose2 (PoseStamped): Segunda pose.
            
        Returns:
            float: Distancia euclídea en metros.
        """
        p1 = pose1.pose.position
        p2 = pose2.pose.position
        return math.hypot(p2.x - p1.x, p2.y - p1.y)
