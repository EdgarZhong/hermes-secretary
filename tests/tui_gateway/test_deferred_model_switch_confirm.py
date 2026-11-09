"""A model picked mid-turn must still get its selection-guard confirm step.

``config.set model`` on a *running* session cannot swap the agent in place --
the worker thread is reading ``agent.model`` / ``agent.client`` on every
iteration -- so it stashes the pick in ``session["pending_model_switch"]`` and
``_apply_pending_model_switch`` applies it at the next turn start.

That deferral used to skip the selection guards entirely: the stash branch
answered ``confirm_required: False`` without ever calling them. A client that
implements the confirm round-trip was therefore told no consent was needed, so
it never prompted. One turn later ``_apply_pending_model_switch`` ran the
guards with the stashed (unconfirmed) flag, saw the warning, and deliberately
dropped the switch -- correct on its own terms, but by then no round-trip was
possible. The user's pick silently reverted and the confirm was never offered
on this path at all.
"""

import threading
import types

import pytest

from tui_gateway import server
from tests.tui_gateway.test_pending_native_turn import live as _native_live  # noqa: F401 -- real native fixture
from tests.tui_gateway.test_pending_native_turn import begin, rpc, settled


@pytest.fixture
def native_context(request, monkeypatch):
    _control_context_dependencies(monkeypatch)
    return request.getfixturevalue("_native_live")

# A vendor-documented data-training tier. The data-policy guard keys on the
# model id alone (no base_url / api_key / model_info), which is exactly what
# the stash branch can see before resolution.
GUARDED_MODEL = "muse-spark-1.2-contributor"
UNGUARDED_MODEL = "anthropic/claude-sonnet-4.6"

def _session(**extra):
    return {
        "agent": types.SimpleNamespace(),
        "session_key": "session-key",
        "history": [],
        "history_lock": threading.Lock(),
        "history_version": 0,
        "running": False,
        "attached_images": [],
        "image_counter": 0,
        "cols": 80,
        "slash_worker": None,
        "show_reasoning": False,
        "tool_progress_mode": "all",
        **extra,
    }

def _config_set_model(value, **extra_params):
    params = {"session_id": "sid", "key": "model", "value": value}
    params.update(extra_params)

    return server.handle_request({"id": "1", "method": "config.set", "params": params})

@pytest.fixture
def running_session(monkeypatch):
    """A busy session whose live swap path is fatal if it is ever reached."""

    def _must_not_run(*_args, **_kwargs):
        raise AssertionError(
            "_apply_model_switch ran on the busy path -- it would race the "
            "worker thread reading agent.model / agent.client"
        )

    monkeypatch.setattr(server, "_apply_model_switch", _must_not_run)
    server._sessions["sid"] = _session(running=True)
    try:
        yield server._sessions["sid"]
    finally:
        server._sessions.pop("sid", None)

class TestGuardedPickAsksBeforeStashing:
    def test_reports_confirm_required_instead_of_deferring(self, running_session):
        resp = _config_set_model(GUARDED_MODEL)

        assert not resp.get("error")
        result = resp["result"]
        assert result["confirm_required"] is True, (
            "the deferred path answered confirm_required=False without running "
            "the guards, so a correct client never prompts and the pick is "
            "dropped a turn later with no way to consent"
        )
        assert result["confirm_message"].strip()
        assert result["deferred"] is False

    def test_leaves_the_session_untouched(self, running_session):
        _config_set_model(GUARDED_MODEL)

        assert "pending_model_switch" not in running_session, (
            "an unconfirmed guarded pick must not be queued -- the next turn "
            "start would drop it anyway, after the pill already moved"
        )

    def test_reconfirming_queues_the_pick(self, running_session):
        resp = _config_set_model(GUARDED_MODEL, confirm_expensive_model=True)

        result = resp["result"]
        assert result["deferred"] is True
        assert result["confirm_required"] is False

        pending = running_session["pending_model_switch"]
        assert pending["raw"] == GUARDED_MODEL
        assert pending["confirm_expensive_model"] is True, (
            "the ack must survive into the stash or _apply_pending_model_switch "
            "re-runs the guard at turn start and drops the confirmed pick"
        )

class TestUnguardedPickStillDefers:
    """The queue-don't-race behaviour is the whole point of this branch."""

    def test_defers_without_a_confirm_step(self, running_session):
        result = _config_set_model(UNGUARDED_MODEL)["result"]

        assert result["deferred"] is True
        assert result["confirm_required"] is False
        assert result["confirm_message"] == ""
        assert result["value"] == UNGUARDED_MODEL

    def test_stashes_the_pick_for_the_next_turn(self, running_session):
        _config_set_model(UNGUARDED_MODEL)

        pending = running_session["pending_model_switch"]
        assert pending["raw"] == UNGUARDED_MODEL
        assert pending["confirm_expensive_model"] is False

    def test_explicit_provider_is_still_recorded_for_display(self, running_session):
        _config_set_model(f"{UNGUARDED_MODEL} --provider anthropic")

        pending = running_session["pending_model_switch"]
        assert pending["display_provider"] == "anthropic"

class TestGuardFailureIsNotFatal:
    def test_a_raising_guard_falls_back_to_deferring(self, running_session, monkeypatch):
        """A broken guard must never cost the user their model pick.

        The apply-time check in ``_apply_pending_model_switch`` is still there,
        so failing open here degrades to the old behaviour rather than to a
        silently unguarded switch.
        """

        def _boom(*_args, **_kwargs):
            raise RuntimeError("guard table is broken")

        monkeypatch.setattr(
            "hermes_cli.model_selection_guards.combined_selection_warning", _boom
        )

        result = _config_set_model(GUARDED_MODEL)["result"]

        assert result["deferred"] is True
        assert running_session["pending_model_switch"]["raw"] == GUARDED_MODEL


def _assert_context_identity(info, context, *, display, actual, pending, provider=None):
    from tui_gateway.contracts.common import SessionLiveInfo
    assert info["model"] == display
    assert info["context_model"] == context["model"] == actual
    assert info["model_switch_pending"] is pending
    assert info["context_provider"] == provider
    typed = SessionLiveInfo.model_validate(info).model_dump()
    assert typed["context_model"] == actual
    assert typed["model_switch_pending"] is pending
    assert typed["context_provider"] == provider


def _control_context_dependencies(monkeypatch):
    import io
    import httpx
    import requests
    monkeypatch.setattr(server, "_probe_credentials", lambda agent: None)
    monkeypatch.setattr("hermes_cli.banner.get_update_result", lambda **kw: None)
    monkeypatch.setattr("hermes_cli.banner.get_available_skills", lambda: {})
    monkeypatch.setattr("hermes_cli.model_catalog._fetch_manifest", lambda *a, **kw: None)
    monkeypatch.setattr("hermes_cli.models._urlopen_model_catalog_request", lambda *a, **kw: io.BytesIO(b'{"data": []}'))
    # Only external metadata HTTP is supplied; all Context/native switch code remains real.
    monkeypatch.setattr(httpx.Client, "send", lambda self, request, **kw: httpx.Response(
        200, json={"data": [{"id": "test/next", "context_length": 256000}]}, request=request))
    def metadata_response(self, request, **kwargs):
        response = requests.Response()
        response.status_code = 200
        response._content = b"{}"
        response.request = request
        return response
    monkeypatch.setattr(requests.Session, "send", metadata_response)


def test_native_pending_context_identity_survives_activate_resume_and_second_pick(native_context, monkeypatch):
    """Read the actual Agent's Context while the actual native Turn waits on its provider."""
    live = native_context
    _control_context_dependencies(monkeypatch)
    live.session["profile_home"] = None  # the formal launch Profile is represented by None
    run = begin(live, monkeypatch, provider_wait=30)
    actual = live.agent.model
    _assert_context_identity(server._session_info(live.agent, live.session),
        rpc("session.context_breakdown")["result"], display=actual, actual=actual, pending=False)
    prompt = live.agent._cached_system_prompt
    before = live.db.get_messages("stored")
    for target, selected_provider in ((actual, "anthropic"), ("test/next", ""), ("test/latest", "")):
        value = f"{target} --provider {selected_provider}" if selected_provider else target
        response = rpc("config.set", key="model", value=value, confirm_expensive_model=True)
        assert response["result"]["deferred"] is True
        context = rpc("session.context_breakdown")["result"]
        info = server._session_info(live.agent, live.session)
        assert info["provider"] == selected_provider
        _assert_context_identity(info, context, display=target, actual=actual, pending=True)
        for method, params in (("session.activate", {"omit_messages": True}),
                               ("session.resume", {"session_id": "stored", "omit_messages": True})):
            result = rpc(method, **params)
            assert "error" not in result, result
            assert result["result"]["session_id"] == "runtime"
            _assert_context_identity(result["result"]["info"], context,
                                     display=target, actual=actual, pending=True)
        assert live.agent._cached_system_prompt == prompt
        assert live.db.get_messages("stored") == before
        assert len(run.calls) == 1  # projection/config acknowledgement never dispatch a model
    run.release.set()
    settled(live)
    assert live.agent.model == actual  # ending this Turn does not apply the next-Turn choice
    from unittest.mock import patch
    monkeypatch.setattr(server, "_restart_slash_worker", lambda *args: None)
    with (patch("agent.process_bootstrap.OpenAI"),
          patch("agent.model_metadata.fetch_model_metadata", return_value={})):
        successor = begin(live, monkeypatch, provider_wait=30)
        assert "pending_model_switch" not in live.session
        _assert_context_identity(rpc("session.activate", omit_messages=True)["result"]["info"],
            rpc("session.context_breakdown")["result"], display="test/latest", actual="test/latest", pending=False)
        assert len(successor.calls) == 1
        successor.release.set()
        settled(live)


def test_native_pending_apply_publishes_the_new_context_identity(native_context, monkeypatch):
    from unittest.mock import patch
    live = native_context
    _control_context_dependencies(monkeypatch)
    # An isolated compute-host uses the same native deferred configuration path even while idle.
    live.session["_compute_host_active"] = True
    assert rpc("config.set", key="model", value="test/next", confirm_expensive_model=True)["result"]["deferred"]
    live.session.pop("_compute_host_active")
    # Control external client construction/metadata only; the native switch, persistence and marker run.
    monkeypatch.setattr(server, "_restart_slash_worker", lambda *args: None)
    with (patch("agent.process_bootstrap.OpenAI"),
          patch("agent.model_metadata.fetch_model_metadata", return_value={})):
        server._apply_pending_model_switch("runtime", live.session)
    assert "pending_model_switch" not in live.session
    assert live.agent.model == "test/next"
    context = rpc("session.context_breakdown")["result"]
    _assert_context_identity(server._fallback_session_info(live.session), context,
        display="test/next", actual="test/next", pending=False)
    emitted = [payload for kind, sid, payload in live.frames if kind == "session.info" and sid == "runtime"]
    assert emitted
    _assert_context_identity(emitted[-1], context, display="test/next", actual="test/next", pending=False)


@pytest.mark.parametrize("named_route", [True, False])
def test_same_model_pending_provider_keeps_actual_custom_context_route(native_context, monkeypatch, named_route, caplog):
    import logging
    from unittest.mock import patch
    live = native_context
    _control_context_dependencies(monkeypatch)
    config = live.home / "config.yaml"
    if named_route:
        config.write_text(config.read_text() + "providers:\n  native-route:\n"
            "    api: http://invalid.local/v1\n    api_key: fixture-key\n    models: [test/model]\n")
    with patch("agent.process_bootstrap.OpenAI"):
        live.agent.switch_model(new_model="test/model", new_provider="custom", api_key="fixture-key",
                                base_url="http://invalid.local/v1", api_mode="chat_completions")
    context = rpc("session.context_breakdown")["result"]
    assert "provider" not in context  # existing Context wire shape is unchanged
    live.session["_compute_host_active"] = True
    assert rpc("config.set", key="model", value="test/model --provider anthropic",
               confirm_expensive_model=True)["result"]["deferred"]
    live.session.pop("_compute_host_active")
    # A remote display mirror must not change the actual local Agent used by Context.
    server._apply_compute_host_metadata_mirror(live.session, {
        "session_info": {"model": "test/model", "provider": "custom:other-route"}})
    info = server._session_info(live.agent, live.session)
    assert info["provider"] == "anthropic"
    _assert_context_identity(info, context, display="test/model", actual="test/model", pending=True,
                             provider="custom:native-route" if named_route else None)
    if named_route:
        foreign = live.home / "profiles" / "foreign"
        foreign.mkdir(parents=True)
        (foreign / "config.yaml").write_text("providers:\n  foreign-route:\n"
            "    api: http://invalid.local/v1\n    models: [test/model]\n")
        with server._profile_build_scope(foreign):
            _assert_context_identity(server._session_info(live.agent, live.session), context,
                display="test/model", actual="test/model", pending=True, provider="custom:native-route")
    private_error = "fixture-private-provider-error-marker"
    private_cause = "fixture-private-provider-cause-marker"
    def unavailable(*args, **kwargs):
        try:
            raise ValueError(private_cause)
        except ValueError as cause:
            raise RuntimeError(private_error) from cause
    monkeypatch.setattr(server, "_runtime_model_config", unavailable)
    # Optional observation failure cannot prevent the original mirrored native info response.
    caplog.clear()
    with caplog.at_level(logging.DEBUG, logger=server.logger.name):
        _assert_context_identity(server._session_info(live.agent, live.session), context,
            display="test/model", actual="test/model", pending=True, provider=None)
    assert private_error not in caplog.text
    assert private_cause not in caplog.text
    assert "Private configuration exception details redacted" in caplog.text
    observations = [record for record in caplog.records if record.message == "native context identity observation unavailable"]
    assert observations
    error = observations[-1].exc_info
    assert error and error[1].__cause__ is None and error[1].__context__ is None
    frames = []
    trace = error[2]
    while trace is not None:
        frames.append(trace.tb_frame.f_code.co_name)
        trace = trace.tb_next
    assert "unavailable" in frames and "_session_context_model_info" in frames


def test_old_typed_live_info_still_accepts_absent_observations():
    from tui_gateway.contracts.common import SessionLiveInfo
    info = SessionLiveInfo.model_validate({"model": "old/model", "provider": "old-provider"})
    assert info.context_model is None and info.context_provider is None and info.model_switch_pending is None
