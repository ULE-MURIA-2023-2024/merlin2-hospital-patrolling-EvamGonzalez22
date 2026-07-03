(define (problem exercise0-problem-ext)
  (:domain exercise0-ext)

  (:objects
    robot1 robot2 - robot
    loc1 loc2 loc3 - location
    box1 box2 - object
  )

  (:init
    (at-robot robot1 loc1)
    (at-robot robot2 loc2)
    (at-object box1 loc1)
    (at-object box2 loc3)
    (mobile robot2) ; robot1 is stationary
    (can-lift robot1 box1) ; ONLY robot1 can pick up box1
    (can-lift robot2 box2) ; robot2 can lift box2
  )

  (:goal
    (and
      (at-object box1 loc2)
      (at-object box2 loc1)
    )
  )
)
