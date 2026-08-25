"""Loading and recolouring the SVG icons."""

import base64
import re
from pathlib import Path


def _data_uri(svg_text):
    """Base64-encode SVG markup for use in an <img> src."""
    encoded = base64.b64encode(svg_text.encode("utf-8")).decode("utf-8")
    return f"data:image/svg+xml;base64,{encoded}"


def _read(svg_path):
    svg_path = Path(svg_path)

    if not svg_path.is_file():
        raise FileNotFoundError(f"Missing icon file: {svg_path}")

    return svg_path.read_text(encoding="utf-8")


def transparent_background(svg_path):
    """Drop an opaque white background. Used by the taxi icon."""

    svg_text = _read(svg_path).replace(
        "fill:#ffffff;fill-opacity:1;",
        "fill:none;fill-opacity:0;",
    )

    return _data_uri(svg_text)


def recolor_params(svg_path, color):
    """Fill in param(...) placeholders. Used by the education icon."""

    svg_text = _replace_params(_read(svg_path), color)

    return _data_uri(svg_text)


def recolor_all(svg_path, color):
    """Force every visible fill and stroke to one colour, preserving fill="none", transparent and url(...) references."""

    svg_text = _read(svg_path)

    svg_text = re.sub(
        r"<svg\b", f'<svg color="{color}"', svg_text, count=1, flags=re.IGNORECASE
    )

    svg_text = _replace_params(svg_text, color)

    for attribute in ("fill", "stroke"):
        svg_text = re.sub(
            rf'{attribute}="(?!none|transparent|url\()[^"]*"',
            f'{attribute}="{color}"',
            svg_text,
            flags=re.IGNORECASE,
        )
        svg_text = re.sub(
            rf'{attribute}\s*:\s*(?!none|transparent|url\()[^;"}}]+',
            f"{attribute}:{color}",
            svg_text,
            flags=re.IGNORECASE,
        )

    return _data_uri(svg_text)


def inline(svg_path, color, size, viewbox=None):
    """Recolour black fills and force a size, returning inline markup rather than a data URI."""

    svg = _read(svg_path)

    for black in ("#000000", "fill:#000000", "fill: #000000", "fill:black"):
        svg = svg.replace(black, black.replace("#000000", color).replace("black", color))

    svg = re.sub(r'width="[^"]*"', f'width="{size}px"', svg, count=1)
    svg = re.sub(r'height="[^"]*"', f'height="{size}px"', svg, count=1)

    if viewbox is not None:
        svg = re.sub(r'viewBox="[^"]*"', f'viewBox="{viewbox}"', svg, count=1)

    svg = re.sub(
        r"<svg\b",
        f'<svg style="width:{size}px; height:{size}px; display:block;"',
        svg,
        count=1,
    )

    return svg


def _replace_params(svg_text, color):
    svg_text = svg_text.replace('fill="param(fill)"', f'fill="{color}"')
    svg_text = svg_text.replace('stroke="param(outline)"', f'stroke="{color}"')
    return svg_text.replace(
        'stroke-width="param(outline-width)"', 'stroke-width="0"'
    )
