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

import time
from datetime import UTC, datetime
from typing import Any, Self

__all__ = ("VoltricxLogger", "voltricx_logger")

# ── ANSI colours ────────────────────────────────────────────────────────────
_RESET = "\033[0m"
_BOLD = "\033[1m"
_DIM = "\033[2m"

_C_NODE = "\033[36m"  # cyan      NODE
_C_WS = "\033[35m"  # magenta   WS
_C_PLAYER = "\033[34m"  # blue      PLAYER
_C_INCOMING = "\033[32m"  # green     INCOMING ←
_C_OUTGOING = "\033[33m"  # yellow    OUTGOING →
_C_ERROR = "\033[31m"  # red       ERROR
_C_WARNING = "\033[33m"  # yellow    WARNING
_C_DEBUG = "\033[37m"  # white     DEBUG
_C_SYSTEM = "\033[96m"  # cyan-br   SYSTEM

_CATEGORY_COLOURS: dict[str, str] = {
    "NODE": _C_NODE,
    "WS": _C_WS,
    "PLAYER": _C_PLAYER,
    "INCOMING": _C_INCOMING,
    "OUTGOING": _C_OUTGOING,
    "ERROR": _C_ERROR,
    "WARNING": _C_WARNING,
    "DEBUG": _C_DEBUG,
    "SYSTEM": _C_SYSTEM,
}

_LEVEL_COLOURS: dict[str, str] = {
    "DEBUG": _C_DEBUG,
    "INFO": "\033[32m",
    "WARNING": _C_WARNING,
    "ERROR": _C_ERROR,
    "CRITICAL": "\033[41m",
}

_LEVEL_NUMS: dict[str, int] = {
    "DEBUG": 10,
    "INFO": 20,
    "WARNING": 30,
    "ERROR": 40,
    "CRITICAL": 50,
}


def _now_ts() -> str:
    return datetime.now(tz=UTC).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]


def _format_meta(meta: dict[str, Any]) -> str:
    if not meta:
        return ""
    parts = []
    for k, v in meta.items():
        parts.append(f"{_DIM}{k}{_RESET}={v}")
    return "  " + "  ".join(parts)


def _emit(level: str, category: str, message: str, meta: dict[str, Any]) -> None:
    ts = _now_ts()
    cat_c = _CATEGORY_COLOURS.get(category, "")
    lvl_c = _LEVEL_COLOURS.get(level, "")
    meta_str = _format_meta(meta)

    # Arrow indicator
    if category == "INCOMING":
        arrow = f"{_C_INCOMING}←{_RESET}"
    elif category == "OUTGOING":
        arrow = f"{_C_OUTGOING}→{_RESET}"
    else:
        arrow = f"{cat_c}•{_RESET}"

    line = (
        f"{_DIM}{ts}{_RESET} "
        f"{lvl_c}{_BOLD}[{level:8s}]{_RESET} "
        f"{cat_c}{_BOLD}[VOLTRICX:{category}]{_RESET} "
        f"{arrow} {message}"
        f"{meta_str}"
    )
    try:
        print(line, flush=True)
    except OSError:
        # Silently suppress broken-pipe and similar I/O errors during log output.
        pass


class VoltricxTimer:
    """Lightweight perf_counter timer for measuring elapsed time of calls."""

    def __init__(self) -> None:
        self._start: float = 0.0
        self.elapsed_ms: float = 0.0

    def __enter__(self) -> Self:
        self._start = time.perf_counter()
        return self

    def __exit__(self, *_: object) -> None:
        self.elapsed_ms = round((time.perf_counter() - self._start) * 1000, 2)


class VoltricxLogger:
    """Self-contained toggleable logger for the voltricx library."""

    def __init__(self) -> None:
        self.enabled: bool = False
        self._level: int = _LEVEL_NUMS["DEBUG"]

    def enable(self) -> None:
        self.enabled = True

    def disable(self) -> None:
        self.enabled = False

    def toggle(self) -> bool:
        """Toggle enabled state. Returns the new state."""
        self.enabled = not self.enabled
        return self.enabled

    def set_level(self, level: str) -> None:
        """Set minimum log level: DEBUG, INFO, WARNING, ERROR, CRITICAL."""
        self._level = _LEVEL_NUMS.get(level.upper(), _LEVEL_NUMS["DEBUG"])

    def _log(self, level: str, category: str, message: str, meta: dict[str, Any]) -> None:
        if not self.enabled:
            return
        if _LEVEL_NUMS.get(level, 0) < self._level:
            return
        _emit(level, category, message, meta)

    def node(self, message: str, **meta: Any) -> None:
        self._log("INFO", "NODE", message, meta)

    def ws(self, message: str, **meta: Any) -> None:
        self._log("INFO", "WS", message, meta)

    def ws_debug(self, message: str, **meta: Any) -> None:
        self._log("DEBUG", "WS", message, meta)

    def player(self, message: str, **meta: Any) -> None:
        self._log("INFO", "PLAYER", message, meta)

    def incoming(self, message: str, **meta: Any) -> None:
        self._log("INFO", "INCOMING", message, meta)

    def outgoing(self, message: str, **meta: Any) -> None:
        self._log("INFO", "OUTGOING", message, meta)

    def debug(self, message: str, **meta: Any) -> None:
        self._log("DEBUG", "DEBUG", message, meta)

    def warning(self, message: str, **meta: Any) -> None:
        self._log("WARNING", "WARNING", message, meta)

    def error(self, message: str, **meta: Any) -> None:
        self._log("ERROR", "ERROR", message, meta)

    def system(self, message: str, **meta: Any) -> None:
        self._log("INFO", "SYSTEM", message, meta)

    def info(self, message: str, **meta: Any) -> None:
        self._log("INFO", "INFO", message, meta)

    @staticmethod
    def timer() -> VoltricxTimer:
        return VoltricxTimer()

    def status(self) -> dict[str, Any]:
        level_name = next((k for k, v in _LEVEL_NUMS.items() if v == self._level), "DEBUG")
        return {
            "enabled": self.enabled,
            "level": level_name,
        }


voltricx_logger: VoltricxLogger = VoltricxLogger()
