(define (problem robot_problem)
  (:domain robot_transport)
  (:objects
    room1 room2 room3 - location
    box - object
  )
  (:init
    (robot_at room1)
    (object_at box room1)
    (connected room1 room2) (connected room2 room1)
    (connected room2 room3) (connected room3 room2)
    (hand_empty)
    (battery-high)
    (has-charger room2) ; Charger in intermediate room
  )
  (:goal
    (and (object_at box room3))
  )
)
