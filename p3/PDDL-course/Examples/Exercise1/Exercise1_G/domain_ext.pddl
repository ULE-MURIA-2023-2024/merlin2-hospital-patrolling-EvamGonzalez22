(define (domain exercise0-ext)
  (:requirements :strips :typing :negative-preconditions :disjunctive-preconditions :equality)

  (:types robot location object)

  (:predicates
    (at-robot ?r - robot ?loc - location)
    (at-object ?o - object ?loc - location)
    (holding ?r - robot ?o - object)
    (mobile ?r - robot)
    (can-lift ?r - robot ?o - object)
  )

  (:action move
    :parameters (?r - robot ?from - location ?to - location)
    :precondition (and (at-robot ?r ?from) (not (= ?from ?to)) (mobile ?r))
    :effect (and (not (at-robot ?r ?from)) (at-robot ?r ?to))
  )

  (:action pick_up
    :parameters (?r - robot ?o - object ?loc - location)
    :precondition (and (at-robot ?r ?loc) (at-object ?o ?loc) (can-lift ?r ?o))
    :effect (and (not (at-object ?o ?loc)) (holding ?r ?o))
  )

  (:action put_down
    :parameters (?r - robot ?o - object ?loc - location)
    :precondition (and (holding ?r ?o) (at-robot ?r ?loc))
    :effect (and (not (holding ?r ?o)) (at-object ?o ?loc))
  )

  (:action pass_object
    :parameters (?from_r - robot ?to_r - robot ?o - object ?loc - location)
    :precondition (and (at-robot ?from_r ?loc) (at-robot ?to_r ?loc) (holding ?from_r ?o) (not (= ?from_r ?to_r)))
    :effect (and (not (holding ?from_r ?o)) (holding ?to_r ?o))
  )
)
