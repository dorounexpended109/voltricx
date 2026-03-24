"""Tests for voltricx.exceptions — targeting 100% branch coverage."""

import pytest

from voltricx.exceptions import (
    ChannelTimeoutException,
    InvalidChannelStateException,
    InvalidNodeException,
    LavalinkException,
    LavalinkLoadException,
    NodeException,
    QueueEmpty,
    RevvLinkException,
    VoltricxException,
)
from voltricx.typings.common import TrackException
from voltricx.typings.node import ErrorResponse

# ── Base exception ─────────────────────────────────────────────────────────


def test_voltricx_exception_is_exception():
    exc = VoltricxException("base error")
    assert isinstance(exc, Exception)
    assert str(exc) == "base error"


def test_revv_link_exception_is_alias():
    assert RevvLinkException is VoltricxException


# ── NodeException ──────────────────────────────────────────────────────────


def test_node_exception_default():
    exc = NodeException()
    assert exc.status is None
    assert str(exc) == "None"


def test_node_exception_with_status():
    exc = NodeException(msg="bad node", status=500)
    assert exc.status == 500
    assert "bad node" in str(exc)


# ── LavalinkException ──────────────────────────────────────────────────────


def _make_error_response(**kwargs):
    defaults = dict(
        timestamp=0,
        status=500,
        error="Internal",
        path="/v4/test",
        trace=None,
        message="error",
    )
    defaults.update(kwargs)
    return ErrorResponse(**defaults)


def test_lavalink_exception_auto_msg():
    resp = _make_error_response(status=404, error="Not Found", path="/v4/loadtracks")
    exc = LavalinkException(data=resp)
    assert exc.status == 404
    assert exc.error == "Not Found"
    assert exc.path == "/v4/loadtracks"
    assert "404" in str(exc)


def test_lavalink_exception_custom_msg():
    resp = _make_error_response()
    exc = LavalinkException(data=resp, msg="custom msg")
    assert str(exc) == "custom msg"


def test_lavalink_exception_with_trace():
    resp = _make_error_response(trace="stack trace here")
    exc = LavalinkException(data=resp)
    assert exc.trace == "stack trace here"


# ── LavalinkLoadException ──────────────────────────────────────────────────


def _make_track_exception(**kwargs):
    defaults = dict(message="load failed", severity="common", cause="SomeError", causeStackTrace="")
    defaults.update(kwargs)
    return TrackException(**defaults)


def test_lavalink_load_exception_auto_msg():
    tex = _make_track_exception()
    exc = LavalinkLoadException(data=tex)
    assert exc.message == "load failed"
    assert exc.cause == "SomeError"
    assert "load failed" in str(exc)


def test_lavalink_load_exception_custom_msg():
    tex = _make_track_exception()
    exc = LavalinkLoadException(data=tex, msg="override")
    assert str(exc) == "override"


# ── Simple exception types ─────────────────────────────────────────────────


def test_invalid_node_exception():
    exc = InvalidNodeException("no node")
    assert isinstance(exc, VoltricxException)
    assert "no node" in str(exc)


def test_channel_timeout_exception():
    exc = ChannelTimeoutException("timed out")
    assert isinstance(exc, VoltricxException)


def test_invalid_channel_state_exception():
    exc = InvalidChannelStateException("bad channel")
    assert isinstance(exc, VoltricxException)


def test_queue_empty_exception():
    exc = QueueEmpty("empty")
    assert isinstance(exc, VoltricxException)


def test_raise_and_catch_voltricx_exception():
    with pytest.raises(VoltricxException):
        raise NodeException("test raise")
