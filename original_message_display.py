from dataclasses import dataclass
from html import escape
import textwrap


@dataclass(frozen=True)
class MarqueeSettings:
    wrap_width: int = 25
    max_lines: int = 4
    font_family: str = '"Arial Black", Impact, sans-serif'
    font_size_px: int = 32
    min_font_size_px: int = 14
    font_weight: int = 900
    line_height: float = 1.1
    text_color: str = "#142327"
    background_color: str = "#e0d9d9"
    border_color: str = "#8e1717"
    border_width_px: int = 3
    border_radius_px: int = 2
    padding_px: int = 12
    text_align: str = "center"
    uppercase: bool = True

    def __post_init__(self):
        if self.wrap_width < 1 or self.max_lines < 1:
            raise ValueError("wrap_width and max_lines must be positive")
        if self.font_size_px < 1 or not 1 <= self.min_font_size_px <= self.font_size_px:
            raise ValueError("font sizes must be positive and min_font_size_px <= font_size_px")
        if self.text_align not in {"left", "center", "right"}:
            raise ValueError("text_align must be left, center, or right")


def message_to_marquee_html(message, settings=None):
    """Return a self-contained, styled HTML block for a marquee-style message."""
    settings = settings or MarqueeSettings()
    display_message = str(message).upper() if settings.uppercase else str(message)
    display_message = " ".join(display_message.split())

    render_width = settings.wrap_width
    lines = textwrap.wrap(display_message, width=render_width, break_long_words=True)
    while len(lines) > settings.max_lines:
        render_width += 1
        lines = textwrap.wrap(display_message, width=render_width, break_long_words=True)
    if not lines:
        lines = [""]

    font_size = max(
        settings.min_font_size_px,
        round(settings.font_size_px * settings.wrap_width / render_width),
    )
    style = (
        f"display:block;box-sizing:border-box;width:fit-content;"
        f"max-width:min(100%, {render_width}ch);margin-inline:auto;"
        f"padding:{settings.padding_px}px;background-color:{settings.background_color};"
        f"border:{settings.border_width_px}px solid {settings.border_color};"
        f"border-radius:{settings.border_radius_px}px;color:{settings.text_color};"
        f"font-family:{settings.font_family};font-size:{font_size}px;"
        f"font-weight:{settings.font_weight};line-height:{settings.line_height};"
    )
    
    line_html = "".join(f"<div>{escape(line)}</div>" for line in lines)
    return f'<div class="marquee-message" style="{escape(style, quote=True)}">{line_html}</div>'