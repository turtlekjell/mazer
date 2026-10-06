from pathlib import Path

from PIL import Image, ImageDraw


def render_maze(
    maze,
    path,
    cell_size=12,
    padding=20,
    wall_width=2,
    solution=False,
):
    if cell_size < 4:
        raise ValueError("cell_size must be at least 4")

    width = maze.num_cols * cell_size + padding * 2
    height = maze.num_rows * cell_size + padding * 2
    image = Image.new("RGB", (width, height), "white")
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

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)
    return path


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
