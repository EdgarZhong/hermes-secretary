import pytest

from gateway.config import GatewayConfig, load_gateway_config


def test_stt_echo_transcripts_defaults_on_for_backwards_compatibility():
    cfg = GatewayConfig.from_dict({})

    assert cfg.stt_enabled is True
    assert cfg.stt_echo_transcripts is True
    assert cfg.to_dict()["stt_echo_transcripts"] is True
    assert cfg.stt_echo_transcripts_with_reply is False
    assert cfg.to_dict()["stt_echo_transcripts_with_reply"] is False


def test_top_level_stt_echo_transcripts_takes_precedence():
    cfg = GatewayConfig.from_dict({
        "stt_echo_transcripts": False,
        "stt": {"echo_transcripts": True},
    })

    assert cfg.stt_echo_transcripts is False


@pytest.mark.parametrize("document", [
    "gateway:\n  stt:\n    echo_transcripts_with_reply: true\n",
    "stt:\n  echo_transcripts_with_reply: true\n",
    "stt_echo_transcripts_with_reply: true\n",
])
def test_merged_stt_echo_loads_from_real_config(tmp_path, monkeypatch, document):
    home = tmp_path / ".hermes"
    home.mkdir()
    (home / "config.yaml").write_text(document)
    monkeypatch.setenv("HERMES_HOME", str(home))

    config = load_gateway_config()

    assert config.stt_echo_transcripts_with_reply is True
    assert config.stt_echo_transcripts is True
    assert config.to_dict()["stt_echo_transcripts_with_reply"] is True


def test_flat_merged_echo_false_overrides_nested_true():
    config = GatewayConfig.from_dict({
        "stt_echo_transcripts_with_reply": False,
        "stt": {"echo_transcripts_with_reply": True},
    })
    assert config.stt_echo_transcripts_with_reply is False
