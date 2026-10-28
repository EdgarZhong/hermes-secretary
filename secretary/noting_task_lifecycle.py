"""Task cleanup follows execution completion, independently of queued Framework delivery."""


class NotingTaskLifecycle:
    def carrier(self):
        return lambda: None

    def execution_finished(self, cleanup):
        cleanup()


def task_lifecycle(child):
    lifecycle = getattr(child, "_secretary_task_lifecycle", None)
    if lifecycle is None:
        lifecycle = child._secretary_task_lifecycle = NotingTaskLifecycle()
    return lifecycle
