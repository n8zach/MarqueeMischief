from dataclasses import dataclass
from html import escape
import textwrap


@dataclass(frozen=True)
class MarqueeSettings:
    wrap_width: int = 25
    max_lines: int = 4
    font_family: str = '"3606-marquee-web", sans-serif'
    font_size_px: int = 28
    min_font_size_px: int = 14
    font_weight: int = 900
    line_height: float = 1.1
    row_spacing_px: int = 3
    text_color: str = "#142327"
    background_color: str = "#ffffff"
    border_color: str = "#8e1717"
    border_width_px: int = 3
    border_radius_px: int = 2
    padding_px: int = 9
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


def message_to_marquee_html(message, settings=None, input_attrs=None):
    """Return a self-contained, styled HTML block for a marquee-style message.

    With input_attrs, the block is sized and styled the same way but holds one
    editable row carrying those HTML attributes instead of the message text.
    """
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
        f"position:relative;display:block;box-sizing:border-box;width:fit-content;"
        f"max-width:min(100%, {render_width}ch);margin-inline:auto;"
        f"padding:{settings.padding_px}px;background-color:{settings.background_color};"
        f"border:{settings.border_width_px}px solid {settings.border_color};"
        f"border-radius:{settings.border_radius_px}px;color:{settings.text_color};"
        f"font-family:{settings.font_family};font-size:{font_size}px;"
        f"font-weight:{settings.font_weight};line-height:{settings.line_height};"
    )

    row_line_height = font_size * settings.line_height + settings.row_spacing_px
    row_style = f"position:relative;line-height:{row_line_height}px"
    if input_attrs is None:
        line_html = "".join(
            f'<div class="marquee-row" data-text="{escape(line, quote=True)}" style="{escape(row_style, quote=True)}">'
            f"{escape(line)}</div>"
            for line in lines
        )
        font_face = (
            '<style>@font-face{font-family:"3606-marquee-web";'
            'src:url("/static/fonts/3606-marquee-web/3606-marquee-web.woff2") format("woff2");'
            'font-weight:900;font-style:normal;font-display:swap;}</style>'
        )
    else:
        attrs = " ".join(f'{name}="{escape(str(value), quote=True)}"' for name, value in input_attrs.items())
        input_style = f"{row_style};min-height:100%;white-space:pre-wrap"
        line_html = f'<div class="marquee-row marquee-input" style="{escape(input_style, quote=True)}" {attrs}></div>'
        font_face = ""
    rule_script = """
<script>
(() => {
    // Rules are computed from the original message's rows (data-text) and drawn on
    // every marquee on the page, so they stay put however the letters change.
    let scheduled = false;
    const drawRules = () => {
        scheduled = false;
        const source = document.querySelector(".marquee-message .marquee-row[data-text]");
        if (!source) return;
        const origin = source.closest(".marquee-message");
        const color = "#d3d3d3";
        const context = document.createElement("canvas").getContext("2d");
        const pixelRatio = window.devicePixelRatio || 1;
        const snap = (value) => Math.round(value * pixelRatio) / pixelRatio;

        // Measure a hidden clone holding the original text, so rows that the
        // browser wraps onto several visual lines each get their own rules.
        const clone = origin.cloneNode(true);
        clone.querySelectorAll(".marquee-row-rule").forEach((rule) => rule.remove());
        clone.querySelectorAll(".marquee-row[data-text]").forEach((row) => { row.textContent = row.dataset.text; });
        clone.style.cssText += ";position:absolute;visibility:hidden;pointer-events:none;left:-9999px;top:0";
        document.body.append(clone);
        const cloneTop = clone.getBoundingClientRect().top + clone.clientTop;

        const positions = [];
        clone.querySelectorAll(".marquee-row[data-text]").forEach((row) => {
            const style = getComputedStyle(row);
            context.font = `${style.fontStyle} ${style.fontWeight} ${style.fontSize} ${style.fontFamily}`;
            const textNode = row.firstChild;
            if (!textNode) return;
            const lines = new Map();
            for (let offset = 0; offset < textNode.length; offset++) {
                const range = document.createRange();
                range.setStart(textNode, offset);
                range.setEnd(textNode, offset + 1);
                const rect = range.getBoundingClientRect();
                if (rect.width === 0 || rect.height === 0) continue;
                const lineTop = Math.round(rect.top * 100) / 100;
                lines.set(lineTop, (lines.get(lineTop) || "") + textNode.data[offset]);
            }
            lines.forEach((text, lineTop) => {
                const metrics = context.measureText(text.trim());
                const ascent = metrics.fontBoundingBoxAscent ?? Number.parseFloat(style.fontSize);
                const baseline = lineTop - cloneTop + ascent;
                positions.push(baseline - metrics.actualBoundingBoxAscent - 1, baseline + metrics.actualBoundingBoxDescent);
            });
        });
        clone.remove();

        document.querySelectorAll(".marquee-message").forEach((marquee) => {
            marquee.querySelectorAll(":scope > .marquee-row-rule").forEach((rule) => rule.remove());
            positions.forEach((top) => {
                const rule = document.createElement("span");
                rule.className = "marquee-row-rule";
                rule.setAttribute("aria-hidden", "true");
                rule.style.cssText = `position:absolute;left:0;right:0;height:1px;top:${snap(top)}px;background-color:${color};pointer-events:none;z-index:1`;
                marquee.append(rule);
            });
        });
    };
    const schedule = () => {
        if (scheduled) return;
        scheduled = true;
        requestAnimationFrame(drawRules);
    };

    window.addEventListener("resize", schedule, { passive: true });
    window.addEventListener("load", schedule);
    if (window.ResizeObserver) new ResizeObserver(schedule).observe(document.querySelector(".marquee-message"));
    if (document.fonts) document.fonts.ready.then(schedule);
    else schedule();
})();
</script>
"""
    marquee_html = f'<div class="marquee-message" style="{escape(style, quote=True)}">{line_html}</div>'
    if input_attrs is not None:
        rule_script = ""
    return f"{font_face}{marquee_html}{rule_script}"