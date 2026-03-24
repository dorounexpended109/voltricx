from unittest.mock import patch

import pytest

from voltricx.utils import ExtrasNamespace, Namespace, build_basic_layout


@pytest.mark.asyncio
async def test_namespace_interaction():
    ns = Namespace(a=1, b=2)
    assert ns.a == 1
    assert ns.b == 2

    items = dict(list(ns))
    assert items == {"a": 1, "b": 2}


@pytest.mark.asyncio
async def test_extras_namespace():
    data = {"foo": "bar"}
    ns = ExtrasNamespace(data, baz="qux")
    assert ns.foo == "bar"
    assert ns.baz == "qux"


@pytest.mark.asyncio
@patch("discord.ui.LayoutView")
@patch("discord.ui.TextDisplay")
@patch("discord.ui.Container")
@patch("discord.ui.Section")
@patch("discord.ui.Thumbnail")
async def test_build_basic_layout(mock_thumb, mock_section, mock_container, mock_text, mock_view):
    from discord import Color

    # Setup mocks
    mock_view_inst = mock_view.return_value
    mock_container.return_value

    view = build_basic_layout(
        description="test desc",
        title="test title",
        image_url="http://example.com/img.png",
        accent_color=Color.blue(),
    )

    assert view == mock_view_inst
    mock_text.assert_any_call(content="## test title")
    mock_text.assert_any_call(content="test desc")
    mock_container.assert_called_once()
    mock_section.assert_called_once()
    mock_view_inst.add_item.assert_called()
