import rclpy
from yasmin import StateMachine, State

class NavigateState(State):
    def __init__(self):
        super().__init__(outcomes=['reached', 'failed'])
    def execute(self, blackboard):
        print(f"Navegando a la habitación...")
        # Aquí irá la lógica de Nav2
        return 'reached'

class RotateState(State):
    def __init__(self):
        super().__init__(outcomes=['rotated'])
    def execute(self, blackboard):
        print(f"Girando 360 grados...")
        # Aquí irá la lógica de giro /cmd_vel
        return 'rotated'

class AnnounceState(State):
    def __init__(self):
        super().__init__(outcomes=['done'])
    def execute(self, blackboard):
        print(f"¡Habitación patrullada con éxito!")
        return 'done'

def create_patrol_fsm():
    sm = StateMachine(outcomes=['patrol_completed', 'patrol_failed'])
    sm.add_state('NAVIGATE', NavigateState(), transitions={'reached': 'ROTATE', 'failed': 'patrol_failed'})
    sm.add_state('ROTATE', RotateState(), transitions={'rotated': 'ANNOUNCE'})
    sm.add_state('ANNOUNCE', AnnounceState(), transitions={'done': 'patrol_completed'})
    return sm
