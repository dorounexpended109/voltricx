"""Tests for voltricx.typings.track — targeting 100% branch coverage."""

from unittest.mock import AsyncMock, patch

import pytest

from voltricx.typings.track import (
    Playable,
    Playlist,
    PlaylistInfo,
    TrackInfo,
)

# ── Helpers ────────────────────────────────────────────────────────────────


def make_track_info(**kwargs):
    defaults = dict(
        identifier="abc123",
        isSeekable=True,
        author="Artist",
        length=240000,
        isStream=False,
        position=0,
        title="Test Track",
        sourceName="youtube",
        artworkUrl="http://img.com/art.jpg",
        isrc="US-1234",
        uri="http://track.url",
    )
    defaults.update(kwargs)
    return TrackInfo(**defaults)


def make_playable(encoded="enc123", title="Test Track", **kwargs):
    info = make_track_info(title=title, **kwargs)
    return Playable(encoded=encoded, info=info)


# ── TrackInfo ──────────────────────────────────────────────────────────────


def test_track_info_fields():
    info = make_track_info()
    assert info.identifier == "abc123"
    assert info.is_seekable is True
    assert info.author == "Artist"
    assert info.length == 240000
    assert info.is_stream is False
    assert info.position == 0
    assert info.title == "Test Track"
    assert info.source_name == "youtube"
    assert info.artwork_url == "http://img.com/art.jpg"
    assert info.isrc == "US-1234"
    assert info.uri == "http://track.url"


def test_track_info_optional_none():
    info = make_track_info(artworkUrl=None, isrc=None, uri=None)
    assert info.artwork_url is None
    assert info.isrc is None
    assert info.uri is None


# ── Playable ───────────────────────────────────────────────────────────────


def test_playable_properties():
    t = make_playable()
    assert t.identifier == "abc123"
    assert t.is_seekable is True
    assert t.author == "Artist"
    assert t.length == 240000
    assert t.is_stream is False
    assert t.position == 0
    assert t.title == "Test Track"
    assert t.uri == "http://track.url"
    assert t.artwork == "http://img.com/art.jpg"
    assert t.isrc == "US-1234"
    assert t.source == "youtube"


def test_playable_extras():
    t = make_playable()
    assert t.extras == {}


def test_playable_str_repr():
    t = make_playable()
    assert str(t) == "Test Track"
    assert "youtube" in repr(t)
    assert "Test Track" in repr(t)


def test_playable_equality_by_encoded():
    t1 = make_playable(encoded="same")
    t2 = make_playable(encoded="same")
    assert t1 == t2


def test_playable_equality_by_identifier():
    t1 = make_playable(encoded="enc1", identifier="ident1")
    t2 = make_playable(encoded="enc2", identifier="ident1")
    assert t1 == t2


def test_playable_not_equal():
    t1 = make_playable(encoded="enc1", identifier="id1")
    t2 = make_playable(encoded="enc2", identifier="id2")
    assert t1 != t2


def test_playable_not_equal_non_playable():
    t = make_playable()
    result = t.__eq__("not a playable")
    assert result is NotImplemented


def test_playable_hash():
    t = make_playable(encoded="hashme")
    assert hash(t) == hash("hashme")


def test_playable_recommended_default():
    t = make_playable()
    assert t.recommended is False


@pytest.mark.asyncio
async def test_playable_search_with_url():
    """Playable.search passes URL directly to Pool.fetch_tracks."""
    with patch("voltricx.pool.Pool.fetch_tracks", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = []
        await Playable.search("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        mock_fetch.assert_called_once_with("https://www.youtube.com/watch?v=dQw4w9WgXcQ", node=None)


@pytest.mark.asyncio
async def test_playable_search_plain_query_with_prefix():
    """Plain query without colon gets source prepended."""
    with patch("voltricx.pool.Pool.fetch_tracks", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = []
        await Playable.search("my query", source="ytsearch")
        mock_fetch.assert_called_once_with("ytsearch:my query", node=None)


@pytest.mark.asyncio
async def test_playable_search_query_with_colon_passthrough():
    """Query with colon (e.g. dzsearch:...) is passed through as-is."""
    with patch("voltricx.pool.Pool.fetch_tracks", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = []
        await Playable.search("dzsearch:some song")
        mock_fetch.assert_called_once_with("dzsearch:some song", node=None)


# ── Playlist ───────────────────────────────────────────────────────────────


def make_playlist(num_tracks=2):
    tracks = [make_playable(encoded=f"enc{i}", identifier=f"id{i}") for i in range(num_tracks)]
    info = PlaylistInfo(name="Test Playlist", selectedTrack=0)
    return Playlist(info=info, tracks=tracks)


def test_playlist_name():
    pl = make_playlist()
    assert pl.name == "Test Playlist"


def test_playlist_selected():
    pl = make_playlist()
    assert pl.selected == 0


def test_playlist_extras():
    pl = make_playlist()
    assert pl.extras == {}


def test_playlist_len():
    pl = make_playlist(num_tracks=3)
    assert len(pl) == 3


def test_playlist_getitem_int():
    pl = make_playlist(num_tracks=2)
    t = pl[0]
    assert t.encoded == "enc0"


def test_playlist_getitem_slice():
    pl = make_playlist(num_tracks=3)
    subset = pl[0:2]
    assert len(subset) == 2


def test_playlist_iter():
    pl = make_playlist(num_tracks=2)
    titles = [t.encoded for t in pl]
    assert "enc0" in titles
    assert "enc1" in titles


def test_playlist_repr():
    pl = make_playlist(num_tracks=2)
    assert "Test Playlist" in repr(pl)
    assert "2" in repr(pl)
