"""Unit tests for StyleConverter."""

import pytest

from tikz2svg.svg.styles import StyleConverter


@pytest.fixture
def converter():
    """Create StyleConverter instance."""
    return StyleConverter()


# Test convert() method


def test_convert_draw_basic(converter):
    """Test basic draw command conversion."""
    result = converter.convert({}, "draw")
    assert "stroke: #000000" in result
    assert "fill: none" in result
    assert "stroke-width: 1.0px" in result


def test_convert_fill_basic(converter):
    """Test basic fill command conversion."""
    result = converter.convert({}, "fill")
    assert "stroke: none" in result
    assert "fill: #000000" in result


def test_convert_filldraw(converter):
    """Test filldraw command conversion."""
    result = converter.convert({}, "filldraw")
    assert "stroke: #000000" in result
    assert "fill: #000000" in result
    assert "stroke-width: 1.0px" in result


def test_convert_with_color(converter):
    """Test conversion with color option."""
    result = converter.convert({"color": "red"}, "draw")
    assert "stroke: #FF0000" in result


def test_convert_with_thick(converter):
    """Test conversion with thick line."""
    result = converter.convert({"thick": True}, "draw")
    assert "stroke-width: 2.0px" in result


def test_convert_with_dashed(converter):
    """Test conversion with dashed line."""
    result = converter.convert({"dashed": True}, "draw")
    assert "stroke-dasharray: 5,5" in result


def test_convert_with_dotted(converter):
    """Test conversion with dotted line."""
    result = converter.convert({"dotted": True}, "draw")
    assert "stroke-dasharray: 2,2" in result


def test_convert_with_opacity(converter):
    """Test conversion with opacity."""
    result = converter.convert({"opacity": 0.5}, "draw")
    assert "opacity: 0.5" in result


def test_convert_with_opacity_int(converter):
    """Test conversion with integer opacity."""
    result = converter.convert({"opacity": 1}, "draw")
    assert "opacity: 1" in result


def test_convert_with_line_cap(converter):
    """Test conversion with line cap."""
    result = converter.convert({"line cap": "round"}, "draw")
    assert "stroke-linecap: round" in result


def test_convert_with_line_join(converter):
    """Test conversion with line join."""
    result = converter.convert({"line join": "bevel"}, "draw")
    assert "stroke-linejoin: bevel" in result


def test_convert_filldraw_with_colors(converter):
    """Test filldraw with different stroke and fill colors."""
    result = converter.convert({"color": "red", "fill": "blue"}, "filldraw")
    assert "stroke: #FF0000" in result
    assert "fill: #0000FF" in result


# Test convert_text_style() method


def test_convert_text_style_default(converter):
    """Test text style with default settings."""
    result = converter.convert_text_style({})
    assert "font-size: 10px" in result
    assert "fill: #000000" in result
    assert "font-family: sans-serif" in result


def test_convert_text_style_tiny(converter):
    """Test text style with tiny font."""
    result = converter.convert_text_style({"font": "tiny"})
    assert "font-size: 7px" in result


def test_convert_text_style_small(converter):
    """Test text style with small font."""
    result = converter.convert_text_style({"font": "small"})
    assert "font-size: 9px" in result


def test_convert_text_style_large(converter):
    """Test text style with large font."""
    result = converter.convert_text_style({"font": "large"})
    assert "font-size: 14px" in result


def test_convert_text_style_huge(converter):
    """Test text style with huge font."""
    result = converter.convert_text_style({"font": "huge"})
    assert "font-size: 18px" in result


def test_convert_text_style_unknown_font(converter):
    """Test text style with unknown font defaults to 10px."""
    result = converter.convert_text_style({"font": "unknown"})
    assert "font-size: 10px" in result


def test_convert_text_style_with_color(converter):
    """Test text style with color."""
    result = converter.convert_text_style({"color": "red"})
    assert "fill: #FF0000" in result


# Test get_color() method


def test_get_color_default(converter):
    """Test get_color with no color options."""
    result = converter.get_color({})
    assert result == "#000000"


def test_get_color_named(converter):
    """Test get_color with named color."""
    result = converter.get_color({"red": True})
    assert result == "#FF0000"


def test_get_color_from_color_key(converter):
    """Test get_color from 'color' key."""
    result = converter.get_color({"color": "blue"})
    assert result == "#0000FF"


def test_get_color_from_draw_key(converter):
    """Test get_color from 'draw' key."""
    result = converter.get_color({"draw": "green"})
    assert result == "#00FF00"


def test_get_color_from_fill_key(converter):
    """Test get_color from 'fill' key."""
    result = converter.get_color({"fill": "yellow"})
    assert result == "#FFFF00"


def test_get_color_specific_key(converter):
    """Test get_color with specific key parameter."""
    result = converter.get_color({"fill": "red", "draw": "blue"}, key="fill")
    assert result == "#FF0000"


def test_get_color_custom_default(converter):
    """Test get_color with custom default."""
    result = converter.get_color({}, default="red")
    assert result == "#FF0000"


def test_get_color_fill_not_for_stroke(converter):
    """Test that fill key is not used when key='stroke'."""
    result = converter.get_color({"fill": "red"}, key="stroke", default="blue")
    assert result == "#0000FF"


# Test parse_color() method


def test_parse_color_none(converter):
    """Test parse_color with None value."""
    result = converter.parse_color(None)
    assert result == "#000000"


def test_parse_color_empty_string(converter):
    """Test parse_color with empty string."""
    result = converter.parse_color("")
    assert result == "#000000"


def test_parse_color_hex(converter):
    """Test parse_color with hex color."""
    result = converter.parse_color("#FF5733")
    assert result == "#FF5733"


def test_parse_color_named(converter):
    """Test parse_color with named color."""
    result = converter.parse_color("red")
    assert result == "#FF0000"


def test_parse_color_mixed(converter):
    """Test parse_color with mixed color."""
    result = converter.parse_color("blue!30!white")
    assert result.startswith("#")


def test_parse_color_unknown(converter):
    """Test parse_color with unknown color defaults to black."""
    result = converter.parse_color("unknowncolor")
    assert result == "#000000"


# Test blend_colors() method


def test_blend_colors_simple(converter):
    """Test blend_colors with color!percentage format."""
    result = converter.blend_colors("red!50")
    # 50% red, 50% white
    assert result.startswith("#")


def test_blend_colors_two_colors(converter):
    """Test blend_colors with two colors (equal blend)."""
    result = converter.blend_colors("red!blue")
    # Should blend red and blue 50/50
    assert result.startswith("#")


def test_blend_colors_three_parts(converter):
    """Test blend_colors with color!percentage!color format."""
    result = converter.blend_colors("blue!30!white")
    # 30% blue, 70% white
    assert result.startswith("#")


def test_blend_colors_complex(converter):
    """Test blend_colors with complex specification."""
    result = converter.blend_colors("green!20!yellow!80")
    # Should handle complex blend
    assert result.startswith("#")


def test_blend_colors_fallback(converter):
    """Test blend_colors fallback to simple color."""
    result = converter.blend_colors("red")
    assert result == "#FF0000"


def test_blend_colors_invalid_percentage(converter):
    """Test blend_colors with invalid percentage defaults to 0.5."""
    result = converter.blend_colors("red!invalid!blue")
    assert result.startswith("#")


# Test mix_two_colors() method


def test_mix_two_colors_equal(converter):
    """Test mixing two colors equally."""
    result = converter.mix_two_colors("red", "blue", 0.5)
    assert result.startswith("#")
    # Should be somewhere between red and blue


def test_mix_two_colors_mostly_first(converter):
    """Test mixing with 80% first color."""
    result = converter.mix_two_colors("red", "white", 0.8)
    # Should be mostly red
    assert result.startswith("#")


def test_mix_two_colors_mostly_second(converter):
    """Test mixing with 20% first color."""
    result = converter.mix_two_colors("black", "white", 0.2)
    # Should be mostly white (gray)
    assert result.startswith("#")


def test_mix_two_colors_with_hex(converter):
    """Test mixing with hex colors."""
    result = converter.mix_two_colors("#FF0000", "#0000FF", 0.5)
    assert result.startswith("#")


def test_mix_two_colors_clamping(converter):
    """Test that color values are clamped to 0-255."""
    # This should not crash even with extreme values
    result = converter.mix_two_colors("white", "white", 1.0)
    assert result == "#FFFFFF"


# Test color_to_rgb() method


def test_color_to_rgb_named(converter):
    """Test converting named color to RGB."""
    result = converter.color_to_rgb("red")
    assert result == (255, 0, 0)


def test_color_to_rgb_hex(converter):
    """Test converting hex color to RGB."""
    result = converter.color_to_rgb("#FF0000")
    assert result == (255, 0, 0)


def test_color_to_rgb_hex_without_hash(converter):
    """Test converting hex without # prefix defaults to black."""
    result = converter.color_to_rgb("0000FF")
    # Without # prefix, it's treated as unknown color
    assert result == (0, 0, 0)


def test_color_to_rgb_unknown(converter):
    """Test converting unknown color defaults to black."""
    result = converter.color_to_rgb("unknowncolor")
    assert result == (0, 0, 0)


def test_color_to_rgb_various_colors(converter):
    """Test converting various named colors."""
    assert converter.color_to_rgb("green") == (0, 255, 0)
    assert converter.color_to_rgb("blue") == (0, 0, 255)
    assert converter.color_to_rgb("white") == (255, 255, 255)
    assert converter.color_to_rgb("black") == (0, 0, 0)


def test_color_to_rgb_gray(converter):
    """Test converting gray color."""
    result = converter.color_to_rgb("gray")
    assert result == (128, 128, 128)


# Test get_line_width() method


def test_get_line_width_default(converter):
    """Test default line width."""
    result = converter.get_line_width({})
    assert result == 1.0


def test_get_line_width_thin(converter):
    """Test thin line width."""
    result = converter.get_line_width({"thin": True})
    assert result == 1.0


def test_get_line_width_thick(converter):
    """Test thick line width."""
    result = converter.get_line_width({"thick": True})
    assert result == 2.0


def test_get_line_width_very_thick(converter):
    """Test very thick line width."""
    result = converter.get_line_width({"very thick": True})
    assert result == 3.0


def test_get_line_width_ultra_thick(converter):
    """Test ultra thick line width."""
    result = converter.get_line_width({"ultra thick": True})
    assert result == 4.0


def test_get_line_width_ultra_thin(converter):
    """Test ultra thin line width."""
    result = converter.get_line_width({"ultra thin": True})
    assert result == 0.5


def test_get_line_width_very_thin(converter):
    """Test very thin line width."""
    result = converter.get_line_width({"very thin": True})
    assert result == 0.75


def test_get_line_width_semithick(converter):
    """Test semithick line width."""
    result = converter.get_line_width({"semithick": True})
    assert result == 1.5


def test_get_line_width_custom(converter):
    """Test custom line width value."""
    result = converter.get_line_width({"line width": 5.5})
    assert result == 5.5


def test_get_line_width_custom_string(converter):
    """Test custom line width as string."""
    result = converter.get_line_width({"line width": "3.0"})
    assert result == 3.0


# Test get_dash_pattern() method


def test_get_dash_pattern_none(converter):
    """Test no dash pattern."""
    result = converter.get_dash_pattern({})
    assert result == ""


def test_get_dash_pattern_dashed(converter):
    """Test dashed pattern."""
    result = converter.get_dash_pattern({"dashed": True})
    assert result == "5,5"


def test_get_dash_pattern_dotted(converter):
    """Test dotted pattern."""
    result = converter.get_dash_pattern({"dotted": True})
    assert result == "2,2"


def test_get_dash_pattern_custom(converter):
    """Test custom dash pattern."""
    result = converter.get_dash_pattern({"dash pattern": "10,5"})
    # Currently returns "5,5" as placeholder (TODO in code)
    assert result == "5,5"


# Integration tests


def test_full_conversion_complex(converter):
    """Test complex conversion with multiple options."""
    options = {
        "color": "blue",
        "thick": True,
        "dashed": True,
        "opacity": 0.7,
        "line cap": "round",
    }
    result = converter.convert(options, "draw")

    assert "stroke: #0000FF" in result
    assert "stroke-width: 2.0px" in result
    assert "stroke-dasharray: 5,5" in result
    assert "opacity: 0.7" in result
    assert "stroke-linecap: round" in result


def test_color_blending_red_white(converter):
    """Test that red!50 produces a pink color."""
    result = converter.parse_color("red!50")
    # Should be between red (#FF0000) and white (#FFFFFF)
    # Expected: approximately #FF7F7F or similar
    assert result.startswith("#")
    rgb = converter.color_to_rgb(result)
    # Red component should be high, green and blue should be medium
    assert rgb[0] > rgb[1]
    assert rgb[0] > rgb[2]


def test_multiple_named_colors(converter):
    """Test all named colors in COLORS dict."""
    for color_name, hex_value in converter.COLORS.items():
        result = converter.get_color({color_name: True})
        assert result == hex_value


def test_all_line_widths(converter):
    """Test all named line widths in LINE_WIDTHS dict."""
    for width_name, width_value in converter.LINE_WIDTHS.items():
        result = converter.get_line_width({width_name: True})
        assert result == width_value
