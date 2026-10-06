from collections import deque
from pathlib import Path

from PIL import Image


NEIGHBORS = ((0, -1), (1, 0), (0, 1), (-1, 0))


def image_to_mask(path, cols=80, rows=None, threshold=160, invert=False):
    """Convert an image into a connected boolean maze mask.

    Dark pixels are treated as foreground by default. Images with transparency
    use alpha as the foreground mask, which works well for PNG silhouettes.
    Only the largest connected component is retained.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)
    if cols < 2:
        raise ValueError("cols must be at least 2")
    if not 0 <= threshold <= 255:
        raise ValueError("threshold must be between 0 and 255")

    with Image.open(path) as source:
        rgba = source.convert("RGBA")
        if rows is None:
            ratio = rgba.height / rgba.width
            rows = max(2, round(cols * ratio))
        if rows < 2:
            raise ValueError("rows must be at least 2")

        resized = rgba.resize((cols, rows), Image.Resampling.LANCZOS)
        alpha = resized.getchannel("A")
        grayscale = resized.convert("L")

        has_transparency = alpha.getextrema()[0] < 250

        mask = []
        for row in range(rows):
            row_values = []
            for col in range(cols):
                if has_transparency:
                    foreground = alpha.getpixel((col, row)) > 64
                else:
                    foreground = grayscale.getpixel((col, row)) < threshold
                if invert:
                    foreground = not foreground
                row_values.append(foreground)
            mask.append(row_values)

    connected = largest_connected_component(mask)
    if not any(any(row) for row in connected):
        raise ValueError(
            "No usable foreground found. Try a different --threshold or use --invert."
        )
    return connected


def largest_connected_component(mask):
    rows = len(mask)
    cols = len(mask[0]) if rows else 0
    visited = set()
    largest = []

    for row in range(rows):
        for col in range(cols):
            if not mask[row][col] or (col, row) in visited:
                continue

            component = []
            queue = deque([(col, row)])
            visited.add((col, row))

            while queue:
                x, y = queue.popleft()
                component.append((x, y))
                for dx, dy in NEIGHBORS:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < cols and 0 <= ny < rows:
                        if mask[ny][nx] and (nx, ny) not in visited:
                            visited.add((nx, ny))
                            queue.append((nx, ny))

            if len(component) > len(largest):
                largest = component

    result = [[False for _ in range(cols)] for _ in range(rows)]
    for col, row in largest:
        result[row][col] = True
    return result
