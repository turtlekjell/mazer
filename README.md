# Mazer

**Current release: v0.5.1**

Mazer turns an image into a **perfect maze** and automatically creates an answer key. A perfect maze has exactly one route between any two reachable cells.

The project began as a small Tkinter maze/solver exercise and now supports reproducible generation, image-shaped mazes, difficulty presets, a faded source image beneath the maze, automatic solving, and PNG export.


## Recommended: browser app

Install the dependency once:

```bash
python -m pip install -r requirements.txt
```

Then start Mazer:

```bash
python webapp.py
```

It opens a local browser interface at `http://127.0.0.1:5000`. Choose one of the reusable images in `input/` or upload your own, select a difficulty, and generate the maze and matching answer key.

For convenience, the repository also includes launch helpers:

- **macOS:** double-click `run_mazer.command` after dependencies are installed.
- **Windows:** double-click `run_mazer.bat` after dependencies are installed.

The helpers start the same local browser app; they do not install Python or Pillow for you.

## Command-line quick start

From the project folder:

```bash
python -m pip install -r requirements.txt
```

Put an image in `input/`. For example:

```text
mazer/
├── input/
│   └── Unicorn.png
├── output/
├── main.py
└── ...
```

Then generate a maze:

```bash
python main.py input/Unicorn.png --difficulty medium
```

Mazer creates a matching pair with a unique puzzle ID so files are not overwritten:

```text
output/Unicorn_20261005-201530_maze.png
output/Unicorn_20261005-201530_solution.png
```

That same puzzle ID is also printed onto both images so the maze and answer key always stay paired.

The puzzle has the source image faded beneath the maze by default. The answer key uses the same image and adds the solution path in red.

## Difficulty

Use a named preset instead of remembering grid sizes:

```bash
python main.py input/Unicorn.png --difficulty easy
python main.py input/Unicorn.png --difficulty medium
python main.py input/Unicorn.png --difficulty hard
python main.py input/Unicorn.png --difficulty extreme
```

The presets currently correspond to approximately:

| Difficulty | Grid width |
| --- | ---: |
| Easy | 35 cells |
| Medium | 60 cells |
| Hard | 90 cells |
| Extreme | 130 cells |

The image aspect ratio automatically determines the grid height. You can still use `--cols` when you want precise control; it overrides `--difficulty`.

## Recommended images

Mazer works best with a clear, connected subject:

- PNG or JPG/JPEG
- silhouettes, logos, icons, clip art, or simple illustrations
- dark subject on a light background
- transparent PNGs with a clean subject
- minimal tiny or disconnected details

Photographs can work, but thresholding is less predictable because the program must decide which pixels belong to the maze shape.

## Background image

For image mazes, the source image is placed underneath the maze at 15% opacity by default:

```bash
python main.py input/Unicorn.png --difficulty medium --background-opacity 0.15
```

Use a stronger background:

```bash
python main.py input/Unicorn.png --background-opacity 0.25
```

Or disable the background completely:

```bash
python main.py input/Unicorn.png --background-opacity 0
```

The accepted range is `0.0` through `1.0`.

## Reproduce or regenerate a maze

A seed lets you recreate the exact same maze:

```bash
python main.py input/Unicorn.png --difficulty medium --seed 42
```

Change the seed to create a different maze using the same image:

```bash
python main.py input/Unicorn.png --difficulty medium --seed 87
```

## Image detection controls

Dark pixels become maze cells by default. If an image does not detect properly, adjust the threshold:

```bash
python main.py input/Unicorn.png --threshold 180
```

A lower threshold requires darker pixels. A higher threshold includes more of the image.

For a light subject on a dark background:

```bash
python main.py input/light-logo.png --invert
```

## Advanced options

```text
--difficulty easy|medium|hard|extreme
--cols N                 exact grid width; overrides difficulty
--rows N                 exact grid height
--threshold 0-255        foreground threshold
--invert                 invert foreground/background detection
--seed N                 reproduce a maze
--cell-size N            rendered pixels per maze cell
--background-opacity N   source image opacity, 0.0-1.0
--output PATH            output directory
--version                show the installed Mazer version
```

## Rectangular maze

An image is optional. To generate a normal rectangular maze:

```bash
python main.py --cols 60 --rows 40 --seed 42
```

This creates a timestamped pair such as:

- `output/maze_20261006-090000_maze.png`
- `output/maze_20261006-090000_solution.png`

## Run tests

```bash
python -m unittest tests.py
```

## How image mazes work

1. The input image is resized into a cell grid.
2. It is converted into a boolean foreground mask.
3. Only the largest connected foreground region is kept.
4. Depth-first search carves a perfect maze through the active cells.
5. Boundary cells are selected for the entrance and exit.
6. The solver records the correct path.
7. Pillow renders the faded source image and maze walls.
8. Mazer writes a puzzle PNG and a separate solution PNG.

The `output/` folder itself is kept in Git so the program always has a target directory, but generated maze files inside it are ignored. Source images in `input/` are meant to stay trackable, so you can keep sample artwork like `Unicorn.png` in the repository.

## Browser details

The browser interface runs only on your computer and uses the same maze engine as the command line.

Then:

1. Drop or choose an image.
2. Pick **Easy**, **Medium**, **Hard**, **Extreme**, or a custom width up to 200 cells.
3. Adjust the faded-background opacity if desired.
4. Click **Generate Maze**.
5. Preview and download the maze and answer key.

Browser uploads are temporary. Mazer deletes the temporary uploaded copy after generation; the finished maze and solution remain in `output/`.

The browser defaults to a random seed so each click can produce a new maze. The seed shown with the result can be entered under **Advanced image controls** when you want to reproduce a particular maze.

### Color artwork

A single color image can already be used: Mazer converts a resized copy to grayscale to determine the maze shape, while the untouched original image is reused as the faded background. Clean illustrations with strong contrast work best. A future image-processing upgrade can improve automatic subject detection for light-colored subjects, busy backgrounds, or artwork whose silhouette is difficult to isolate.

### Built-in samples and custom difficulty

The browser automatically scans `input/` for reusable images. Any PNG, JPG/JPEG, or WebP placed there appears as a selectable sample the next time the page is loaded. The repository includes simple Heart, Star, and Lightning samples, and your own tracked images such as `Unicorn.png` can live beside them.

User uploads remain separate: they are written only to `uploads/` temporarily and deleted after generation. Files in `input/` are never deleted by the browser.

Along with Easy, Medium, Hard, and Extreme, the browser has a **Custom** difficulty. Enter a grid width from **10 to 200 cells**. A 200-cell-wide maze is intentionally excessive; it is useful for very detailed or “insanely hard” puzzles, but it also creates a larger image and can take longer to generate.

## Project folders

```text
input/      reusable sample images tracked in Git
uploads/    temporary browser uploads; generated content ignored by Git
output/     generated mazes and answer keys; generated content ignored by Git
static/     browser-interface styling
```

`output/.gitkeep` and `uploads/.gitkeep` keep those directories present in a fresh clone without committing generated files.

## Release check

Before publishing a release or pushing a major change:

```bash
python -m pip install -r requirements.txt
python -m unittest tests.py
python webapp.py
```

Confirm the browser loads, generate one sample maze, and verify both the maze and answer key download correctly.

## License

Mazer is released under the MIT License. See `LICENSE`.
