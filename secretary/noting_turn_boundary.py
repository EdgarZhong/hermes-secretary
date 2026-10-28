"""Observe Secretary Turns only inside an accepted native durable lease boundary."""


def observe_admitted_turn_started(parent, lease):
    if lease is not None:
        from secretary.noting_runtime import note_main_turn_started
        return note_main_turn_started(parent)
    return False


def observe_admitted_turn_finished(parent, lease):
    if lease is not None:
        from secretary.noting_runtime import note_main_turn_finished
        return note_main_turn_finished(parent)
    return False
