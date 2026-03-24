"""Expanded tests for voltricx.filters — covering all remaining branches."""

import pytest

from voltricx.filters import (
    ChannelMix,
    Distortion,
    Equalizer,
    Filters,
    Karaoke,
    LowPass,
    PluginFilters,
    Rotation,
    Timescale,
    Tremolo,
    Vibrato,
)

# ── Equalizer ──────────────────────────────────────────────────────────────


def test_equalizer_str():
    eq = Equalizer()
    assert str(eq) == "Equalizer"


def test_equalizer_repr():
    eq = Equalizer()
    assert "Equalizer" in repr(eq)


def test_equalizer_set_all_bands():
    eq = Equalizer()
    bands = [{"band": i, "gain": 0.1} for i in range(15)]
    eq.set(bands)
    for i in range(15):
        assert eq.payload[i]["gain"] == pytest.approx(0.1)


def test_equalizer_set_resets_others():
    eq = Equalizer()
    eq.set_band(band=0, gain=0.5)
    eq.set([{"band": 1, "gain": 0.2}])  # only sets band 1, resets band 0
    assert eq.payload[0]["gain"] == pytest.approx(0.0)
    assert eq.payload[1]["gain"] == pytest.approx(0.2)


def test_equalizer_set_empty_none():
    eq = Equalizer()
    eq.set_band(band=0, gain=0.5)
    eq.set(None)  # should reset all
    assert eq.payload[0]["gain"] == pytest.approx(0.0)


def test_equalizer_init_with_payload():
    bands = [{"band": 2, "gain": 0.3}]
    eq = Equalizer(payload=bands)
    assert eq.payload[2]["gain"] == pytest.approx(0.3)


def test_equalizer_set_band_out_of_range():
    eq = Equalizer()
    eq.set_band(band=99, gain=1.0)  # should be ignored
    for i in range(15):
        assert eq.payload[i]["gain"] == pytest.approx(0.0)


def test_equalizer_reset_returns_self():
    eq = Equalizer()
    result = eq.reset()
    assert result is eq


# ── Karaoke ────────────────────────────────────────────────────────────────


def test_karaoke_str():
    k = Karaoke()
    assert str(k) == "Karaoke"


def test_karaoke_set_partial():
    k = Karaoke()
    k.set(level=0.3)
    assert k.level == pytest.approx(0.3)
    assert k.mono_level == pytest.approx(1.0)  # unchanged


def test_karaoke_set_all():
    k = Karaoke()
    k.set(level=0.5, mono_level=0.5, filter_band=300.0, filter_width=200.0)
    assert k.level == pytest.approx(0.5)
    assert k.mono_level == pytest.approx(0.5)
    assert k.filter_band == pytest.approx(300.0)
    assert k.filter_width == pytest.approx(200.0)


def test_karaoke_reset():
    k = Karaoke()
    k.set(level=0.0, mono_level=0.0)
    k.reset()
    assert k.level == pytest.approx(1.0)
    assert k.mono_level == pytest.approx(1.0)


# ── Timescale ──────────────────────────────────────────────────────────────


def test_timescale_str():
    t = Timescale()
    assert str(t) == "Timescale"


def test_timescale_set_partial():
    t = Timescale()
    t.set(speed=1.2)
    assert t.speed == pytest.approx(1.2)
    assert t.pitch == pytest.approx(1.0)  # unchanged


def test_timescale_set_rate():
    t = Timescale()
    t.set(rate=0.8)
    assert t.rate == pytest.approx(0.8)


def test_timescale_reset():
    t = Timescale()
    t.set(speed=2.0, pitch=2.0, rate=2.0)
    t.reset()
    assert t.speed == pytest.approx(1.0)


# ── Tremolo ────────────────────────────────────────────────────────────────


def test_tremolo_str():
    t = Tremolo()
    assert str(t) == "Tremolo"


def test_tremolo_set_and_reset():
    t = Tremolo()
    t.set(frequency=5.0, depth=0.9)
    assert t.frequency == pytest.approx(5.0)
    t.reset()
    assert t.frequency == pytest.approx(2.0)
    assert t.depth == pytest.approx(0.5)


def test_tremolo_set_partial():
    t = Tremolo()
    t.set(depth=0.9)
    assert t.depth == pytest.approx(0.9)
    assert t.frequency == pytest.approx(2.0)


# ── Vibrato ────────────────────────────────────────────────────────────────


def test_vibrato_str():
    v = Vibrato()
    assert str(v) == "Vibrato"


def test_vibrato_set_and_reset():
    v = Vibrato()
    v.set(frequency=10.0, depth=0.7)
    v.reset()
    assert v.frequency == pytest.approx(2.0)


def test_vibrato_set_partial():
    v = Vibrato()
    v.set(frequency=4.0)
    assert v.frequency == pytest.approx(4.0)


# ── Rotation ───────────────────────────────────────────────────────────────


def test_rotation_str():
    r = Rotation()
    assert str(r) == "Rotation"


def test_rotation_set_and_reset():
    r = Rotation()
    r.set(rotation_hz=0.5)
    assert r.rotation_hz == pytest.approx(0.5)
    r.reset()
    assert r.rotation_hz == pytest.approx(0.0)


def test_rotation_set_none():
    r = Rotation()
    r.set(rotation_hz=None)  # None should not change the value
    assert r.rotation_hz == pytest.approx(0.0)


# ── Distortion ────────────────────────────────────────────────────────────


def test_distortion_str():
    d = Distortion()
    assert str(d) == "Distortion"


def test_distortion_set_and_reset():
    d = Distortion()
    d.set(sin_offset=1.0, cos_scale=2.0)
    assert d.sin_offset == pytest.approx(1.0)
    d.reset()
    assert d.sin_offset == pytest.approx(0.0)


def test_distortion_set_ignores_none():
    d = Distortion()
    d.set(sin_offset=None)  # None should be skipped
    assert d.sin_offset == pytest.approx(0.0)


# ── ChannelMix ────────────────────────────────────────────────────────────


def test_channelmix_str():
    c = ChannelMix()
    assert str(c) == "ChannelMix"


def test_channelmix_set_and_reset():
    c = ChannelMix()
    c.set(left_to_right=0.5, right_to_left=0.5)
    assert c.left_to_right == pytest.approx(0.5)
    c.reset()
    assert c.left_to_right == pytest.approx(0.0)


def test_channelmix_set_partial():
    c = ChannelMix()
    c.set(left_to_left=0.8)
    assert c.left_to_left == pytest.approx(0.8)
    assert c.left_to_right == pytest.approx(0.0)


# ── LowPass ───────────────────────────────────────────────────────────────


def test_lowpass_str():
    lp = LowPass()
    assert str(lp) == "LowPass"


def test_lowpass_set_and_reset():
    lp = LowPass()
    lp.set(smoothing=50.0)
    assert lp.smoothing == pytest.approx(50.0)
    lp.reset()
    assert lp.smoothing == pytest.approx(20.0)


def test_lowpass_set_none():
    lp = LowPass()
    lp.set(smoothing=None)
    assert lp.smoothing == pytest.approx(20.0)


# ── PluginFilters ─────────────────────────────────────────────────────────


def test_plugin_filters_str():
    pf = PluginFilters()
    assert str(pf) == "PluginFilters"


def test_plugin_filters_set_and_payload():
    pf = PluginFilters()
    pf.set(custom_plugin={"param": "value"})
    assert pf.payload == {"custom_plugin": {"param": "value"}}


def test_plugin_filters_reset():
    pf = PluginFilters()
    pf.set(some_key="val")
    pf.reset()
    assert pf.payload == {}


def test_plugin_filters_init_with_data():
    pf = PluginFilters(data={"x": 1})
    assert pf.payload == {"x": 1}


# ── Filters (full object) ──────────────────────────────────────────────────


def test_filters_repr():
    f = Filters()
    assert "volume" in repr(f)


def test_filters_call_returns_dict():
    f = Filters()
    result = f()
    assert isinstance(result, dict)


def test_filters_set_filters_method():
    f = Filters()
    result = f.set_filters(volume=0.5)
    assert f.volume == pytest.approx(0.5)
    assert result is f


def test_filters_set_filters_with_reset():
    f = Filters()
    f.equalizer.set_band(band=0, gain=0.5)
    f.set_filters(reset=True)
    assert f.to_dict() == {}


def test_filters_from_filters_factory():
    f = Filters.from_filters(volume=0.8)
    assert f.volume == pytest.approx(0.8)


def test_filters_to_dict_with_volume():
    f = Filters()
    f.volume = 0.5
    payload = f.to_dict()
    assert payload["volume"] == pytest.approx(0.5)


def test_filters_to_dict_with_rotation():
    f = Filters()
    f.rotation.set(rotation_hz=0.2)
    payload = f.to_dict()
    assert "rotation" in payload


def test_filters_to_dict_with_tremolo():
    f = Filters()
    f.tremolo.set(frequency=5.0, depth=0.8)
    payload = f.to_dict()
    assert "tremolo" in payload


def test_filters_to_dict_with_vibrato():
    f = Filters()
    f.vibrato.set(frequency=5.0, depth=0.8)
    payload = f.to_dict()
    assert "vibrato" in payload


def test_filters_to_dict_with_distortion():
    f = Filters()
    f.distortion.set(sin_offset=1.0)
    payload = f.to_dict()
    assert "distortion" in payload


def test_filters_to_dict_with_channelmix():
    f = Filters()
    f.channel_mix.set(left_to_right=0.5)
    payload = f.to_dict()
    assert "channelMix" in payload


def test_filters_to_dict_with_lowpass():
    f = Filters()
    f.low_pass.set(smoothing=50.0)
    payload = f.to_dict()
    assert "lowPass" in payload


def test_filters_to_dict_with_plugin_filters():
    f = Filters()
    f.plugin_filters.set(my_plugin={"k": "v"})
    payload = f.to_dict()
    assert "pluginFilters" in payload


def test_filters_create_from_dict_all_fields():
    data = {
        "volume": 0.9,
        "equalizer": [{"band": 0, "gain": 0.1}],
        "timescale": {"speed": 1.2},
        "tremolo": {"frequency": 3.0, "depth": 0.4},
        "vibrato": {"frequency": 3.0, "depth": 0.4},
        "rotation": {"rotationHz": 0.3},
        "distortion": {"sinOffset": 0.1},
        "channelMix": {"leftToLeft": 0.9},
        "lowPass": {"smoothing": 30.0},
        "pluginFilters": {"x": 1},
    }
    f = Filters(data=data)
    assert f.volume == pytest.approx(0.9)
    assert f.timescale.speed == pytest.approx(1.2)
    assert f.tremolo.frequency == pytest.approx(3.0)
    assert f.vibrato.frequency == pytest.approx(3.0)
    assert f.rotation.rotation_hz == pytest.approx(0.3)
    assert f.distortion.sin_offset == pytest.approx(0.1)
    assert f.channel_mix.left_to_left == pytest.approx(0.9)
    assert f.low_pass.smoothing == pytest.approx(30.0)
    assert f.plugin_filters.payload == {"x": 1}
