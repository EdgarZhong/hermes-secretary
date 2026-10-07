"""A16 / 02 §5.1: the old Background Self-Improvement Review no longer runs.

The automatic post-turn review and the explicit ``/refine`` entry both funnel into
``AIAgent._spawn_background_review`` → ``spawn_background_review_thread``. With the gate
permanently disabled and the spawn entry refusing, no fork is ever constructed — while the
retained fork machinery (cache parity, the run worker) stays intact behind the gate for the
Noting child runtime and ``/btw``.
"""

import contextvars
import time
from types import SimpleNamespace

import agent.background_review as bg
import run_agent as run_agent_module
from run_agent import AIAgent


class _ImmediateThread:
    """Drop-in for ``threading.Thread`` that runs the target inline."""

    def __init__(self, *, target, daemon=None, name=None):
        self._target = target

    def start(self):
        self._target()


def _bare_agent() -> AIAgent:
    agent = object.__new__(AIAgent)
    agent.session_id = "retired-session"
    agent._delegate_depth = 0
    agent._MEMORY_REVIEW_PROMPT = "review memory"
    agent._SKILL_REVIEW_PROMPT = "review skills"
    agent._COMBINED_REVIEW_PROMPT = "review both"
    return agent


def _record_forks(monkeypatch):
    forks = []

    class FakeReviewAgent:
        def __init__(self, **kwargs):
            forks.append(kwargs)

    monkeypatch.setattr(run_agent_module, "AIAgent", FakeReviewAgent)
    monkeypatch.setattr(run_agent_module.threading, "Thread", _ImmediateThread)
    return forks


def test_automatic_post_turn_review_never_spawns(monkeypatch):
    forks = _record_forks(monkeypatch)
    agent = _bare_agent()

    AIAgent._spawn_background_review(
        agent, messages_snapshot=[{"role": "user", "content": "hi"}],
        review_memory=True, review_skills=True,
    )

    assert forks == []


def test_old_switch_set_in_config_changes_nothing(monkeypatch):
    from hermes_constants import get_hermes_home

    (get_hermes_home() / "config.yaml").write_text(
        "auxiliary:\n  background_review:\n    enabled: true\n", encoding="utf-8")
    forks = _record_forks(monkeypatch)
    agent = _bare_agent()

    AIAgent._spawn_background_review(
        agent, messages_snapshot=[{"role": "user", "content": "hi"}], review_memory=True)

    assert forks == []
    assert bg.load_background_review_settings() == (False, {})


def test_explicit_refine_call_builds_no_fork_and_completes_the_handshake(monkeypatch):
    forks = _record_forks(monkeypatch)
    agent = _bare_agent()

    AIAgent._spawn_background_review(
        agent, messages_snapshot=[{"role": "user", "content": "hi"}],
        review_memory=True, focus="save the deploy workflow", explicit=True,
    )

    assert forks == []
    # The retired target completes the run token, so a live turn's cancellation path never
    # waits out its bounded deadline on a review that will not start.
    assert getattr(agent, "_background_review_run", None) is None


def test_queue_dispatch_can_never_resurrect_a_review(monkeypatch):
    from agent.review_idle_queue import ReviewIdleQueue, _PendingReview

    spawned = []
    agent = SimpleNamespace(session_id="sess", _spawn_background_review_now=lambda **kw: spawned.append(kw))
    queue = ReviewIdleQueue()
    queue._ensure_thread = lambda: None
    item = _PendingReview(agent, "sess", {}, time.monotonic(), contextvars.copy_context())

    assert queue._still_enabled(item) is False
    queue._dispatch(item)
    assert spawned == []


def test_gate_opened_explicitly_still_reaches_the_retained_machinery(monkeypatch):
    """The machinery below the retired gate is intact: a caller that patches the gate open
    (the legacy machinery tests) still reaches the run worker and the prompt assembly."""
    calls = []
    monkeypatch.setattr(bg, "load_background_review_settings", lambda: (True, {}))
    monkeypatch.setattr(bg, "_run_review_in_thread", lambda *args, **kwargs: calls.append(kwargs))

    target, prompt = bg.spawn_background_review_thread(
        SimpleNamespace(session_id="s"), [], review_memory=True, review_skills=False)
    target()

    assert prompt == bg._MEMORY_REVIEW_PROMPT
    assert calls and calls[0]["review_memory"] is True


def test_shared_machinery_remains_importable_for_noting_and_btw():
    from agent.cache_parity import apply_cache_parity_from_parent, parent_cache_parity_kwargs

    assert callable(bg.build_cache_parity_fork)
    assert callable(parent_cache_parity_kwargs)
    assert callable(apply_cache_parity_from_parent)
