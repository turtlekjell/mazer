import argparse
import re
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

from image_mask import image_to_mask
from maze import Maze
from renderer import render_maze
from version import __version__


DIFFICULTY_COLS = {
    "easy": 35,
    "medium": 60,
    "hard": 90,
    "extreme": 130,
}


def resolve_columns(cols, difficulty):
    """Return an explicit column count, or the preset for a difficulty name."""
    if cols is not None:
        if cols < 2:
            raise ValueError("cols must be at least 2")
        return cols
    return DIFFICULTY_COLS[difficulty]


def normalize_stem(value):
    """Convert a filename stem into a filesystem-friendly base name."""
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("._-")
    return cleaned or "maze"


def make_puzzle_id(stem, now=None):
    """Build a human-readable unique ID used by both output files."""
    now = now or datetime.now()
    return f"{normalize_stem(stem)}_{now.strftime('%Y%m%d-%H%M%S')}"


def build_output_paths(output_dir, stem, now=None):
    """Return a matching, non-overwriting puzzle ID and output paths."""
    base_id = make_puzzle_id(stem, now=now)
    output_dir = Path(output_dir)
    puzzle_id = base_id
    counter = 2

    while (output_dir / f"{puzzle_id}_maze.png").exists() or (
        output_dir / f"{puzzle_id}_solution.png"
    ).exists():
        puzzle_id = f"{base_id}-{counter:02d}"
        counter += 1

    maze_path = output_dir / f"{puzzle_id}_maze.png"
    solution_path = output_dir / f"{puzzle_id}_solution.png"
    return puzzle_id, maze_path, solution_path


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate a perfect maze, optionally shaped by an input image."
    )
    parser.add_argument("--version", action="version", version=f"Mazer {__version__}")
    parser.add_argument(
        "image",
        nargs="?",
        help="Optional source image. Dark/opaque pixels become the maze shape.",
    )
    parser.add_argument(
        "--difficulty",
        choices=tuple(DIFFICULTY_COLS),
        default="medium",
        help="Maze detail preset (default: medium). --cols overrides this setting.",
    )
    parser.add_argument(
        "--cols",
        type=int,
        default=None,
        help="Explicit maze columns. Overrides --difficulty.",
    )
    parser.add_argument(
        "--rows",
        type=int,
        default=None,
        help="Maze rows. For image input, defaults to the image aspect ratio.",
    )
    parser.add_argument("--threshold", type=int, default=160, help="Image threshold 0-255")
    parser.add_argument("--invert", action="store_true", help="Invert image foreground/background")
    parser.add_argument("--seed", type=int, default=0, help="Random seed for reproducible mazes")
    parser.add_argument("--cell-size", type=int, default=12, help="Rendered cell size in pixels")
    parser.add_argument(
        "--background-opacity",
        type=float,
        default=0.15,
        help="Source-image opacity beneath image mazes, from 0.0 to 1.0 (default: 0.15)",
    )
    parser.add_argument("--output", default="output", help="Output directory")
    return parser.parse_args()


def build_maze(args):
    cols = resolve_columns(args.cols, args.difficulty)

    if args.image:
        mask = image_to_mask(
            args.image,
            cols=cols,
            rows=args.rows,
            threshold=args.threshold,
            invert=args.invert,
        )
        rows = len(mask)
        cols = len(mask[0])
    else:
        rows = args.rows or 60
        mask = None

    maze = Maze(
        x1=0,
        y1=0,
        num_rows=rows,
        num_cols=cols,
        cell_size_x=1,
        cell_size_y=1,
        seed=args.seed,
        mask=mask,
    )
    if not maze.solve():
        raise RuntimeError("Maze generation succeeded, but the maze could not be solved")
    return maze



def generate_maze_files(
    image=None,
    source_stem=None,
    difficulty="medium",
    cols=None,
    rows=None,
    threshold=160,
    invert=False,
    seed=0,
    cell_size=12,
    background_opacity=0.15,
    output="output",
):
    """Generate a maze/solution pair for CLI or browser callers."""
    if difficulty not in DIFFICULTY_COLS:
        raise ValueError(f"Unknown difficulty: {difficulty}")
    if not 0.0 <= background_opacity <= 1.0:
        raise ValueError("background_opacity must be between 0.0 and 1.0")

    args = SimpleNamespace(
        image=image,
        difficulty=difficulty,
        cols=cols,
        rows=rows,
        threshold=threshold,
        invert=invert,
        seed=seed,
        cell_size=cell_size,
        background_opacity=background_opacity,
        output=str(output),
    )
    maze = build_maze(args)

    stem = source_stem or (Path(image).stem if image else "maze")
    puzzle_id, maze_path, solution_path = build_output_paths(output, stem)
    background_image = image if image else None
    difficulty_label = difficulty if cols is None else "custom"
    footer_lines = [f"Puzzle ID: {puzzle_id}", f"Difficulty: {difficulty_label}"]

    render_maze(
        maze,
        maze_path,
        cell_size=cell_size,
        solution=False,
        background_image=background_image,
        background_opacity=background_opacity,
        footer_lines=footer_lines,
    )
    render_maze(
        maze,
        solution_path,
        cell_size=cell_size,
        solution=True,
        background_image=background_image,
        background_opacity=background_opacity,
        footer_lines=footer_lines,
    )

    return {
        "maze": maze,
        "puzzle_id": puzzle_id,
        "maze_path": maze_path,
        "solution_path": solution_path,
        "difficulty": difficulty_label,
        "seed": seed,
        "background_opacity": background_opacity,
    }

def main():
    args = parse_args()
    if not 0.0 <= args.background_opacity <= 1.0:
        raise SystemExit("--background-opacity must be between 0.0 and 1.0")

    result = generate_maze_files(
        image=args.image,
        difficulty=args.difficulty,
        cols=args.cols,
        rows=args.rows,
        threshold=args.threshold,
        invert=args.invert,
        seed=args.seed,
        cell_size=args.cell_size,
        background_opacity=args.background_opacity,
        output=args.output,
    )

    maze = result["maze"]
    print(f'Maze:       {result["maze_path"]}')
    print(f'Solution:   {result["solution_path"]}')
    print(f'Puzzle ID:  {result["puzzle_id"]}')
    print(f'Difficulty: {result["difficulty"]}')
    print(f"Grid:       {maze.num_cols} x {maze.num_rows}")
    print(f"Path:       {len(maze.solution_path)} cells")
    print(f'Seed:       {result["seed"]}')
    if args.image:
        print(f'Background: {result["background_opacity"]:.0%} opacity')


if __name__ == "__main__":
    main()
