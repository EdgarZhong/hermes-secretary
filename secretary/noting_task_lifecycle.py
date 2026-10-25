"""Join a Noting execution with settlement of its own Framework carriers.

The worker never waits for Main. A queued carrier retains the existing task
owner until publication or retirement, without adding durable pending work.
"""

import logging
import threading

logger = logging.getLogger(__name__)


class NotingTaskLifecycle:
    def __init__(self):
        self._lock = threading.Lock()
        self._pending = set()
        self._cleanup = None
        self._execution_done = False

    def carrier(self):
        token = object()
        with self._lock:
            self._pending.add(token)

        def settled():
            with self._lock:
                self._pending.discard(token)
                ready = self._execution_done and not self._pending and self._cleanup is not None
            if ready:
                # Settlement can be called inside a publisher's outer Framework
                # or persistence lock. Only the already-finished worker's tail
                # cleanup moves to a native context-scoped thread.
                self._dispatch_cleanup()

        return settled

    def execution_finished(self, cleanup):
        with self._lock:
            self._execution_done = True
            self._cleanup = cleanup
            ready = not self._pending
        if ready:
            self._run_cleanup()

    def _run_cleanup(self):
        with self._lock:
            if not self._execution_done or self._pending:
                return
            cleanup, self._cleanup = self._cleanup, None
        if cleanup is not None:
            cleanup()

    def _deferred_cleanup(self):
        try:
            self._run_cleanup()
        except Exception:
            logger.warning("Noting task final cleanup failed", exc_info=True)
        return False

    def _dispatch_cleanup(self):
        try:
            from agent.memory_provider import spawn_context_thread
            spawn_context_thread(self._deferred_cleanup, name="noting-task-close", daemon=True).start()
        except Exception:
            logger.warning("Noting close worker unavailable; using native timer", exc_info=True)
            # The callback stays owned until a runner actually claims it. Even
            # if both dispatch mechanisms fail, do not mark cleanup completed.
            from agent.periodic_scheduler import schedule
            schedule(self._deferred_cleanup, 0.01)


def task_lifecycle(child):
    lifecycle = getattr(child, "_secretary_task_lifecycle", None)
    if lifecycle is None:
        lifecycle = child._secretary_task_lifecycle = NotingTaskLifecycle()
    return lifecycle
