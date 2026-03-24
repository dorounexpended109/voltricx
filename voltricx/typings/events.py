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

from typing import Annotated, Literal, Union

from pydantic import Field

from .base import LavalinkBaseModel
from .common import TrackException
from .enums import EventType, TrackEndReason
from .track import Playable


class TrackStartEvent(LavalinkBaseModel):
    op: Literal["event"]
    type: Literal[EventType.track_start] = EventType.track_start
    guild_id: str = Field(alias="guildId")
    track: Playable


class TrackEndEvent(LavalinkBaseModel):
    op: Literal["event"]
    type: Literal[EventType.track_end] = EventType.track_end
    guild_id: str = Field(alias="guildId")
    track: Playable
    reason: TrackEndReason


class TrackExceptionEvent(LavalinkBaseModel):
    op: Literal["event"]
    type: Literal[EventType.track_exception] = EventType.track_exception
    guild_id: str = Field(alias="guildId")
    track: Playable
    exception: TrackException


class TrackStuckEvent(LavalinkBaseModel):
    op: Literal["event"]
    type: Literal[EventType.track_stuck] = EventType.track_stuck
    guild_id: str = Field(alias="guildId")
    track: Playable
    threshold_ms: int = Field(alias="thresholdMs")


class WebSocketClosedEvent(LavalinkBaseModel):
    op: Literal["event"]
    type: Literal[EventType.websocket_closed] = EventType.websocket_closed
    guild_id: str = Field(alias="guildId")
    code: int
    reason: str
    by_remote: bool = Field(alias="byRemote")


EventPayload = Annotated[
    Union[
        TrackStartEvent,
        TrackEndEvent,
        TrackExceptionEvent,
        TrackStuckEvent,
        WebSocketClosedEvent,
    ],
    Field(discriminator="type"),
]
