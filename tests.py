import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw

from image_mask import image_to_mask, largest_connected_component
from maze import Maze
from renderer import render_maze


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
            render_maze(maze, output, cell_size=8, solution=True)
            self.assertTrue(output.exists())
            self.assertGreater(output.stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
