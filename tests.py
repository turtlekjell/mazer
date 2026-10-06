import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw

from image_mask import image_to_mask, largest_connected_component
from main import DIFFICULTY_COLS, build_output_paths, make_puzzle_id, resolve_columns
from maze import Maze
from renderer import render_maze
import webapp


class Tests(unittest.TestCase):
    def test_maze_create_cells(self):
        m = Maze(0, 0, 10, 12, 10, 10)
        self.assertEqual(len(m.cells), 12)
        self.assertEqual(len(m.cells[0]), 10)

    def test_maze_small_grid(self):
        m = Maze(0, 0, 1, 1, 10, 10)
        self.assertEqual(m.start, (0, 0))
        self.assertEqual(m.end, (0, 0))
        self.assertTrue(m.solve())

    def test_maze_entrance_exit(self):
        m = Maze(0, 0, 3, 3, 10, 10, seed=0)
        self.assertFalse(m.cells[0][0].has_top_wall)
        self.assertFalse(m.cells[2][2].has_bottom_wall)

    def test_seed_is_reproducible(self):
        m1 = Maze(0, 0, 8, 8, 10, 10, seed=42)
        m2 = Maze(0, 0, 8, 8, 10, 10, seed=42)
        m3 = Maze(0, 0, 8, 8, 10, 10, seed=43)
        self.assertEqual(m1.wall_signature(), m2.wall_signature())
        self.assertNotEqual(m1.wall_signature(), m3.wall_signature())

    def test_solver_returns_path(self):
        m = Maze(0, 0, 10, 12, 10, 10, seed=7)
        self.assertTrue(m.solve())
        self.assertEqual(m.solution_path[0], m.start)
        self.assertEqual(m.solution_path[-1], m.end)

    def test_mask_maze_uses_only_active_cells(self):
        mask = [
            [False, True, True, False],
            [False, True, True, True],
            [False, False, True, True],
        ]
        m = Maze(0, 0, 3, 4, 10, 10, seed=2, mask=mask)
        self.assertTrue(m.solve())
        for col, row in m.solution_path:
            self.assertTrue(mask[row][col])

    def test_largest_connected_component(self):
        mask = [
            [True, True, False, True],
            [True, False, False, True],
            [False, False, True, True],
        ]
        result = largest_connected_component(mask)
        self.assertEqual(sum(map(sum, result)), 4)

    def test_difficulty_presets_and_cols_override(self):
        self.assertEqual(resolve_columns(None, "easy"), DIFFICULTY_COLS["easy"])
        self.assertEqual(resolve_columns(None, "medium"), 60)
        self.assertEqual(resolve_columns(77, "easy"), 77)

    def test_make_puzzle_id_and_paths(self):
        now = datetime(2026, 10, 5, 20, 30, 45)
        puzzle_id = make_puzzle_id("Unicorn Magic", now=now)
        self.assertEqual(puzzle_id, "Unicorn_Magic_20261005-203045")

        built_id, maze_path, solution_path = build_output_paths("output", "Unicorn Magic", now=now)
        self.assertEqual(built_id, puzzle_id)
        self.assertEqual(maze_path, Path("output") / "Unicorn_Magic_20261005-203045_maze.png")
        self.assertEqual(solution_path, Path("output") / "Unicorn_Magic_20261005-203045_solution.png")

    def test_output_paths_do_not_overwrite_same_second(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            now = datetime(2026, 10, 5, 20, 30, 45)
            puzzle_id, maze_path, solution_path = build_output_paths(tmp, "Unicorn", now=now)
            self.assertEqual(puzzle_id, "Unicorn_20261005-203045")
            maze_path.touch()
            solution_path.touch()

            second_id, second_maze, second_solution = build_output_paths(tmp, "Unicorn", now=now)
            self.assertEqual(second_id, "Unicorn_20261005-203045-02")
            self.assertNotEqual(second_maze, maze_path)
            self.assertNotEqual(second_solution, solution_path)

    def test_browser_generation_uses_temp_upload_and_keeps_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            old_upload, old_output, old_input = webapp.UPLOAD_DIR, webapp.OUTPUT_DIR, webapp.INPUT_DIR
            webapp.UPLOAD_DIR = tmp / "uploads"
            webapp.OUTPUT_DIR = tmp / "output"
            webapp.INPUT_DIR = tmp / "input"
            try:
                source = Image.new("RGB", (100, 70), "white")
                draw = ImageDraw.Draw(source)
                draw.ellipse((15, 10, 85, 60), fill="black")
                from io import BytesIO
                buffer = BytesIO()
                source.save(buffer, format="PNG")

                result, _defaults = webapp.generate_from_form(
                    {
                        "difficulty": "custom",
                        "custom_cols": "40",
                        "opacity": "15",
                        "threshold": "160",
                        "seed": "42",
                    },
                    {"filename": "Browser Unicorn.png", "data": buffer.getvalue()},
                )
                self.assertTrue((webapp.OUTPUT_DIR / result["maze_filename"]).exists())
                self.assertTrue((webapp.OUTPUT_DIR / result["solution_filename"]).exists())
                self.assertEqual(result["grid"].split(" × ")[0], "40")
                self.assertEqual(list(webapp.UPLOAD_DIR.glob("*")), [])
            finally:
                webapp.UPLOAD_DIR, webapp.OUTPUT_DIR, webapp.INPUT_DIR = old_upload, old_output, old_input

    def test_browser_can_generate_from_input_sample_without_deleting_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            old_upload, old_output, old_input = webapp.UPLOAD_DIR, webapp.OUTPUT_DIR, webapp.INPUT_DIR
            webapp.UPLOAD_DIR = tmp / "uploads"
            webapp.OUTPUT_DIR = tmp / "output"
            webapp.INPUT_DIR = tmp / "input"
            webapp.INPUT_DIR.mkdir()
            try:
                sample = webapp.INPUT_DIR / "Sample_Heart.png"
                source = Image.new("RGB", (100, 100), "white")
                draw = ImageDraw.Draw(source)
                draw.ellipse((15, 15, 85, 85), fill="black")
                source.save(sample)

                result, _defaults = webapp.generate_from_form(
                    {
                        "sample": sample.name,
                        "difficulty": "easy",
                        "opacity": "15",
                        "threshold": "160",
                        "seed": "42",
                    },
                    None,
                )
                self.assertTrue(sample.exists())
                self.assertTrue((webapp.OUTPUT_DIR / result["maze_filename"]).exists())
                self.assertEqual(result["source_name"], "Heart")
            finally:
                webapp.UPLOAD_DIR, webapp.OUTPUT_DIR, webapp.INPUT_DIR = old_upload, old_output, old_input

    def test_browser_custom_difficulty_caps_at_200(self):
        defaults = webapp.form_defaults({"difficulty": "custom", "custom_cols": "200"})
        self.assertEqual(defaults["custom_cols"], 200)
        with self.assertRaisesRegex(ValueError, "between 10 and 200"):
            webapp.generate_from_form(
                {
                    "sample": "missing.png",
                    "difficulty": "custom",
                    "custom_cols": "201",
                    "opacity": "15",
                    "threshold": "160",
                },
                None,
            )

    def test_image_to_mask_and_render(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            source = tmp / "shape.png"
            image = Image.new("RGB", (100, 70), "white")
            draw = ImageDraw.Draw(image)
            draw.ellipse((15, 10, 85, 60), fill="black")
            image.save(source)

            mask = image_to_mask(source, cols=30, threshold=160)
            maze = Maze(0, 0, len(mask), len(mask[0]), 1, 1, seed=5, mask=mask)
            self.assertTrue(maze.solve())

            output = tmp / "maze.png"
            render_maze(
                maze,
                output,
                cell_size=8,
                solution=True,
                background_image=source,
                background_opacity=0.20,
                footer_lines=["Puzzle ID: test_123", "Difficulty: medium"],
            )
            self.assertTrue(output.exists())
            self.assertGreater(output.stat().st_size, 0)

            rendered = Image.open(output).convert("RGB")
            center = rendered.getpixel((rendered.width // 2, rendered.height // 2 - 8))
            self.assertNotEqual(center, (255, 255, 255))


if __name__ == "__main__":
    unittest.main()
