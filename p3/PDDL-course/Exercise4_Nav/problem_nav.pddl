(define (problem nav_prob)
  (:domain waypoints_nav)
  (:objects
    r1 - bot
    wp1 wp2 wp3 wp4 wp5 - waypoint
    package1 - item
  )
  (:init
    (at-bot r1 wp1)
    (hand-empty r1)
    (at-item package1 wp2)
    (connected wp1 wp2) (connected wp2 wp1)
    (connected wp2 wp3) (connected wp3 wp2)
    (connected wp3 wp4) (connected wp4 wp3)
    (connected wp4 wp5) (connected wp5 wp4)
    (connected wp2 wp5) (connected wp5 wp2)
    
    (clear wp1) (clear wp2) (clear wp3) (clear wp4)
    ; wp5 missing 'clear', indicates an obstacle
  )
  (:goal
    (and
      (at-item package1 wp5)
      (at-bot r1 wp1)
    )
  )
)
