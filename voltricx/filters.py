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

import math
from typing import Any, Self

from .typings.filters import (
    ChannelMix as ChannelMixModel,
)
from .typings.filters import (
    Distortion as DistortionModel,
)
from .typings.filters import (
    Equalizer as EqualizerModel,
)
from .typings.filters import (
    Karaoke as KaraokeModel,
)
from .typings.filters import (
    LowPass as LowPassModel,
)
from .typings.filters import (
    Rotation as RotationModel,
)
from .typings.filters import (
    Timescale as TimescaleModel,
)
from .typings.filters import (
    Tremolo as TremoloModel,
)
from .typings.filters import (
    Vibrato as VibratoModel,
)

__all__ = (
    "ChannelMix",
    "Distortion",
    "Equalizer",
    "Filters",
    "Karaoke",
    "LowPass",
    "PluginFilters",
    "Rotation",
    "Timescale",
    "Tremolo",
    "Vibrato",
)


class Equalizer:
    """Equalizer Filter Class.

    There are 15 bands ``0`` to ``14`` that can be changed.
    Each band has a ``gain`` which is the multiplier for the given band. ``gain`` defaults to ``0``.

    Valid ``gain`` values range from ``-0.25`` to ``1.0``, where ``-0.25`` means
    the given band is completely muted,
    and ``0.25`` means it will be doubled.

    Modifying the ``gain`` could also change the volume of the output.
    """

    def __init__(self, payload: list[dict[str, Any]] | None = None) -> None:
        """Initialize an Equalizer filter.

        Parameters
        ----------
        payload: List[Dict[str, Any]] | None
            An optional list of 15 bands to initialize the equalizer with.
            Each dictionary should contain the keys ``band`` and ``gain``.
            If not provided, all bands will be initialized with a gain of ``0.0``.
        """
        self._bands: dict[int, EqualizerModel] = {
            n: EqualizerModel(band=n, gain=0.0) for n in range(15)
        }
        if payload:
            self._set(payload)

    def _set(self, payload: list[dict[str, Any]]) -> None:
        for eq in payload:
            band: int = eq.get("band", -1)
            gain: float = eq.get("gain", 0.0)
            if 0 <= band <= 14:
                self._bands[band] = EqualizerModel(band=band, gain=gain)

    def set(self, bands: list[dict[str, Any]] | None = None) -> Self:
        """Set the bands of the Equalizer.

        This method changes **all** bands, resetting any bands not provided to ``0.0``.

        Parameters
        ----------
        bands: List[Dict[str, Any]] | None
            A list of dictionary objects containing ``band`` and ``gain``.
            ``band`` must be an integer between ``0`` and ``14``.
            ``gain`` must be a float between ``-0.25`` and ``1.0``.

        Returns
        -------
        Self
            The current instance for chaining.
        """
        # Reset all bands first as per old code behavior ("resetting any bands not provided to 0.0")
        self.reset()
        if bands:
            self._set(bands)
        return self

    def reset(self) -> Self:
        """Reset the Equalizer to its default state.

        Returns
        -------
        Self
            The current instance for chaining.
        """
        self._bands = {n: EqualizerModel(band=n, gain=0.0) for n in range(15)}
        return self

    def set_band(self, *, band: int, gain: float) -> Self:
        """Set a specific band of the Equalizer.

        Parameters
        ----------
        band: int
            The band to set, between ``0`` and ``14``.
        gain: float
            The gain for the band, between ``-0.25`` and ``1.0``.

        Returns
        -------
        Self
            The current instance for chaining.
        """
        if 0 <= band <= 14:
            self._bands[band] = EqualizerModel(band=band, gain=gain)
        return self

    @property
    def payload(self) -> list[dict[str, Any]]:
        """The raw payload associated with this filter."""
        return [m.model_dump() for m in self._bands.values()]

    def __str__(self) -> str:
        return "Equalizer"

    def __repr__(self) -> str:
        return f"<Equalizer: {list(self._bands.values())}>"


class Karaoke(KaraokeModel):
    """Karaoke Filter class.

    Uses equalization to eliminate part of a band, usually targeting vocals.
    """

    def set(
        self,
        level: float | None = None,
        mono_level: float | None = None,
        filter_band: float | None = None,
        filter_width: float | None = None,
    ) -> Self:
        """Set the properties of the Karaoke filter.

        This method does not override existing settings if they are not provided (None).

        Parameters
        ----------
        level: float | None
            The vocal elimination level, between ``0.0`` and ``1.0``.
        mono_level: float | None
            The mono level, between ``0.0`` and ``1.0``.
        filter_band: float | None
            The filter band in Hz.
        filter_width: float | None
            The filter width.

        Returns
        -------
        Self
            The current instance for chaining.
        """
        if level is not None:
            self.level = level
        if mono_level is not None:
            self.mono_level = mono_level
        if filter_band is not None:
            self.filter_band = filter_band
        if filter_width is not None:
            self.filter_width = filter_width
        return self

    def reset(self) -> Self:
        """Reset this filter to its defaults."""
        self.level = 1.0
        self.mono_level = 1.0
        self.filter_band = 220.0
        self.filter_width = 100.0
        return self

    def __str__(self) -> str:
        return "Karaoke"


class Timescale(TimescaleModel):
    """Timescale Filter class.

    Changes the speed, pitch, and rate.
    """

    def set(
        self,
        speed: float | None = None,
        pitch: float | None = None,
        rate: float | None = None,
    ) -> Self:
        """Set the properties of the Timescale filter."""
        if speed is not None:
            self.speed = speed
        if pitch is not None:
            self.pitch = pitch
        if rate is not None:
            self.rate = rate
        return self

    def reset(self) -> Self:
        self.speed = 1.0
        self.pitch = 1.0
        self.rate = 1.0
        return self

    def __str__(self) -> str:
        return "Timescale"


class Tremolo(TremoloModel):
    """The Tremolo Filter class.

    Uses amplification to create a shuddering effect, where the volume quickly oscillates.
    """

    def set(self, frequency: float | None = None, depth: float | None = None) -> Self:
        if frequency is not None:
            self.frequency = frequency
        if depth is not None:
            self.depth = depth
        return self

    def reset(self) -> Self:
        self.frequency = 2.0
        self.depth = 0.5
        return self

    def __str__(self) -> str:
        return "Tremolo"


class Vibrato(VibratoModel):
    """The Vibrato Filter class.

    Similar to tremolo. While tremolo oscillates the volume, vibrato oscillates the pitch.
    """

    def set(self, frequency: float | None = None, depth: float | None = None) -> Self:
        if frequency is not None:
            self.frequency = frequency
        if depth is not None:
            self.depth = depth
        return self

    def reset(self) -> Self:
        self.frequency = 2.0
        self.depth = 0.5
        return self

    def __str__(self) -> str:
        return "Vibrato"


class Rotation(RotationModel):
    """The Rotation Filter class.

    Rotates the sound around the stereo channels/user headphones (aka Audio Panning).
    """

    def set(self, rotation_hz: float | None = None) -> Self:
        if rotation_hz is not None:
            self.rotation_hz = rotation_hz
        return self

    def reset(self) -> Self:
        self.rotation_hz = 0.0
        return self

    def __str__(self) -> str:
        return "Rotation"


class Distortion(DistortionModel):
    """The Distortion Filter class.

    According to Lavalink "It can generate some pretty unique audio effects."
    """

    def set(self, **kwargs) -> Self:
        for k, v in kwargs.items():
            if hasattr(self, k) and v is not None:
                setattr(self, k, v)
        return self

    def reset(self) -> Self:
        self.sin_offset = 0.0
        self.sin_scale = 1.0
        self.cos_offset = 0.0
        self.cos_scale = 1.0
        self.tan_offset = 0.0
        self.tan_scale = 1.0
        self.offset = 0.0
        self.scale = 1.0
        return self

    def __str__(self) -> str:
        return "Distortion"


class ChannelMix(ChannelMixModel):
    """The ChannelMix Filter class."""

    def set(
        self,
        left_to_left: float | None = None,
        left_to_right: float | None = None,
        right_to_left: float | None = None,
        right_to_right: float | None = None,
    ) -> Self:
        if left_to_left is not None:
            self.left_to_left = left_to_left
        if left_to_right is not None:
            self.left_to_right = left_to_right
        if right_to_left is not None:
            self.right_to_left = right_to_left
        if right_to_right is not None:
            self.right_to_right = right_to_right
        return self

    def reset(self) -> Self:
        self.left_to_left = 1.0
        self.left_to_right = 0.0
        self.right_to_left = 0.0
        self.right_to_right = 1.0
        return self

    def __str__(self) -> str:
        return "ChannelMix"


class LowPass(LowPassModel):
    """The LowPass Filter class."""

    def set(self, smoothing: float | None = None) -> Self:
        if smoothing is not None:
            self.smoothing = smoothing
        return self

    def reset(self) -> Self:
        self.smoothing = 20.0
        return self

    def __str__(self) -> str:
        return "LowPass"


class PluginFilters:
    """The PluginFilters class."""

    def __init__(self, data: dict[str, Any] | None = None) -> None:
        self._data: dict[str, Any] = data or {}

    def set(self, **options: dict[str, Any]) -> Self:
        self._data.update(options)
        return self

    def reset(self) -> Self:
        self._data = {}
        return self

    @property
    def payload(self) -> dict[str, Any]:
        return self._data.copy()

    def __str__(self) -> str:
        return "PluginFilters"


class Filters:
    """The voltricx Filters class.

    This class contains the information associated with each of Lavalinks filter objects,
    as Python classes.
    Each filter can be ``set`` or ``reset`` individually.
    """

    def __init__(self, data: dict[str, Any] | None = None) -> None:
        self.volume: float = 1.0
        self.equalizer: Equalizer = Equalizer()
        self.karaoke: Karaoke = Karaoke()
        self.timescale: Timescale = Timescale()
        self.tremolo: Tremolo = Tremolo()
        self.vibrato: Vibrato = Vibrato()
        self.rotation: Rotation = Rotation()
        self.distortion: Distortion = Distortion()
        self.channel_mix: ChannelMix = ChannelMix()
        self.low_pass: LowPass = LowPass()
        self.plugin_filters: PluginFilters = PluginFilters()

        if data:
            self._create_from(data)

    def _create_from(self, data: dict[str, Any]) -> None:
        self.volume = data.get("volume", 1.0)
        if "equalizer" in data:
            self.equalizer = Equalizer(data["equalizer"])
        if "karaoke" in data:
            self.karaoke = Karaoke(**data["karaoke"])
        if "timescale" in data:
            self.timescale = Timescale(**data["timescale"])
        if "tremolo" in data:
            self.tremolo = Tremolo(**data["tremolo"])
        if "vibrato" in data:
            self.vibrato = Vibrato(**data["vibrato"])
        if "rotation" in data:
            self.rotation = Rotation(**data["rotation"])
        if "distortion" in data:
            self.distortion = Distortion(**data["distortion"])
        if "channelMix" in data:
            self.channel_mix = ChannelMix(**data["channelMix"])
        if "lowPass" in data:
            self.low_pass = LowPass(**data["lowPass"])
        if "pluginFilters" in data:
            self.plugin_filters = PluginFilters(data["pluginFilters"])

    def set_filters(self, **kwargs) -> Self:
        """Set multiple filters at once."""
        reset = kwargs.pop("reset", False)
        if reset:
            self.reset()

        for k, v in kwargs.items():
            if hasattr(self, k):
                attr = getattr(self, k)
                if hasattr(attr, "set"):
                    attr.set(**v) if isinstance(v, dict) else attr.set(v)
                else:
                    setattr(self, k, v)
        return self

    def reset(self) -> Self:
        """Method which resets this object to an original state."""
        self.volume = 1.0
        self.equalizer.reset()
        self.karaoke.reset()
        self.timescale.reset()
        self.tremolo.reset()
        self.vibrato.reset()
        self.rotation.reset()
        self.distortion.reset()
        self.channel_mix.reset()
        self.low_pass.reset()
        self.plugin_filters.reset()
        return self

    @classmethod
    def from_filters(cls, **options) -> Filters:
        """Creates a Filters object with specified filters."""
        inst = cls()
        inst.set_filters(**options)
        return inst

    @staticmethod
    def _changed(filter_obj: Any, default_cls: type) -> dict[str, Any] | None:
        """Return the filter's serialized payload if it differs from its default; else None."""
        if not filter_obj:
            return None
        data = filter_obj.model_dump(by_alias=True, exclude_none=True)
        default = default_cls().model_dump(by_alias=True, exclude_none=True)
        return data if data != default else None

    def to_dict(self) -> dict[str, Any]:
        """Generates payload for Lavalink. Only includes non-default filters."""
        payload: dict[str, Any] = {}

        # Use math.isclose to avoid direct float equality comparisons.
        if not math.isclose(self.volume, 1.0):
            payload["volume"] = self.volume

        eq = self.equalizer.payload
        if any(not math.isclose(b["gain"], 0.0) for b in eq):
            payload["equalizer"] = eq

        _sub_filters: list[tuple[Any, type, str]] = [
            (self.karaoke, KaraokeModel, "karaoke"),
            (self.timescale, TimescaleModel, "timescale"),
            (self.tremolo, TremoloModel, "tremolo"),
            (self.vibrato, VibratoModel, "vibrato"),
            (self.rotation, RotationModel, "rotation"),
            (self.distortion, DistortionModel, "distortion"),
            (self.channel_mix, ChannelMixModel, "channelMix"),
            (self.low_pass, LowPassModel, "lowPass"),
        ]
        for filter_obj, default_cls, key in _sub_filters:
            data = self._changed(filter_obj, default_cls)
            if data is not None:
                payload[key] = data

        if self.plugin_filters._data:
            payload["pluginFilters"] = self.plugin_filters.payload

        return payload

    def __call__(self) -> dict[str, Any]:
        """Retrieve the raw payload for this Filters class."""
        return self.to_dict()

    def __repr__(self) -> str:
        return (
            f"<Filters volume={self.volume} equalizer={self.equalizer!r} "
            f"karaoke={self.karaoke!r} timescale={self.timescale!r} "
            f"tremolo={self.tremolo!r} vibrato={self.vibrato!r} "
            f"rotation={self.rotation!r} distortion={self.distortion!r} "
            f"channel_mix={self.channel_mix!r} low_pass={self.low_pass!r}>"
        )
