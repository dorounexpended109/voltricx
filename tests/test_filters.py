import pytest

from voltricx import Equalizer, Filters

# These tests are legacy from pre-refactor. Comprehensive filter tests are in test_filters_extended.py
pytestmark = pytest.mark.skip(reason="Legacy tests - see test_filters_extended.py")


@pytest.mark.asyncio
async def test_filters_initialization():
    f = Filters()
    assert f.volume == 1.0
    assert isinstance(f.equalizer, Equalizer)
    # Empty filters dict because all are at defaults
    payload = f.to_dict()
    # Should be empty or only contain defaults that shouldn't be sent
    assert payload == {} or all(k in ["volume", "equalizer"] for k in payload.keys())


@pytest.mark.asyncio
async def test_equalizer_bands():
    eq = Equalizer()
    eq.set_band(band=0, gain=0.25)
    payload = eq.payload
    assert payload[0]["gain"] == 0.25
    assert payload[1]["gain"] == 0.0


@pytest.mark.asyncio
async def test_filters_with_equalizer():
    f = Filters()
    f.equalizer.set_band(band=0, gain=0.25)
    payload = f.to_dict()
    assert "equalizer" in payload
    assert payload["equalizer"][0]["gain"] == 0.25


@pytest.mark.asyncio
async def test_karaoke_filter():
    f = Filters()
    f.karaoke.set(level=0.5, mono_level=0.5)
    payload = f.to_dict()
    assert "karaoke" in payload
    assert payload["karaoke"]["level"] == 0.5
    assert payload["karaoke"]["monoLevel"] == 0.5


@pytest.mark.asyncio
async def test_timescale_filter():
    f = Filters()
    f.timescale.set(speed=1.5, pitch=1.5)
    payload = f.to_dict()
    assert "timescale" in payload
    assert payload["timescale"]["speed"] == 1.5
    assert payload["timescale"]["pitch"] == 1.5


@pytest.mark.asyncio
async def test_filters_reset():
    f = Filters()
    f.volume = 0.5
    f.equalizer.set_band(band=0, gain=0.25)
    f.reset()
    assert f.volume == 1.0
    # After reset, filters should be at defaults
    payload = f.to_dict()
    assert payload == {} or all(k in ["volume"] for k in payload.keys())


@pytest.mark.asyncio
async def test_filters_from_dict():
    data = {"volume": 0.8, "karaoke": {"level": 0.5, "monoLevel": 0.5}}
    f = Filters(data=data)
    assert f.volume == 0.8
    assert f.karaoke.level == 0.5
    assert f.karaoke.mono_level == 0.5
