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


from pydantic import Field

from .base import LavalinkBaseModel


class NodeConfig(LavalinkBaseModel):
    identifier: str
    uri: str
    password: str
    region: str | None = "global"
    heartbeat: float = 15.0
    retries: int | None = None
    resume_timeout: int = 60
    inactive_player_timeout: int | None = 300
    inactive_channel_tokens: int | None = 3


class Version(LavalinkBaseModel):
    semver: str
    major: int
    minor: int
    patch: int
    pre_release: str | None = Field(None, alias="preRelease")
    build: str | None = None


class Git(LavalinkBaseModel):
    branch: str
    commit: str
    commit_time: int = Field(alias="commitTime")


class Plugin(LavalinkBaseModel):
    name: str
    version: str


class NodeInfo(LavalinkBaseModel):
    version: Version
    build_time: int = Field(alias="buildTime")
    git: Git
    jvm: str
    lavaplayer: str
    source_managers: list[str] = Field(alias="sourceManagers")
    filters: list[str]
    plugins: list[Plugin]


class MemoryStats(LavalinkBaseModel):
    free: int
    used: int
    allocated: int
    reservable: int


class CPUStats(LavalinkBaseModel):
    cores: int
    system_load: float = Field(alias="systemLoad")
    lavalink_load: float = Field(alias="lavalinkLoad")


class FrameStats(LavalinkBaseModel):
    sent: int
    nulled: int
    deficit: int


class NodeHeaders(LavalinkBaseModel):
    authorization: str = Field(alias="Authorization")
    user_id: str = Field(alias="User-Id")
    client_name: str = Field(alias="Client-Name")
    session_id: str | None = Field(None, alias="Session-Id")


class ErrorResponse(LavalinkBaseModel):
    timestamp: int
    status: int
    error: str
    trace: str | None = None
    message: str
    path: str
