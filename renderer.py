from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont


def render_maze(
    maze,
    path,
    cell_size=12,
    padding=20,
    wall_width=2,
    solution=False,
    background_image=None,
    background_opacity=0.0,
    footer_lines=None,
):
    if cell_size < 4:
        raise ValueError("cell_size must be at least 4")
    if not 0.0 <= background_opacity <= 1.0:
        raise ValueError("background_opacity must be between 0.0 and 1.0")

    footer_lines = [line for line in (footer_lines or []) if line]
    font = ImageFont.load_default()
    footer_height = _footer_height(footer_lines, font)

    width = maze.num_cols * cell_size + padding * 2
    height = maze.num_rows * cell_size + padding * 2 + footer_height
    image = Image.new("RGBA", (width, height), "white")

    if background_image and background_opacity > 0:
        _add_background(
            image,
            maze,
            background_image,
            cell_size=cell_size,
            padding=padding,
            opacity=background_opacity,
        )

    draw = ImageDraw.Draw(image)

    for col in range(maze.num_cols):
        for row in range(maze.num_rows):
            cell = maze.cells[col][row]
            if not cell.active:
                continue

            x1 = padding + col * cell_size
            y1 = padding + row * cell_size
            x2 = x1 + cell_size
            y2 = y1 + cell_size

            if cell.has_top_wall:
                draw.line((x1, y1, x2, y1), fill="black", width=wall_width)
            if cell.has_right_wall:
                draw.line((x2, y1, x2, y2), fill="black", width=wall_width)
            if cell.has_bottom_wall:
                draw.line((x1, y2, x2, y2), fill="black", width=wall_width)
            if cell.has_left_wall:
                draw.line((x1, y1, x1, y2), fill="black", width=wall_width)

    if solution:
        points = [
            (
                padding + col * cell_size + cell_size // 2,
                padding + row * cell_size + cell_size // 2,
            )
            for col, row in maze.solution_path
        ]
        if len(points) > 1:
            draw.line(points, fill="#d11f1f", width=max(2, wall_width + 1), joint="curve")

    _draw_marker(draw, maze.start, maze.start_opening, cell_size, padding, "S", "#167d32")
    _draw_marker(draw, maze.end, maze.end_opening, cell_size, padding, "E", "#1957b8")

    if footer_lines:
        _draw_footer(draw, image.width, image.height, padding, footer_lines, font)

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    image.convert("RGB").save(path)
    return path


def _footer_height(lines, font):
    if not lines:
        return 0
    bbox = font.getbbox("Ag")
    line_height = bbox[3] - bbox[1]
    return line_height * len(lines) + 14


def _draw_footer(draw, image_width, image_height, padding, lines, font):
    bbox = font.getbbox("Ag")
    line_height = bbox[3] - bbox[1]
    block_height = line_height * len(lines)
    top = image_height - block_height - 8
    separator_y = top - 6
    draw.line((padding, separator_y, image_width - padding, separator_y), fill="#cfcfcf", width=1)

    for index, line in enumerate(lines):
        y = top + index * line_height
        draw.text((padding, y), line, fill="#555555", font=font)


def _add_background(canvas, maze, source_path, cell_size, padding, opacity):
    """Fade the source image beneath the maze, clipped to active maze cells."""
    grid_width = maze.num_cols * cell_size
    grid_height = maze.num_rows * cell_size

    with Image.open(source_path) as source:
        source = source.convert("RGBA").resize(
            (grid_width, grid_height), Image.Resampling.LANCZOS
        )

    active_mask = Image.new("L", (grid_width, grid_height), 0)
    mask_draw = ImageDraw.Draw(active_mask)
    for col in range(maze.num_cols):
        for row in range(maze.num_rows):
            if not maze.cells[col][row].active:
                continue
            x1 = col * cell_size
            y1 = row * cell_size
            mask_draw.rectangle(
                (x1, y1, x1 + cell_size - 1, y1 + cell_size - 1), fill=255
            )

    source_alpha = source.getchannel("A").point(lambda value: round(value * opacity))
    source.putalpha(ImageChops.multiply(source_alpha, active_mask))
    canvas.alpha_composite(source, (padding, padding))


def _draw_marker(draw, cell, opening, cell_size, padding, label, color):
    col, row = cell
    cx = padding + col * cell_size + cell_size // 2
    cy = padding + row * cell_size + cell_size // 2
    radius = max(2, cell_size // 5)
    draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), fill=color)

    # For larger cells, add a tiny S/E label just outside the maze opening.
    if cell_size >= 14:
        offsets = {
            "top": (0, -cell_size // 2 - 8),
            "right": (cell_size // 2 + 5, -5),
            "bottom": (0, cell_size // 2 + 2),
            "left": (-cell_size // 2 - 10, -5),
        }
        dx, dy = offsets.get(opening, (0, 0))
        draw.text((cx + dx, cy + dy), label, fill=color)
