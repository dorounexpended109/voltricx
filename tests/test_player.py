from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from voltricx import Playable, Player

# These tests are legacy from pre-refactor. Comprehensive player tests are in test_player_extended.py
pytestmark = pytest.mark.skip(
    reason="Legacy tests - see test_player_extended.py and test_player_edge.py"
)


@pytest.fixture
def mock_pool():
    with patch("voltricx.Pool.get_node") as mock:
        yield mock


@pytest.mark.asyncio
async def test_player_initialization(mock_client, mock_voice_channel, mock_pool, mock_node):
    mock_pool.return_value = mock_node
    player = Player(client=mock_client, channel=mock_voice_channel)

    assert player.node == mock_node
    assert player.volume == 100
    assert player.paused is False
    assert player.queue.count == 0


@pytest.mark.asyncio
async def test_player_play(mock_client, mock_voice_channel, mock_pool, mock_node, mock_guild):
    mock_pool.return_value = mock_node
    player = Player(client=mock_client, channel=mock_voice_channel)
    player._guild = mock_guild

    track = MagicMock(spec=Playable)
    track.encoded = "encoded_track"
    track.title = "Test Track"
    track.extras = {}

    mock_node._update_player = AsyncMock()

    await player.play(track)

    assert player.current == track
    mock_node._update_player.assert_called_once()
    # Check if encoded track was passed in payload
    args, kwargs = mock_node._update_player.call_args
    assert kwargs["data"]["track"]["encoded"] == "encoded_track"


@pytest.mark.asyncio
async def test_player_pause(mock_client, mock_voice_channel, mock_pool, mock_node, mock_guild):
    mock_pool.return_value = mock_node
    player = Player(client=mock_client, channel=mock_voice_channel)
    player._guild = mock_guild

    mock_node._update_player = AsyncMock()

    await player.pause(True)
    assert player.paused is True
    mock_node._update_player.assert_called_with(mock_guild.id, data={"paused": True})


@pytest.mark.asyncio
async def test_player_set_volume(mock_client, mock_voice_channel, mock_pool, mock_node, mock_guild):
    mock_pool.return_value = mock_node
    player = Player(client=mock_client, channel=mock_voice_channel)
    player._guild = mock_guild

    mock_node._update_player = AsyncMock()

    await player.set_volume(50)
    assert player.volume == 50
    mock_node._update_player.assert_called_with(mock_guild.id, data={"volume": 50})


@pytest.mark.asyncio
async def test_player_stop(mock_client, mock_voice_channel, mock_pool, mock_node, mock_guild):
    mock_pool.return_value = mock_node
    player = Player(client=mock_client, channel=mock_voice_channel)
    player._guild = mock_guild

    player.play = AsyncMock()

    await player.stop()
    player.play.assert_called_with(None, replace=True)
