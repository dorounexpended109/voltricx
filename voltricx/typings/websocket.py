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
from .enums import OpCode
from .events import EventPayload
from .node import CPUStats, FrameStats, MemoryStats
from .player import PlayerState


class ReadyOp(LavalinkBaseModel):
    op: Literal[OpCode.ready] = OpCode.ready
    resumed: bool
    session_id: str = Field(alias="sessionId")


class PlayerUpdateOp(LavalinkBaseModel):
    op: Literal[OpCode.player_update] = OpCode.player_update
    guild_id: str = Field(alias="guildId")
    state: PlayerState


class StatsOp(LavalinkBaseModel):
    op: Literal[OpCode.stats] = OpCode.stats
    players: int
    playing_players: int = Field(alias="playingPlayers")
    uptime: int
    memory: MemoryStats
    cpu: CPUStats
    frame_stats: FrameStats | None = Field(None, alias="frameStats")


# DAVE Protocol Events-initiates MLS handshake
class DAVEProtocolChangeEvent(LavalinkBaseModel):
    op: Literal["dave"]
    type: Literal["protocolChange"]
    guild_id: str = Field(alias="guildId")
    protocol: str  # "udp" or "kcp"
    encryption_key: str = Field(alias="encryptionKey")


# DAVE prepare transition event - epoch/key rotation
class DAVEPrepareTransitionEvent(LavalinkBaseModel):
    op: Literal["dave"]
    type: Literal["prepareTransition"]
    guild_id: str = Field(alias="guildId")
    epoch: int  # MLS epoch for key rotation
    next_encryption_key: str = Field(alias="nextEncryptionKey")


DavePayload = Annotated[
    Union[DAVEProtocolChangeEvent, DAVEPrepareTransitionEvent],
    Field(discriminator="type"),
]

WebSocketPayload = Annotated[
    Union[ReadyOp, PlayerUpdateOp, StatsOp, EventPayload, DavePayload],
    Field(discriminator="op"),
]
