"""Dual-SPA mount: the native dashboard at a subpath sharing one API surface.

Covers the confirmed private deployment shape (06 §0.7): the Secretary SPA stays at
``/`` and the native dashboard is mounted at ``HERMES_DASHBOARD_PREFIX`` (default
``/dashboard``) in the same process, with ``<prefix>/api/*`` rewritten to ``/api/*``
for HTTP and WebSocket. Unset ``HERMES_DASHBOARD_WEB_DIST`` keeps the original
single-SPA behaviour.
"""

from pathlib import Path

from fastapi import FastAPI, WebSocket
from starlette.testclient import TestClient

from hermes_cli import web_server
from hermes_cli import web_server_dashboard


def _write_dist(root: Path, marker: str) -> None:
    (root / "assets").mkdir(parents=True)
    (root / "index.html").write_text(
        f"<html><head></head><body>{marker}</body></html>", encoding="utf-8"
    )
    (root / "assets" / "app.js").write_text(f"// {marker}", encoding="utf-8")
    (root / "assets" / "app.css").write_text(
        "body{background:url(/fonts/x.woff2)}", encoding="utf-8"
    )


def _make_client(
    tmp_path: Path,
    monkeypatch,
    *,
    dashboard: bool = True,
    prefix: str = "/dashboard",
):
    secretary = tmp_path / "secretary"
    native = tmp_path / "native"
    _write_dist(secretary, "SECRETARY")
    _write_dist(native, "DASHBOARD")

    monkeypatch.setattr(web_server, "WEB_DIST", secretary)
    monkeypatch.delenv("HERMES_SERVE_HEADLESS", raising=False)
    if dashboard:
        monkeypatch.setenv("HERMES_DASHBOARD_WEB_DIST", str(native))
        monkeypatch.setenv("HERMES_DASHBOARD_PREFIX", prefix)
    else:
        monkeypatch.delenv("HERMES_DASHBOARD_WEB_DIST", raising=False)
        monkeypatch.delenv("HERMES_DASHBOARD_PREFIX", raising=False)

    app = FastAPI()

    @app.get("/api/status")
    def api_status():
        return {"owner": "shared"}

    @app.websocket("/api/ws")
    async def api_ws(ws: WebSocket) -> None:
        await ws.accept()
        await ws.send_text("ws-ok")
        await ws.close()

    web_server_dashboard.mount_spa(app)
    return TestClient(app)


def test_unset_second_dist_keeps_original_single_spa_behaviour(tmp_path, monkeypatch):
    client = _make_client(tmp_path, monkeypatch, dashboard=False)

    root = client.get("/")
    assert root.status_code == 200
    assert "SECRETARY" in root.text
    assert 'window.__HERMES_BASE_PATH__="";' in root.text

    # No /dashboard mount: the primary catch-all keeps serving the Secretary SPA.
    dashboard = client.get("/dashboard")
    assert dashboard.status_code == 200
    assert "SECRETARY" in dashboard.text


def test_second_spa_is_mounted_at_default_prefix(tmp_path, monkeypatch):
    client = _make_client(tmp_path, monkeypatch)

    root = client.get("/")
    assert root.status_code == 200
    assert "SECRETARY" in root.text
    assert 'window.__HERMES_BASE_PATH__="";' in root.text

    dashboard = client.get("/dashboard")
    assert dashboard.status_code == 200
    assert "DASHBOARD" in dashboard.text
    assert 'window.__HERMES_BASE_PATH__="/dashboard";' in dashboard.text
    assert "window.__HERMES_SESSION_TOKEN__=" in dashboard.text

    deep_link = client.get("/dashboard/sessions/abc")
    assert deep_link.status_code == 200
    assert "DASHBOARD" in deep_link.text


def test_both_asset_trees_and_css_prefix_are_isolated(tmp_path, monkeypatch):
    client = _make_client(tmp_path, monkeypatch)

    assert client.get("/assets/app.js").text == "// SECRETARY"
    assert client.get("/dashboard/assets/app.js").text == "// DASHBOARD"

    css = client.get("/dashboard/assets/app.css")
    assert css.status_code == 200
    assert "url(/dashboard/fonts/x.woff2)" in css.text


def test_dashboard_api_and_websocket_share_the_root_api_surface(tmp_path, monkeypatch):
    client = _make_client(tmp_path, monkeypatch)

    assert client.get("/api/status").json() == {"owner": "shared"}
    assert client.get("/dashboard/api/status").json() == {"owner": "shared"}
    # A missing API endpoint under the prefix is a JSON 404, never the SPA HTML.
    missing = client.get("/dashboard/api/missing")
    assert missing.status_code == 404
    assert missing.headers["content-type"].startswith("application/json")

    with client.websocket_connect("/dashboard/api/ws") as ws:
        assert ws.receive_text() == "ws-ok"


def test_prefix_is_configurable(tmp_path, monkeypatch):
    client = _make_client(tmp_path, monkeypatch, prefix="/ops/dashboard")

    dashboard = client.get("/ops/dashboard")
    assert dashboard.status_code == 200
    assert "DASHBOARD" in dashboard.text
    assert 'window.__HERMES_BASE_PATH__="/ops/dashboard";' in dashboard.text

    assert client.get("/ops/dashboard/api/status").json() == {"owner": "shared"}
    assert client.get("/ops/dashboard/assets/app.js").text == "// DASHBOARD"
    css = client.get("/ops/dashboard/assets/app.css")
    assert "url(/ops/dashboard/fonts/x.woff2)" in css.text

    # The root SPA is untouched by the second mount.
    assert "SECRETARY" in client.get("/").text
