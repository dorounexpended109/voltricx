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

"""
Voltricx
~~~~~~~~

A modern, simple, and powerful Lavalink wrapper for discord.py and its derivatives.
Built with performance and ease of use in mind.
"""

__title__ = "Voltricx"
__author__ = "@JustNixx and @Dipendra-creator"
__license__ = "MIT"
__copyright__ = "Copyright 2026-Present (c) @JustNixx and @Dipendra-creator"

try:
    from ._version import version as __version__  # pyright: ignore[reportMissingImports]
except ImportError:
    __version__ = "unknown"

from .exceptions import (  # noqa: F401
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
from .filters import (
    ChannelMix,
    Distortion,
    Equalizer,
    Filters,
    Karaoke,
    LowPass,
    Rotation,
    Timescale,
    Tremolo,
    Vibrato,
)
from .hypercache import HyperCache
from .logger import voltricx_logger
from .node import Node
from .player import Player
from .pool import Pool
from .queue import Queue
from .typings import *  # noqa: F401, F403 – intentional re-export of all typing symbols
from .typings.track import Playable, Playlist
from .utils import ExtrasNamespace, Namespace, build_basic_layout  # noqa: F401

__all__ = (
    "Node",
    "Pool",
    "Player",
    "Queue",
    "Filters",
    "Equalizer",
    "Karaoke",
    "Timescale",
    "Tremolo",
    "Vibrato",
    "Rotation",
    "Distortion",
    "ChannelMix",
    "LowPass",
    "HyperCache",
    "Playable",
    "Playlist",
    "voltricx_logger",
    "__version__",
    "__title__",
    "__author__",
    "__license__",
    "__copyright__",
)
