import unittest
from maze import Maze

class Tests(unittest.TestCase):
    def test_maze_create_cells(self):
        num_cols = 12
        num_rows = 10
        m1 = Maze(0, 0, num_rows, num_cols, 10, 10)
        self.assertEqual(len(m1._Maze__cells), num_cols)
        self.assertEqual(len(m1._Maze__cells[0]), num_rows)

    def test_maze_small_grid(self):
        m = Maze(0, 0, 1, 1, 10, 10)
        self.assertEqual(len(m._Maze__cells), 1)
        self.assertEqual(len(m._Maze__cells[0]), 1)

    def test_maze_medium_grid(self):
        m = Maze(0, 0, 5, 7, 10, 10)
        self.assertEqual(len(m._Maze__cells), 7)
        self.assertEqual(len(m._Maze__cells[0]), 5)

    def test_maze_entrance_exit(self):
        m = Maze(0, 0, 3, 3, 10, 10)
        cells = m._Maze__cells
        print("Top-left wall value:", cells[0][0].has_top_wall)
        print("Bottom-right wall value:", cells[2][2].has_bottom_wall)
        self.assertFalse(cells[0][0].has_top_wall, "Entrance should have no top wall")
        self.assertFalse(cells[2][2].has_bottom_wall, "Exit should have no bottom wall")

    def test_reset_cells_visited(self):
        m = Maze(0, 0, 3, 3, 10, 10, seed=0)
        cells = m._Maze__cells

        # After generation, all should already be reset to False
        for col in cells:
            for cell in col:
                self.assertFalse(cell.visited)

        # Manually mark them as visited
        for col in cells:
            for cell in col:
                cell.visited = True

        # Reset
        m._Maze__reset_cells_visited()

        # Check they're reset
        for col in cells:
            for cell in col:
                self.assertFalse(cell.visited)



if __name__ == "__main__":
    unittest.main()
