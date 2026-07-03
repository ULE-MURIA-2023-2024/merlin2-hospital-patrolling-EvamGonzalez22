#!/usr/bin/env python3

"""
Navegador FSM con YASMIN para ROSER.
Gestiona la transicion entre waypoints mediante una maquina de estados finita.
"""

import os
import random
import sys
import yaml

import rclpy
from rclpy.node import Node
from ament_index_python.packages import get_package_share_directory
from geometry_msgs.msg import PoseStamped
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
from rcl_interfaces.srv import SetParameters
from rcl_interfaces.msg import Parameter, ParameterType, ParameterValue
from nav2_msgs.action import NavigateToPose

import yasmin
from yasmin import Blackboard, State, StateMachine
from yasmin_ros import ActionState, ServiceState
from yasmin_ros.basic_outcomes import SUCCEED, ABORT, CANCEL
from yasmin_viewer import YasminViewerPub

from controlador_voz import ControladorVoz
from analizador_camino import AnalizadorCamino


def create_pose(nav: BasicNavigator, wp: dict) -> PoseStamped:
    """Convierte un waypoint del YAML a PoseStamped."""
    pose = PoseStamped()
    pose.header.frame_id = "map"
    pose.header.stamp = nav.get_clock().now().to_msg()
    pose.pose.position.x = float(wp["x"])
    pose.pose.position.y = float(wp["y"])
    pose.pose.orientation.w = 1.0
    return pose


class LoadWaypointState(State):
    """Carga el siguiente waypoint y prepara la meta de navegacion."""

    def __init__(self) -> None:
        super().__init__(["loaded", "finished"])

    def execute(self, blackboard: Blackboard) -> str:
        idx = blackboard["current_index"]
        points = blackboard["waypoints"]

        if idx >= len(points):
            yasmin.YASMIN_LOG_INFO("No quedan waypoints. Finalizando mision.")
            return "finished"

        wp = points[idx]
        blackboard["current_wp"] = wp
        blackboard["goal_pose"] = create_pose(blackboard["nav"], wp)

        yasmin.YASMIN_LOG_INFO(
            f"Waypoint {idx + 1}/{len(points)}: {wp['name']}"
        )
        return "loaded"


class SelectControllerState(ServiceState):
    """Selecciona y aplica el controlador local mediante servicio ROS 2."""

    def __init__(self) -> None:
        super().__init__(
            SetParameters,
            "/controller_server/set_parameters",
            self.create_request_handler,
            None,
            self.response_handler,
        )

    def create_request_handler(self, blackboard: Blackboard) -> SetParameters.Request:
        idx = blackboard["current_index"]
        points = blackboard["waypoints"]

        if idx == 0:
            selected = "FollowPath"
        else:
            start_pose = create_pose(blackboard["nav"], points[idx - 1])
            selected = blackboard["analizador"].seleccionar_controlador(
                start_pose,
                blackboard["goal_pose"],
            )

        blackboard["selected_controller"] = selected

        # Preparamos peticion del servicio
        req = SetParameters.Request()
        param = Parameter()
        param.name = "FollowPath.plugin"
        param.value = ParameterValue(
            type=ParameterType.PARAMETER_STRING,
            string_value=selected
        )
        req.parameters = [param]
        return req

    def response_handler(self, blackboard: Blackboard, response: SetParameters.Response) -> str:
        selected = blackboard["selected_controller"]
        yasmin.YASMIN_LOG_INFO(f"Controlador activo: {selected}")
        return SUCCEED


class NavigateState(ActionState):
    """Ejecuta la navegacion al waypoint actual usando action de Nav2."""

    def __init__(self) -> None:
        super().__init__(
            NavigateToPose,
            "/navigate_to_pose",
            self.create_goal_handler,
            None,
            self.response_handler,
        )

    def create_goal_handler(self, blackboard: Blackboard) -> NavigateToPose.Goal:
        wp = blackboard["current_wp"]
        selected = blackboard.get("selected_controller", "FollowPath")
        blackboard["voz"].decir(f"Voy a {wp['name']} usando {selected}")
        
        goal = NavigateToPose.Goal()
        goal.pose = blackboard["goal_pose"]
        return goal

    def response_handler(self, blackboard: Blackboard, response: NavigateToPose.Result) -> str:
        wp = blackboard["current_wp"]
        yasmin.YASMIN_LOG_INFO(f"Llegada correcta a {wp['name']}")
        blackboard["voz"].decir(f"He llegado a {wp['name']}")
        return SUCCEED


class AskContinueState(State):
    """Pregunta al usuario si continuar con el siguiente waypoint."""

    def __init__(self) -> None:
        super().__init__(["continue", "stop"])

    def execute(self, blackboard: Blackboard) -> str:
        blackboard["voz"].decir("Deseas que continue al siguiente punto?")
        order = blackboard["voz"].escuchar()

        if blackboard["voz"].contiene_palabra_clave_no(order):
            blackboard["voz"].decir("Detengo la mision.")
            return "stop"

        # Si no se entiende, por defecto continua para no bloquear.
        return "continue"


class AdvanceWaypointState(State):
    """Avanza el indice de waypoint para la siguiente iteracion."""

    def __init__(self) -> None:
        super().__init__(["next"])

    def execute(self, blackboard: Blackboard) -> str:
        blackboard["current_index"] += 1
        return "next"


def build_waypoint_list(mode: str) -> list:
    """Carga waypoints desde YAML y aplica modo secuencial/aleatorio."""
    pkg_path = get_package_share_directory("practicas_nav_pkg")
    yaml_path = os.path.join(pkg_path, "config", "waypoints.yaml")

    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    points = data["waypoints"]
    if mode == "aleatorio":
        random.shuffle(points)

    return points


def main() -> None:
    mode = "secuencial"
    if len(sys.argv) > 1:
        mode = sys.argv[1].strip().lower()

    rclpy.init()

    nav = BasicNavigator()
    voz = ControladorVoz()
    analizador = AnalizadorCamino(nav)

    waypoints = build_waypoint_list(mode)
    nav.waitUntilNav2Active()

    blackboard = Blackboard()
    blackboard["mode"] = mode
    blackboard["waypoints"] = waypoints
    blackboard["current_index"] = 0
    blackboard["nav"] = nav
    blackboard["voz"] = voz
    blackboard["analizador"] = analizador

    sm = StateMachine(outcomes=["succeeded", "cancelled", "aborted"], handle_sigint=True)
    sm.add_state(
        "LOAD_WAYPOINT",
        LoadWaypointState(),
        transitions={
            "loaded": "SELECT_CONTROLLER",
            "finished": "succeeded",
        },
    )
    sm.add_state(
        "SELECT_CONTROLLER",
        SelectControllerState(),
        transitions={
            SUCCEED: "NAVIGATE",
            ABORT: "NAVIGATE",
        },
    )
    sm.add_state(
        "NAVIGATE",
        NavigateState(),
        transitions={
            SUCCEED: "ASK_CONTINUE",
            ABORT: "ADVANCE_WAYPOINT",
            CANCEL: "cancelled",
        },
    )
    sm.add_state(
        "ASK_CONTINUE",
        AskContinueState(),
        transitions={
            "continue": "ADVANCE_WAYPOINT",
            "stop": "cancelled",
        },
    )
    sm.add_state(
        "ADVANCE_WAYPOINT",
        AdvanceWaypointState(),
        transitions={
            "next": "LOAD_WAYPOINT",
        },
    )

    YasminViewerPub(sm, "ROSER_FSM_NAV")

    try:
        outcome = sm(blackboard)
        yasmin.YASMIN_LOG_INFO(f"FSM finalizada con outcome: {outcome}")
    except Exception as exc:
        yasmin.YASMIN_LOG_WARN(f"Error en FSM: {exc}")
    finally:
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
