from __future__ import annotations

from pathlib import Path
from textwrap import wrap

from PIL import Image, ImageDraw, ImageFont


ROOT_DIR = Path(__file__).resolve().parents[1]
OUTPUT_PATH = ROOT_DIR / "docs" / "screenshots" / "project_flow.png"
ALTERNATE_OUTPUT_PATH = ROOT_DIR / "docs" / "screenshots" / "project_flow_swimlane.png"

WIDTH = 1800
HEIGHT = 1120
ALTERNATE_HEIGHT = 1220
BACKGROUND = "#F7F9FC"
INK = "#172033"
MUTED = "#667085"
LINE = "#98A2B3"
WHITE = "#FFFFFF"
BLUE = "#2563EB"
BLUE_TINT = "#EAF2FF"
GREEN = "#16803A"
GREEN_TINT = "#EAF7EE"
AMBER = "#B65C00"
AMBER_TINT = "#FFF4E5"
RED = "#C92A2A"
RED_TINT = "#FDECEC"
GRAY_TINT = "#EEF1F5"


def _font(size: int, *, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        Path("C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default()


TITLE_FONT = _font(46, bold=True)
SUBTITLE_FONT = _font(22)
SECTION_FONT = _font(25, bold=True)
BOX_TITLE_FONT = _font(22, bold=True)
BODY_FONT = _font(18)
SMALL_FONT = _font(16)
SMALL_BOLD_FONT = _font(16, bold=True)


def _text_size(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> tuple[int, int]:
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    return right - left, bottom - top


def _centered_text(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    text: str,
    font: ImageFont.ImageFont,
    fill: str = INK,
    *,
    max_chars: int = 36,
    spacing: int = 5,
) -> None:
    x0, y0, x1, y1 = box
    lines = []
    for paragraph in text.split("\n"):
        lines.extend(wrap(paragraph, width=max_chars) or [""])
    heights = [_text_size(draw, line, font)[1] for line in lines]
    total_height = sum(heights) + spacing * max(0, len(lines) - 1)
    y = y0 + ((y1 - y0) - total_height) / 2
    for line, line_height in zip(lines, heights):
        line_width, _ = _text_size(draw, line, font)
        draw.text((x0 + ((x1 - x0) - line_width) / 2, y), line, font=font, fill=fill)
        y += line_height + spacing


def _box(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    title: str,
    detail: str,
    *,
    accent: str,
    fill: str,
) -> None:
    draw.rounded_rectangle(box, radius=8, fill=fill, outline=accent, width=3)
    x0, y0, x1, y1 = box
    draw.rectangle((x0, y0, x0 + 12, y1), fill=accent)
    _centered_text(draw, (x0 + 28, y0 + 12, x1 - 18, y0 + 52), title, BOX_TITLE_FONT, max_chars=30)
    _centered_text(draw, (x0 + 30, y0 + 55, x1 - 20, y1 - 12), detail, BODY_FONT, MUTED, max_chars=38)


def _pill(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    text: str,
    *,
    fill: str,
    outline: str,
) -> None:
    draw.rounded_rectangle(box, radius=8, fill=fill, outline=outline, width=2)
    _centered_text(draw, box, text, SMALL_BOLD_FONT, max_chars=18)


def _arrow(
    draw: ImageDraw.ImageDraw,
    start: tuple[int, int],
    end: tuple[int, int],
    *,
    color: str = LINE,
    width: int = 5,
) -> None:
    draw.line((start, end), fill=color, width=width)
    x2, y2 = end
    x1, y1 = start
    if abs(x2 - x1) >= abs(y2 - y1):
        direction = 1 if x2 >= x1 else -1
        points = [(x2, y2), (x2 - 16 * direction, y2 - 10), (x2 - 16 * direction, y2 + 10)]
    else:
        direction = 1 if y2 >= y1 else -1
        points = [(x2, y2), (x2 - 10, y2 - 16 * direction), (x2 + 10, y2 - 16 * direction)]
    draw.polygon(points, fill=color)


def _branch_panel(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    title: str,
    subtitle: str,
    metrics: list[str],
    process_left: str,
    process_right: str,
    *,
    accent: str,
    tint: str,
) -> None:
    x0, y0, x1, y1 = box
    draw.rounded_rectangle(box, radius=8, fill=WHITE, outline=accent, width=3)
    draw.rectangle((x0, y0, x1, y0 + 64), fill=tint)
    draw.text((x0 + 24, y0 + 16), title, font=SECTION_FONT, fill=INK)
    subtitle_width, _ = _text_size(draw, subtitle, SMALL_FONT)
    draw.text((x1 - subtitle_width - 24, y0 + 22), subtitle, font=SMALL_FONT, fill=MUTED)

    gap = 14
    inner_width = x1 - x0 - 48
    pill_width = int((inner_width - gap * (len(metrics) - 1)) / len(metrics))
    pill_y0 = y0 + 92
    for index, metric in enumerate(metrics):
        pill_x0 = x0 + 24 + index * (pill_width + gap)
        _pill(draw, (pill_x0, pill_y0, pill_x0 + pill_width, pill_y0 + 62), metric, fill=tint, outline=accent)

    process_y0 = y0 + 196
    process_width = int((inner_width - 64) / 2)
    left_box = (x0 + 24, process_y0, x0 + 24 + process_width, process_y0 + 82)
    right_box = (x1 - 24 - process_width, process_y0, x1 - 24, process_y0 + 82)
    _pill(draw, left_box, process_left, fill=GRAY_TINT, outline=LINE)
    _pill(draw, right_box, process_right, fill=GRAY_TINT, outline=LINE)
    _arrow(draw, (left_box[2] + 8, (left_box[1] + left_box[3]) // 2), (right_box[0] - 8, (right_box[1] + right_box[3]) // 2), color=accent, width=4)


def generate_project_flow(output_path: Path = OUTPUT_PATH) -> Path:
    image = Image.new("RGB", (WIDTH, HEIGHT), BACKGROUND)
    draw = ImageDraw.Draw(image)

    draw.text((70, 42), "RTO SPC Dashboard: From Weekly PM Data to Engineering Review", font=TITLE_FONT, fill=INK)
    draw.text(
        (72, 102),
        "Deterministic synthetic data, baseline-only limits, auditable event rules, and a deployable review workflow",
        font=SUBTITLE_FONT,
        fill=MUTED,
    )

    top_boxes = [
        ((70, 160, 500, 280), "Synthetic PM Generator", "4 tools | 8 chambers | 7 monitor metrics", BLUE, BLUE_TINT),
        ((685, 160, 1115, 280), "monitor_measurements.csv", "Baseline + monitoring rows with hashed synthetic IDs", INK, GRAY_TINT),
        ((1300, 160, 1730, 280), "Schema Validation", "Required columns, types, allowed values, and non-empty files", GREEN, GREEN_TINT),
    ]
    for box, title, detail, accent, fill in top_boxes:
        _box(draw, box, title, detail, accent=accent, fill=fill)
    _arrow(draw, (515, 220), (670, 220), color=BLUE)
    _arrow(draw, (1130, 220), (1285, 220), color=GREEN)

    thickness_box = (70, 350, 860, 685)
    particle_box = (940, 350, 1730, 685)
    _branch_panel(
        draw,
        thickness_box,
        "Thickness SPC Path",
        "Per tool / chamber / recipe / metric",
        ["RTR Mean", "X-BAR", "WIW Stdev", "SIGMA"],
        "Baseline-only UCL / CL / LCL",
        "Warning + OOC rules",
        accent=BLUE,
        tint=BLUE_TINT,
    )
    _branch_panel(
        draw,
        particle_box,
        "Particle Alert Path",
        "Threshold logic remains separate from SPC limits",
        ["Total Adder", "Cluster Adder", "Large Adder"],
        "Fixed Warning / High thresholds",
        "Repeated-event escalation",
        accent=AMBER,
        tint=AMBER_TINT,
    )
    _arrow(draw, (1115, 280), (465, 335), color=BLUE, width=4)
    _arrow(draw, (1115, 280), (1335, 335), color=AMBER, width=4)

    output_boxes = [
        ((70, 760, 500, 890), "spc_results.csv", "Precomputed limits, flags, severity, and rule IDs", BLUE, BLUE_TINT),
        ((685, 760, 1115, 890), "excursion_events.csv", "One auditable row for every warning or OOC result", RED, RED_TINT),
        ((1300, 760, 1730, 890), "Streamlit Engineering Review", "Fleet health | 14-week overlays | drilldown | CSV export", GREEN, GREEN_TINT),
    ]
    for box, title, detail, accent, fill in output_boxes:
        _box(draw, box, title, detail, accent=accent, fill=fill)
    _arrow(draw, (465, 700), (285, 745), color=BLUE, width=4)
    _arrow(draw, (1335, 700), (285, 745), color=AMBER, width=4)
    _arrow(draw, (515, 825), (670, 825), color=RED)
    _arrow(draw, (1130, 825), (1285, 825), color=GREEN)

    ci_box = (70, 970, 1730, 1060)
    draw.rounded_rectangle(ci_box, radius=8, fill=WHITE, outline=INK, width=3)
    draw.text((95, 994), "GitHub Actions CI", font=SECTION_FONT, fill=INK)
    ci_steps = ["Regenerate data", "Validate schemas", "Run tests", "Validate release"]
    start_x = 400
    step_width = 260
    for index, step in enumerate(ci_steps):
        x0 = start_x + index * 325
        _pill(draw, (x0, 987, x0 + step_width, 1044), step, fill=GRAY_TINT, outline=LINE)
        if index < len(ci_steps) - 1:
            _arrow(draw, (x0 + step_width + 10, 1015), (x0 + 315, 1015), color=INK, width=3)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path, format="PNG", optimize=True)
    return output_path


def _lane_header(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    index: str,
    title: str,
    *,
    fill: str,
) -> None:
    x0, y0, x1, y1 = box
    draw.rounded_rectangle(box, radius=8, fill=fill)
    draw.text((x0 + 20, y0 + 13), index, font=SMALL_BOLD_FONT, fill=WHITE)
    index_width, _ = _text_size(draw, index, SMALL_BOLD_FONT)
    draw.text((x0 + index_width + 38, y0 + 9), title, font=SECTION_FONT, fill=WHITE)


def _compact_card(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    title: str,
    detail: str,
    *,
    accent: str,
    title_fill: str = INK,
    detail_chars: int = 34,
) -> None:
    x0, y0, x1, y1 = box
    draw.rounded_rectangle(box, radius=8, fill=WHITE, outline=accent, width=3)
    draw.rectangle((x0, y0, x0 + 10, y1), fill=accent)
    _centered_text(draw, (x0 + 26, y0 + 14, x1 - 18, y0 + 52), title, BOX_TITLE_FONT, title_fill, max_chars=30)
    _centered_text(
        draw,
        (x0 + 28, y0 + 58, x1 - 20, y1 - 14),
        detail,
        BODY_FONT,
        MUTED,
        max_chars=detail_chars,
    )


def _processing_lane(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    title: str,
    subtitle: str,
    metrics: list[str],
    process_left: str,
    process_right: str,
    *,
    accent: str,
    tint: str,
) -> None:
    x0, y0, x1, y1 = box
    draw.rounded_rectangle(box, radius=8, fill=WHITE, outline=accent, width=3)
    draw.rectangle((x0, y0, x1, y0 + 58), fill=tint)
    draw.text((x0 + 22, y0 + 14), title, font=BOX_TITLE_FONT, fill=INK)
    subtitle_width, _ = _text_size(draw, subtitle, SMALL_FONT)
    draw.text((x1 - subtitle_width - 22, y0 + 18), subtitle, font=SMALL_FONT, fill=MUTED)

    gap = 10
    inner_width = x1 - x0 - 44
    pill_width = int((inner_width - gap * (len(metrics) - 1)) / len(metrics))
    metric_y0 = y0 + 82
    for index, metric in enumerate(metrics):
        metric_x0 = x0 + 22 + index * (pill_width + gap)
        _pill(
            draw,
            (metric_x0, metric_y0, metric_x0 + pill_width, metric_y0 + 52),
            metric,
            fill=tint,
            outline=accent,
        )

    process_y0 = y0 + 166
    process_width = int((inner_width - 56) / 2)
    left_box = (x0 + 22, process_y0, x0 + 22 + process_width, process_y0 + 62)
    right_box = (x1 - 22 - process_width, process_y0, x1 - 22, process_y0 + 62)
    _pill(draw, left_box, process_left, fill=GRAY_TINT, outline=LINE)
    _pill(draw, right_box, process_right, fill=GRAY_TINT, outline=LINE)
    _arrow(
        draw,
        (left_box[2] + 8, (left_box[1] + left_box[3]) // 2),
        (right_box[0] - 8, (right_box[1] + right_box[3]) // 2),
        color=accent,
        width=4,
    )


def generate_project_flow_swimlane(output_path: Path = ALTERNATE_OUTPUT_PATH) -> Path:
    image = Image.new("RGB", (WIDTH, ALTERNATE_HEIGHT), BACKGROUND)
    draw = ImageDraw.Draw(image)

    draw.text((70, 42), "RTO SPC Dashboard: From Weekly PM Data to Engineering Review", font=TITLE_FONT, fill=INK)
    draw.text(
        (72, 102),
        "Deterministic synthetic data, baseline-only limits, auditable event rules, and a deployable review workflow",
        font=SUBTITLE_FONT,
        fill=MUTED,
    )

    input_column = (70, 170, 505, 900)
    rules_column = (555, 170, 1245, 900)
    output_column = (1295, 170, 1730, 900)
    for column, fill in [
        (input_column, "#EEF4FC"),
        (rules_column, "#F2F5FA"),
        (output_column, "#EEF8F1"),
    ]:
        draw.rounded_rectangle(column, radius=8, fill=fill, outline="#D0D5DD", width=2)

    _lane_header(draw, (70, 170, 505, 226), "01", "INPUT & DATA CONTRACT", fill=INK)
    _lane_header(draw, (555, 170, 1245, 226), "02", "RULE PROCESSING", fill=BLUE)
    _lane_header(draw, (1295, 170, 1730, 226), "03", "OUTPUT & REVIEW", fill=GREEN)

    generator_box = (90, 258, 485, 390)
    measurements_box = (90, 446, 485, 598)
    validation_box = (90, 654, 485, 806)
    _compact_card(
        draw,
        generator_box,
        "Synthetic PM Generator",
        "4 tools | 8 chambers | 7 monitor metrics",
        accent=BLUE,
    )
    _compact_card(
        draw,
        measurements_box,
        "monitor_measurements.csv",
        "Baseline + monitoring rows with hashed synthetic IDs",
        accent=INK,
    )
    _compact_card(
        draw,
        validation_box,
        "Schema Validation",
        "Required columns, types, allowed values, and non-empty files",
        accent=GREEN,
    )
    _arrow(draw, (287, 402), (287, 434), color=BLUE, width=4)
    _arrow(draw, (287, 610), (287, 642), color=GREEN, width=4)

    thickness_box = (575, 258, 1225, 512)
    particle_box = (575, 552, 1225, 806)
    _processing_lane(
        draw,
        thickness_box,
        "Thickness SPC Path",
        "Per tool / chamber / recipe / metric",
        ["RTR Mean", "X-BAR", "WIW Stdev", "SIGMA"],
        "Baseline-only UCL / CL / LCL",
        "Warning + OOC rules",
        accent=BLUE,
        tint=BLUE_TINT,
    )
    _processing_lane(
        draw,
        particle_box,
        "Particle Alert Path",
        "Threshold logic remains separate from SPC limits",
        ["Total Adder", "Cluster Adder", "Large Adder"],
        "Fixed Warning / High thresholds",
        "Repeated-event escalation",
        accent=AMBER,
        tint=AMBER_TINT,
    )

    branch_x = 530
    draw.line((485, 730, branch_x, 730), fill=GREEN, width=4)
    draw.line((branch_x, 385, branch_x, 679), fill=GREEN, width=4)
    _arrow(draw, (branch_x, 385), (563, 385), color=BLUE, width=4)
    _arrow(draw, (branch_x, 679), (563, 679), color=AMBER, width=4)

    spc_box = (1315, 258, 1710, 390)
    events_box = (1315, 446, 1710, 598)
    review_box = (1315, 654, 1710, 806)
    _compact_card(
        draw,
        spc_box,
        "spc_results.csv",
        "Precomputed limits, flags, severity, and rule IDs",
        accent=BLUE,
    )
    _compact_card(
        draw,
        events_box,
        "excursion_events.csv",
        "One auditable row for every warning or OOC result",
        accent=RED,
    )
    _compact_card(
        draw,
        review_box,
        "Streamlit Engineering Review",
        "Fleet health | 14-week overlays | drilldown | CSV export",
        accent=GREEN,
    )

    merge_x = 1270
    draw.line((1237, 385, merge_x, 385), fill=BLUE, width=4)
    draw.line((1237, 679, merge_x, 679), fill=AMBER, width=4)
    draw.line((merge_x, 385, merge_x, 679), fill=LINE, width=4)
    _arrow(draw, (merge_x, 385), (1303, 324), color=BLUE, width=4)
    _arrow(draw, (1512, 402), (1512, 434), color=RED, width=4)
    _arrow(draw, (1512, 610), (1512, 642), color=GREEN, width=4)

    ci_box = (70, 950, 1730, 1145)
    draw.rounded_rectangle(ci_box, radius=8, fill=WHITE, outline=INK, width=3)
    draw.rectangle((70, 950, 1730, 1008), fill=INK)
    draw.text((94, 963), "CONTINUOUS VERIFICATION", font=SECTION_FONT, fill=WHITE)
    draw.text((1452, 968), "GitHub Actions CI", font=SMALL_BOLD_FONT, fill=WHITE)

    ci_steps = ["Regenerate data", "Validate schemas", "Run tests", "Validate release"]
    step_width = 310
    step_gap = 78
    start_x = 112
    for index, step in enumerate(ci_steps):
        x0 = start_x + index * (step_width + step_gap)
        _pill(draw, (x0, 1042, x0 + step_width, 1107), step, fill=GRAY_TINT, outline=LINE)
        if index < len(ci_steps) - 1:
            _arrow(draw, (x0 + step_width + 10, 1074), (x0 + step_width + step_gap - 10, 1074), color=INK, width=3)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path, format="PNG", optimize=True)
    return output_path


if __name__ == "__main__":
    primary_path = generate_project_flow()
    alternate_path = generate_project_flow_swimlane()
    print(f"README visual created: {primary_path}")
    print(f"Alternate README visual created: {alternate_path}")
