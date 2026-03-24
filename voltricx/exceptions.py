# The MIT License (MIT)
#
# Copyright (c) 2026-Present @JustNixx, @Dipendra-creator and RevvLabs
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .typings.common import TrackException
    from .typings.node import ErrorResponse


__all__ = (
    "VoltricxException",
    "RevvLinkException",
    "NodeException",
    "LavalinkException",
    "LavalinkLoadException",
    "InvalidNodeException",
    "ChannelTimeoutException",
    "InvalidChannelStateException",
    "QueueEmpty",
)


class VoltricxException(Exception):
    """Base voltricx Exception class."""


RevvLinkException = VoltricxException


class NodeException(VoltricxException):
    """Error raised when an Unknown or Generic error occurs on a Node."""

    def __init__(self, msg: str | None = None, status: int | None = None) -> None:
        super().__init__(msg)
        self.status = status


class LavalinkException(VoltricxException):
    """Exception raised when Lavalink returns an invalid response."""

    def __init__(self, data: ErrorResponse, msg: str | None = None) -> None:
        self.timestamp = data.timestamp
        self.status = data.status
        self.error = data.error
        self.trace = data.trace
        self.path = data.path

        if not msg:
            msg = f"Lavalink API Error: status={self.status}, error={self.error}, path={self.path}"
        super().__init__(msg)


class LavalinkLoadException(VoltricxException):
    """Exception raised when an error occurred loading tracks via Lavalink."""

    def __init__(self, data: TrackException, msg: str | None = None) -> None:
        self.message = data.message
        self.severity = data.severity
        self.cause = data.cause

        if not msg:
            msg = f"Lavalink Load Error: {self.message} (Severity: {self.severity})"
        super().__init__(msg)


class InvalidNodeException(VoltricxException):
    """Exception raised when a Node is invalid or not found."""


class ChannelTimeoutException(VoltricxException):
    """Exception raised when connecting to a voice channel times out."""


class InvalidChannelStateException(VoltricxException):
    """Exception raised when a Player tries to connect to an invalid channel."""


class QueueEmpty(VoltricxException):
    """Exception raised when you try to retrieve from an empty queue."""
