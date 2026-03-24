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

from enum import StrEnum


class QueueMode(StrEnum):
    normal = "normal"
    loop = "loop"
    loop_all = "loop_all"


class Severity(StrEnum):
    common = "common"
    suspicious = "suspicious"
    fault = "fault"


class OpCode(StrEnum):
    ready = "ready"
    player_update = "playerUpdate"
    stats = "stats"
    event = "event"
    dave = "dave"


class EventType(StrEnum):
    track_start = "TrackStartEvent"
    track_end = "TrackEndEvent"
    track_exception = "TrackExceptionEvent"
    track_stuck = "TrackStuckEvent"
    websocket_closed = "WebSocketClosedEvent"


class TrackEndReason(StrEnum):
    finished = "finished"
    load_failed = "loadFailed"
    stopped = "stopped"
    replaced = "replaced"
    cleanup = "cleanup"


class IPBlockType(StrEnum):
    inet4 = "Inet4Address"
    inet6 = "Inet6Address"


class RoutePlannerClass(StrEnum):
    rotating_ip = "RotatingIpRoutePlanner"
    nano_ip = "NanoIpRoutePlanner"
    rotating_nano_ip = "RotatingNanoIpRoutePlanner"
    balancing_ip = "BalancingIpRoutePlanner"


class LoadType(StrEnum):
    track = "track"
    playlist = "playlist"
    search = "search"
    empty = "empty"
    error = "error"


class NodeStatus(StrEnum):
    connected = "connected"
    connecting = "connecting"
    disconnected = "disconnected"


class AutoPlayMode(StrEnum):
    enabled = "enabled"
    partial = "partial"
    disabled = "disabled"
