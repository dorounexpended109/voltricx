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

from typing import TYPE_CHECKING, Annotated, Any

import yarl
from pydantic import ConfigDict, Field

from .base import LavalinkBaseModel
from .common import TrackException
from .enums import LoadType

if TYPE_CHECKING:
    from ..node import Node


class TrackInfo(LavalinkBaseModel):
    model_config = ConfigDict(frozen=True)
    identifier: str
    is_seekable: bool = Field(alias="isSeekable")
    author: str
    length: int
    is_stream: bool = Field(alias="isStream")
    position: int
    title: str
    uri: str | None = None
    artwork_url: str | None = Field(None, alias="artworkUrl")
    isrc: str | None = None
    source_name: str = Field(alias="sourceName")


class Playable(LavalinkBaseModel):
    model_config = ConfigDict(frozen=True)
    encoded: str
    info: TrackInfo
    plugin_info: dict[str, Any] = Field(default_factory=dict, alias="pluginInfo")
    user_data: dict[str, Any] = Field(default_factory=dict, alias="userData")

    # Extra fields for compatibility
    recommended: bool = False

    @property
    def identifier(self) -> str:
        return self.info.identifier

    @property
    def is_seekable(self) -> bool:
        return self.info.is_seekable

    @property
    def author(self) -> str:
        return self.info.author

    @property
    def length(self) -> int:
        return self.info.length

    @property
    def is_stream(self) -> bool:
        return self.info.is_stream

    @property
    def position(self) -> int:
        return self.info.position

    @property
    def title(self) -> str:
        return self.info.title

    @property
    def uri(self) -> str | None:
        return self.info.uri

    @property
    def artwork(self) -> str | None:
        return self.info.artwork_url

    @property
    def isrc(self) -> str | None:
        return self.info.isrc

    @property
    def source(self) -> str:
        return self.info.source_name

    @property
    def extras(self) -> dict[str, Any]:
        return self.user_data

    @extras.setter
    def extras(self, value: dict[str, Any]) -> None:
        # Use clear() and update() to mutate the existing dict on a frozen model
        self.user_data.clear()
        self.user_data.update(value)

    def __str__(self) -> str:
        return self.title

    def __repr__(self) -> str:
        return f"Playable(source={self.source}, title={self.title}, identifier={self.identifier})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Playable):
            return NotImplemented
        return self.encoded == other.encoded or self.identifier == other.identifier

    def __hash__(self) -> int:
        return hash(self.encoded)

    @classmethod
    async def search(
        cls,
        query: str,
        /,
        *,
        source: str = "dzsearch",
        node: Node | None = None,
    ) -> Search:
        """Search for tracks. High-fidelity port of the original search method."""
        from ..pool import Pool

        check = yarl.URL(query)
        if check.host:
            return await Pool.fetch_tracks(query, node=node)

        if ":" not in query:
            query = f"{source}:{query}"

        return await Pool.fetch_tracks(query, node=node)


class PlaylistInfo(LavalinkBaseModel):
    name: str
    selected_track: int = Field(alias="selectedTrack")


class Playlist(LavalinkBaseModel):
    info: PlaylistInfo
    plugin_info: dict[str, Any] = Field(default_factory=dict, alias="pluginInfo")
    tracks: list[Playable]
    user_data: dict[str, Any] = Field(default_factory=dict, alias="userData")

    @property
    def name(self) -> str:
        return self.info.name

    @property
    def selected(self) -> int:
        return self.info.selected_track

    @property
    def extras(self) -> dict[str, Any]:
        return self.user_data

    @extras.setter
    def extras(self, value: dict[str, Any]) -> None:
        self.user_data = value
        for track in self.tracks:
            # Use fset to bypass Pydantic's frozen model restriction for properties
            Playable.extras.fset(track, value)  # type: ignore

    def __len__(self) -> int:
        return len(self.tracks)

    def __getitem__(self, index: int | slice) -> Playable | list[Playable]:
        return self.tracks[index]

    def __iter__(self):  # pyright: ignore[reportIncompatibleMethodOverride]
        return iter(self.tracks)

    def __repr__(self) -> str:
        return f"Playlist(name={self.name}, tracks={len(self.tracks)})"


class TrackResult(LavalinkBaseModel):
    load_type: LoadType = LoadType.track
    data: Playable


class PlaylistResult(LavalinkBaseModel):
    load_type: LoadType = LoadType.playlist
    data: Playlist


class SearchResult(LavalinkBaseModel):
    load_type: LoadType = LoadType.search
    data: list[Playable]


class EmptyResult(LavalinkBaseModel):
    load_type: LoadType = LoadType.empty
    data: dict[str, Any] = Field(default_factory=dict)


class ErrorResult(LavalinkBaseModel):
    load_type: LoadType = LoadType.error
    data: TrackException


Search = list[Playable] | Playlist

LoadTracksResult = Annotated[
    TrackResult | PlaylistResult | SearchResult | EmptyResult | ErrorResult,
    Field(discriminator="load_type"),
]
