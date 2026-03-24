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

from typing import Any

from pydantic import Field

from .base import LavalinkBaseModel
from .filters import Filters
from .track import Playable


class VoiceState(LavalinkBaseModel):
    token: str
    endpoint: str
    session_id: str = Field(alias="sessionId")
    channel_id: str | None = Field(default=None, alias="channelId")


class PlayerState(LavalinkBaseModel):
    time: int
    position: int
    connected: bool
    ping: int


class Player(LavalinkBaseModel):
    guild_id: str = Field(alias="guildId")
    track: Playable | None = None
    volume: int
    paused: bool
    state: PlayerState
    voice: VoiceState
    filters: Filters
    seamless_play: bool | None = Field(default=None, alias="seamlessPlay")


class UpdatePlayerTrack(LavalinkBaseModel):
    encoded: str | None = None
    identifier: str | None = None
    user_data: dict[str, Any] = Field(default_factory=dict, alias="userData")


class UpdatePlayerPayload(LavalinkBaseModel):
    track: UpdatePlayerTrack | None = None
    position: int | None = None
    end_time: int | None = Field(default=None, alias="endTime")
    volume: int | None = None
    paused: bool | None = None
    filters: dict[str, Any] | None = None
    voice: VoiceState | None = None
