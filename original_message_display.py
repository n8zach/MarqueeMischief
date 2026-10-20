from dataclasses import dataclass
from html import escape
import textwrap


@dataclass(frozen=True)
class MarqueeSettings:
    wrap_width: int = 25
    max_lines: int = 4
    font_family: str = '"3606-marquee-web", sans-serif'
    font_size_px: int = 32
    min_font_size_px: int = 14
    font_weight: int = 900
    line_height: float = 1.1
    row_spacing_px: int = 4
    text_color: str = "#142327"
    background_color: str = "#ffffff"
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
        if self.row_spacing_px < 0:
            raise ValueError("row_spacing_px must be non-negative")
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

    row_line_height = font_size * settings.line_height + settings.row_spacing_px
    row_style = f"position:relative;line-height:{row_line_height}px"
    line_html = "".join(
        f'<div class="marquee-row" style="{escape(row_style, quote=True)}">'
        f"{escape(line)}</div>"
        for line in lines
    )
    font_face = (
        '<style>@font-face{font-family:"3606-marquee-web";'
        'src:url("/static/fonts/3606-marquee-web/3606-marquee-web.woff2") format("woff2");'
        'font-weight:900;font-style:normal;font-display:swap;}</style>'
    )
    rule_script = """
<script>
(() => {
    const scheduleRules = (marquee) => {
        if (marquee.dataset.rulesScheduled) return;
        marquee.dataset.rulesScheduled = "true";
        requestAnimationFrame(() => {
            delete marquee.dataset.rulesScheduled;
            const color = getComputedStyle(marquee).borderTopColor;
            const canvas = document.createElement("canvas");
            const context = canvas.getContext("2d");

            marquee.querySelectorAll(".marquee-row").forEach((row) => {
                row.querySelectorAll(".marquee-row-rule").forEach((rule) => rule.remove());
                const textNode = row.firstChild;
                if (!textNode || textNode.nodeType !== Node.TEXT_NODE) return;

                const rowStyle = getComputedStyle(row);
                context.font = `${rowStyle.fontStyle} ${rowStyle.fontWeight} ${rowStyle.fontSize} ${rowStyle.fontFamily}`;
                const groups = new Map();
                for (let offset = 0; offset < textNode.length; offset++) {
                    const range = document.createRange();
                    range.setStart(textNode, offset);
                    range.setEnd(textNode, offset + 1);
                    const rect = range.getBoundingClientRect();
                    if (rect.width === 0 || rect.height === 0) continue;
                    const lineTop = Math.round(rect.top * 100) / 100;
                    const group = groups.get(lineTop) || { top: lineTop, start: offset, end: offset + 1 };
                    group.start = Math.min(group.start, offset);
                    group.end = Math.max(group.end, offset + 1);
                    groups.set(lineTop, group);
                }

                const rowTop = row.getBoundingClientRect().top;
                const pixelRatio = window.devicePixelRatio || 1;
                const snap = (value) => Math.round(value * pixelRatio) / pixelRatio;
                groups.forEach((group) => {
                    const metrics = context.measureText(textNode.data.slice(group.start, group.end).trim());
                    const fontAscent = metrics.fontBoundingBoxAscent ?? Number.parseFloat(rowStyle.fontSize);
                    const inkTop = group.top + fontAscent - metrics.actualBoundingBoxAscent;
                    const inkBottom = group.top + fontAscent + metrics.actualBoundingBoxDescent;

                    [inkTop - 1, inkBottom].forEach((lineTop) => {
                        const rule = document.createElement("span");
                        rule.className = "marquee-row-rule";
                        rule.setAttribute("aria-hidden", "true");
                        rule.style.cssText = `position:absolute;left:0;right:0;height:1px;top:${snap(lineTop - rowTop)}px;background-color:${color};pointer-events:none;z-index:1`;
                        row.append(rule);
                    });
                });
            });
        });
    };

    document.querySelectorAll(".marquee-message").forEach((marquee) => {
        if (marquee.dataset.rulesInitialized) return;
        marquee.dataset.rulesInitialized = "true";
        const schedule = () => scheduleRules(marquee);
        marquee.addEventListener("marqueecontentchange", schedule);
        window.addEventListener("resize", schedule, { passive: true });
        if (window.ResizeObserver) new ResizeObserver(schedule).observe(marquee);
        if (document.fonts) document.fonts.ready.then(schedule);
        else schedule();
    });
})();
</script>
"""
    marquee_html = f'<div class="marquee-message" style="{escape(style, quote=True)}">{line_html}</div>'
    return f"{font_face}{marquee_html}{rule_script}"