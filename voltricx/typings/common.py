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

from pydantic import Field

from .base import LavalinkBaseModel
from .enums import Severity


class TrackException(LavalinkBaseModel):
    message: str | None = None
    severity: Severity
    cause: str
    cause_stack_trace: str = Field(alias="causeStackTrace")


class DiscordVoiceStateUpdateData(LavalinkBaseModel):
    guild_id: str = Field(alias="guild_id")
    channel_id: str | None = Field(None, alias="channel_id")
    self_mute: bool = Field(alias="self_mute")
    self_deaf: bool = Field(alias="self_deaf")


class DiscordVoiceStateUpdate(LavalinkBaseModel):
    op: int = Field(4, alias="op")
    d: DiscordVoiceStateUpdateData


class HyperCacheConfig(LavalinkBaseModel):
    capacity: int = 100
    track_capacity: int = 1000
    decay_factor: float = 0.5
    decay_threshold: int = 1000


class QueueConfig(LavalinkBaseModel):
    max_history_size: int = 100
    atomic_default: bool = True
