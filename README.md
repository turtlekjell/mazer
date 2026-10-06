# Mazer

Mazer generates and solves **perfect mazes** (every reachable cell has exactly one route to every other cell). It can create a normal rectangular maze or use an image as the shape of the maze.

The project began as a small Tkinter maze/solver exercise and has been updated to support reproducible generation, image masks, automatic solving, and PNG answer-key export.

## Install

```bash
python -m pip install -r requirements.txt
```

## Make a rectangular maze

```bash
python main.py --cols 60 --rows 40 --seed 42
```

This writes:

- `output/maze_maze.png`
- `output/maze_solution.png`

## Make a maze from an image

For best results, start with a simple logo, silhouette, icon, or other high-contrast image.

```bash
python main.py input/turtle.png --cols 90 --seed 42
```

Mazer turns dark pixels into maze cells, keeps the largest connected shape, generates a maze inside it, picks boundary entrance/exit points, solves it, and exports both the puzzle and answer key.

Useful image options:

```bash
python main.py input/turtle.png --cols 100 --threshold 180 --seed 7
python main.py input/light-logo.png --cols 100 --invert
```

- `--cols`: detail/difficulty. Larger values create more cells.
- `--rows`: optional; otherwise image aspect ratio determines the row count.
- `--threshold`: which pixels count as foreground (0-255).
- `--invert`: use for a light subject on a dark background.
- `--seed`: reproduce the exact same maze.
- `--cell-size`: PNG resolution per maze cell.
- `--output`: output directory.

## Run tests

```bash
python -m unittest tests.py
```

## How it works

1. The input image is resized into a cell grid.
2. It is converted into a boolean foreground mask.
3. Only the largest connected foreground region is kept.
4. Recursive depth-first search carves a perfect maze through the active cells.
5. Boundary cells are selected for the entrance and exit.
6. A recursive solver records the solution path.
7. Pillow renders a clean maze PNG and a separate solution PNG.
