import argparse
from pathlib import Path

from image_mask import image_to_mask
from maze import Maze
from renderer import render_maze


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate a perfect maze, optionally shaped by an input image."
    )
    parser.add_argument(
        "image",
        nargs="?",
        help="Optional source image. Dark/opaque pixels become the maze shape.",
    )
    parser.add_argument("--cols", type=int, default=80, help="Maze columns (default: 80)")
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
    parser.add_argument("--output", default="output", help="Output directory")
    return parser.parse_args()


def build_maze(args):
    if args.image:
        mask = image_to_mask(
            args.image,
            cols=args.cols,
            rows=args.rows,
            threshold=args.threshold,
            invert=args.invert,
        )
        rows = len(mask)
        cols = len(mask[0])
    else:
        cols = args.cols
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


def main():
    args = parse_args()
    maze = build_maze(args)

    output_dir = Path(args.output)
    stem = Path(args.image).stem if args.image else "maze"
    maze_path = output_dir / f"{stem}_maze.png"
    solution_path = output_dir / f"{stem}_solution.png"

    render_maze(maze, maze_path, cell_size=args.cell_size, solution=False)
    render_maze(maze, solution_path, cell_size=args.cell_size, solution=True)

    print(f"Maze:     {maze_path}")
    print(f"Solution: {solution_path}")
    print(f"Grid:     {maze.num_cols} x {maze.num_rows}")
    print(f"Path:     {len(maze.solution_path)} cells")
    print(f"Seed:     {args.seed}")


if __name__ == "__main__":
    main()
