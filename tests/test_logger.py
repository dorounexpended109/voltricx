"""Tests for voltricx.logger — targeting 100% branch coverage."""

from voltricx.logger import (
    VoltricxLogger,
    VoltricxTimer,
    _emit,
    _format_meta,
    _now_ts,
    voltricx_logger,
)

# ── Module-level helpers ───────────────────────────────────────────────────


def test_now_ts_returns_string():
    ts = _now_ts()
    assert isinstance(ts, str)
    assert len(ts) > 0


def test_format_meta_empty():
    assert _format_meta({}) == ""


def test_format_meta_with_data():
    result = _format_meta({"node_id": "Node-1", "method": "GET"})
    assert "node_id" in result
    assert "Node-1" in result


def test_emit_incoming_arrow(capsys):
    _emit("INFO", "INCOMING", "test message", {})
    out = capsys.readouterr().out
    assert "←" in out


def test_emit_outgoing_arrow(capsys):
    _emit("INFO", "OUTGOING", "test message", {})
    out = capsys.readouterr().out
    assert "→" in out


def test_emit_other_bullet(capsys):
    _emit("INFO", "NODE", "bullet message", {})
    out = capsys.readouterr().out
    assert "•" in out


def test_emit_with_meta(capsys):
    _emit("INFO", "PLAYER", "with meta", {"guild_id": "12345"})
    out = capsys.readouterr().out
    assert "12345" in out


# ── VoltricxTimer ──────────────────────────────────────────────────────────


def test_timer_measures_elapsed():
    import time

    with VoltricxLogger.timer() as t:
        time.sleep(0.01)
    assert t.elapsed_ms >= 0.0
    assert isinstance(t.elapsed_ms, float)


def test_timer_context_manager():
    timer = VoltricxTimer()
    with timer as t:
        pass
    assert t.elapsed_ms >= 0


# ── VoltricxLogger ────────────────────────────────────────────────────────


def test_logger_default_state():
    logger = VoltricxLogger()
    assert logger.enabled is False


def test_logger_enable_disable():
    logger = VoltricxLogger()
    logger.enable()
    assert logger.enabled is True
    logger.disable()
    assert logger.enabled is False


def test_logger_toggle():
    logger = VoltricxLogger()
    result = logger.toggle()
    assert result is True
    result = logger.toggle()
    assert result is False


def test_logger_set_level():
    logger = VoltricxLogger()
    logger.set_level("WARNING")
    assert logger._level == 30


def test_logger_set_invalid_level_defaults_to_debug():
    logger = VoltricxLogger()
    logger.set_level("UNKNOWN_LEVEL")
    assert logger._level == 10  # DEBUG default


def test_logger_does_not_emit_when_disabled(capsys):
    logger = VoltricxLogger()
    logger.disable()
    logger.node("should not appear")
    assert capsys.readouterr().out == ""


def test_logger_does_not_emit_below_level(capsys):
    logger = VoltricxLogger()
    logger.enable()
    logger.set_level("ERROR")
    logger.debug("should not appear")
    assert capsys.readouterr().out == ""


def test_logger_emits_when_enabled(capsys):
    logger = VoltricxLogger()
    logger.enable()
    logger.node("test node message")
    out = capsys.readouterr().out
    assert "test node message" in out


def test_logger_all_methods(capsys):
    logger = VoltricxLogger()
    logger.enable()
    logger.set_level("DEBUG")

    methods = [
        logger.node,
        logger.ws,
        logger.ws_debug,
        logger.player,
        logger.incoming,
        logger.outgoing,
        logger.debug,
        logger.warning,
        logger.error,
        logger.system,
        logger.info,
    ]
    for method in methods:
        method("test message")

    out = capsys.readouterr().out
    assert out.count("test message") == len(methods)


def test_logger_status():
    logger = VoltricxLogger()
    logger.enable()
    logger.set_level("INFO")
    status = logger.status()
    assert status["enabled"] is True
    assert status["level"] == "INFO"


def test_logger_status_disabled():
    logger = VoltricxLogger()
    status = logger.status()
    assert status["enabled"] is False


def test_global_voltricx_logger_is_instance():
    assert isinstance(voltricx_logger, VoltricxLogger)
