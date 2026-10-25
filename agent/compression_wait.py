"""Progress-aware pre-commit wait shared by native compression hosts."""

import concurrent.futures
import logging
import time
from typing import Any, Tuple

logger = logging.getLogger("agent.conversation_compression")

def _await_worker_within_budget(
    future: Any, fence: Any, *, idle: float, ceiling: float, wait_started: float
) -> Tuple[bool, Any]:
    """Poll ``future`` under the idle budget + ceiling; ``(True, result)`` when it settled."""
    while True:
        waited = time.monotonic() - wait_started
        remaining_ceiling = ceiling - waited
        if remaining_ceiling <= 0:
            return False, None
        # Charge idle budget from LAST PROGRESS, not slice start, or silence could approach 2x the budget.
        since_progress = fence.seconds_since_progress()
        wait_slice = min(max(idle - since_progress, 0.005), remaining_ceiling)
        try:
            return True, future.result(timeout=wait_slice)
        except concurrent.futures.TimeoutError:
            # Aliases builtin TimeoutError (3.11+): also fires when the WORKER died with one (#63892).
            # A settled future never unsettles — re-waiting spun ~2k iter/s; take the stall path now.
            if future.done():
                exc = future.exception()
                if exc is None:
                    return True, future.result()
                logger.info("Context compression worker exited with %r — taking the stall path", exc)
                return False, None
            waited = time.monotonic() - wait_started
            since_progress = fence.seconds_since_progress()
            if not fence.deadline_exceeded and since_progress < idle and waited < ceiling:
                logger.info(
                    "Context compression still streaming after %.0fs (last progress %.1fs ago) — extending wait (ceiling %.0fs)",
                    waited, since_progress, ceiling,
                )
                continue
            return False, None

