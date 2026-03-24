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

from collections.abc import Iterator
from types import SimpleNamespace
from typing import Any

import discord

__all__ = (
    "ExtrasNamespace",
    "Namespace",
    "build_basic_layout",
)


class Namespace(SimpleNamespace):
    """
    An iterable subclass of SimpleNamespace.
    """

    def __iter__(self) -> Iterator[tuple[str, Any]]:
        return iter(self.__dict__.items())


class ExtrasNamespace(Namespace):
    """
    A subclass of Namespace for handling arbitrary track or playlist data.

    Supports initialization from a dictionary and/or keyword arguments.
    Ported with high fidelity from the original codebase.
    """

    def __init__(self, _dict: dict[str, Any] | None = None, /, **kwargs: Any) -> None:
        updated = (_dict or {}) | kwargs
        super().__init__(**updated)


def build_basic_layout(
    description: str,
    title: str | None = None,
    image_url: str | None = None,
    accent_color: discord.Color | None = None,
) -> Any:
    """
    Builds a basic LayoutView container for Discord UI responses.

    This helper is used throughout the Player and other components for
    sending standardized UI messages.
    """

    # Note: These components are assumed to be part of the discord.py
    # environment or specific UI extensions used by Voltricx.
    view = discord.ui.LayoutView()
    items = []

    if title:
        items.append(discord.ui.TextDisplay(content=f"## {title}"))

    items.append(discord.ui.TextDisplay(content=description))

    if accent_color:
        container = discord.ui.Container(*items, accent_color=accent_color)
    else:
        container = discord.ui.Container(*items)

    if image_url:
        section = discord.ui.Section(
            title if title else "",
            description if not title else "",
            accessory=discord.ui.Thumbnail(image_url),
        )
        if not title and items:
            items.pop()
        view.add_item(section)

    view.add_item(container)
    return view
