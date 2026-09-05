"""Chart image generation (Pillow).

Renders a candlestick chart with optional SMA overlays to a PNG so reports
can include a visual along with the text. Pure drawing — no analysis logic —
so it stays safe to replace with a heavier charting library later.
"""

from __future__ import annotations

import logging
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .domain import Candle

logger = logging.getLogger(__name__)

WIDTH, HEIGHT = 1000, 460
PAD_LEFT, PAD_RIGHT, PAD_TOP, PAD_BOTTOM = 70, 30, 40, 46

BG = (19, 23, 34)
GRID = (38, 45, 60)
TEXT = (205, 211, 225)
UP = (38, 166, 154)     # green candles
DOWN = (239, 83, 80)    # red candles
MA_COLORS = [(66, 165, 245, 255), (255, 213, 79, 255)]


def _font(size: int):
    """Try common fonts; fall back to Pillow's default bitmap font."""
    for name in ("DejaVuSans.ttf", "Arial.ttf", "arial.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def render_chart(
    candles: list[Candle],
    output_path: Path,
    title: str,
    ma_series: list[list[float | None]] | None = None,
) -> Path:
    """Draw candles + optional aligned SMA overlays and save a PNG.

    ``ma_series`` entries must align with ``candles`` (None = warm-up gap).
    Returns the written path.
    """
    if len(candles) < 2:
        raise ValueError("Need at least 2 candles to render a chart")

    lows = [c.low for c in candles]
    highs = [c.high for c in candles]
    min_price = min(lows)
    max_price = max(highs)
    overlays = ma_series or []
    for series in overlays:
        values = [v for v in series if v is not None]
        if values:
            min_price = min(min_price, min(values))
            max_price = max(max_price, max(values))
    span = max_price - min_price
    if span <= 0:
        span = max_price * 0.01 or 1.0
    # Add a little headroom above the extremes.
    min_price -= span * 0.05
    max_price += span * 0.05

    def y_for(price: float) -> float:
        return PAD_TOP + (max_price - price) / (max_price - min_price) * (HEIGHT - PAD_TOP - PAD_BOTTOM)

    plot_w = WIDTH - PAD_LEFT - PAD_RIGHT
    step = plot_w / (len(candles) - 1)

    image = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(image)
    title_font = _font(18)
    small_font = _font(12)

    # Grid + price labels.
    for i in range(6):
        ratio = i / 5.0
        grid_y = PAD_TOP + ratio * (HEIGHT - PAD_TOP - PAD_BOTTOM)
        draw.line([(PAD_LEFT, grid_y), (WIDTH - PAD_RIGHT, grid_y)], fill=GRID, width=1)
        price = max_price - ratio * (max_price - min_price)
        draw.text((8, grid_y - 8), f"{price:,.2f}", font=small_font, fill=TEXT)

    # Candles.
    body_w = max(2.0, step * 0.6)
    for i, candle in enumerate(candles):
        x = PAD_LEFT + i * step
        color = UP if candle.close >= candle.open else DOWN
        draw.line([(x, y_for(candle.high)), (x, y_for(candle.low))], fill=color, width=1)
        top = min(y_for(candle.open), y_for(candle.close))
        bottom = max(y_for(candle.open), y_for(candle.close))
        if bottom - top < 1:
            bottom = top + 1
        draw.rectangle([x - body_w / 2, top, x + body_w / 2, bottom], fill=color)

    # MA overlays (polyline across aligned series values).
    for index, series in enumerate(overlays):
        points: list[tuple[float, float]] = []
        for i, value in enumerate(series):
            if value is not None:
                points.append((PAD_LEFT + i * step, y_for(value)))
        if len(points) > 1:
            draw.line(points, fill=MA_COLORS[index % len(MA_COLORS)], width=2)

    draw.text((PAD_LEFT, 12), title, font=title_font, fill=TEXT)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path, "PNG")
    logger.info("Chart saved to %s", output_path)
    return output_path
