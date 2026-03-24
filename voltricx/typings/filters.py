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


class Equalizer(LavalinkBaseModel):
    band: int
    gain: float


# EqualizerFilter model is replaced by a direct list in Filters


class Karaoke(LavalinkBaseModel):
    level: float = 1.0
    mono_level: float = Field(default=1.0, alias="monoLevel")
    filter_band: float = Field(default=220.0, alias="filterBand")
    filter_width: float = Field(default=100.0, alias="filterWidth")


class Timescale(LavalinkBaseModel):
    speed: float = 1.0
    pitch: float = 1.0
    rate: float = 1.0


class Tremolo(LavalinkBaseModel):
    frequency: float = 2.0
    depth: float = 0.5


class Vibrato(LavalinkBaseModel):
    frequency: float = 2.0
    depth: float = 0.5


class Rotation(LavalinkBaseModel):
    rotation_hz: float = Field(default=0.0, alias="rotationHz")


class Distortion(LavalinkBaseModel):
    sin_offset: float = Field(default=0.0, alias="sinOffset")
    sin_scale: float = Field(default=1.0, alias="sinScale")
    cos_offset: float = Field(default=0.0, alias="cosOffset")
    cos_scale: float = Field(default=1.0, alias="cosScale")
    tan_offset: float = Field(default=0.0, alias="tanOffset")
    tan_scale: float = Field(default=1.0, alias="tanScale")
    offset: float = 0.0
    scale: float = 1.0


class ChannelMix(LavalinkBaseModel):
    left_to_left: float = Field(default=1.0, alias="leftToLeft")
    left_to_right: float = Field(default=0.0, alias="leftToRight")
    right_to_left: float = Field(default=0.0, alias="rightToLeft")
    right_to_right: float = Field(default=1.0, alias="rightToRight")


class LowPass(LavalinkBaseModel):
    smoothing: float = 20.0


class Filters(LavalinkBaseModel):
    volume: float = 1.0
    equalizer: list[Equalizer] = Field(default_factory=list)
    karaoke: Karaoke = Field(default_factory=lambda: Karaoke())
    timescale: Timescale = Field(default_factory=lambda: Timescale())
    tremolo: Tremolo = Field(default_factory=lambda: Tremolo())
    vibrato: Vibrato = Field(default_factory=lambda: Vibrato())
    rotation: Rotation = Field(default_factory=lambda: Rotation())
    distortion: Distortion = Field(default_factory=lambda: Distortion())
    channel_mix: ChannelMix = Field(default_factory=lambda: ChannelMix(), alias="channelMix")
    low_pass: LowPass = Field(default_factory=lambda: LowPass(), alias="lowPass")
    plugin_filters: dict[str, Any] = Field(default_factory=dict, alias="pluginFilters")
