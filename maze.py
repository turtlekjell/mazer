import time
from cell import Cell
import random

class Maze:
    def __init__(
        self,
        x1,
        y1,
        num_rows,
        num_cols,
        cell_size_x,
        cell_size_y,
        win=None,
        seed=None
    ):
        self.__x1 = x1
        self.__y1 = y1
        self.__num_rows = num_rows
        self.__num_cols = num_cols
        self.__cell_size_x = cell_size_x
        self.__cell_size_y = cell_size_y
        self.__win = win
        self.__cells = []

        self.__create_cells()

        if seed is not None:
            random.seed(seed)


    def __create_cells(self):
    # Build the full grid of cells first
        self.__cells = [
            [Cell(self.__win) for _ in range(self.__num_rows)]
            for _ in range(self.__num_cols)
    ]
        self.__break_entrance_and_exit()
        self.__break_walls_r(0, 0)
        self.__reset_cells_visited()

    # Now that __cells[i][j] exists, we can draw each one
        for col in range(self.__num_cols):
            for row in range(self.__num_rows):
                self.__draw_cell(col, row)



    def __draw_cell(self, i, j):
        x1 = self.__x1 + i * self.__cell_size_x
        y1 = self.__y1 + j * self.__cell_size_y
        x2 = x1 + self.__cell_size_x
        y2 = y1 + self.__cell_size_y

        self.__cells[i][j].draw(x1, y1, x2, y2)
        self.__animate()

    def __animate(self):
        if self.__win is not None:
            self.__win.redraw()
            time.sleep(0.05)

    def __break_entrance_and_exit(self):
    # Entrance = top-left cell
        self.__cells[0][0].has_top_wall = False
        self.__draw_cell(0, 0)

    # Exit = bottom-right cell
        last_col = self.__num_cols - 1
        last_row = self.__num_rows - 1
        self.__cells[last_col][last_row].has_bottom_wall = False
        self.__draw_cell(last_col, last_row)

    def __break_walls_r(self, i, j):
        current = self.__cells[i][j]
        current.visited = True

        while True:
            neighbors = []

            # Up
            if j > 0 and not self.__cells[i][j - 1].visited:
                neighbors.append(("up", i, j - 1))
            # Down
            if j < self.__num_rows - 1 and not self.__cells[i][j + 1].visited:
                neighbors.append(("down", i, j + 1))
            # Left
            if i > 0 and not self.__cells[i - 1][j].visited:
                neighbors.append(("left", i - 1, j))
            # Right
            if i < self.__num_cols - 1 and not self.__cells[i + 1][j].visited:
                neighbors.append(("right", i + 1, j))

            if not neighbors:
                self.__draw_cell(i, j)
                return

            direction, ni, nj = random.choice(neighbors)
            neighbor = self.__cells[ni][nj]

            # Knock down the wall between current and neighbor
            if direction == "up":
                current.has_top_wall = False
                neighbor.has_bottom_wall = False
            elif direction == "down":
                current.has_bottom_wall = False
                neighbor.has_top_wall = False
            elif direction == "left":
                current.has_left_wall = False
                neighbor.has_right_wall = False
            elif direction == "right":
                current.has_right_wall = False
                neighbor.has_left_wall = False

            # Recursive call
            self.__break_walls_r(ni, nj)

    def __reset_cells_visited(self):
        for col in self.__cells:
            for cell in col:
                cell.visited = False

    def solve(self):
        return self.__solve_r(0, 0)

    def __solve_r(self, i, j):
        current = self.__cells[i][j]
        self.__animate()
        current.visited = True

        # Check if this is the end
        if i == self.__num_cols - 1 and j == self.__num_rows - 1:
            return True

        directions = [
            ("up", i, j - 1),
            ("down", i, j + 1),
            ("left", i - 1, j),
            ("right", i + 1, j)
        ]

        for direction, ni, nj in directions:
            # Check bounds
            if 0 <= ni < self.__num_cols and 0 <= nj < self.__num_rows:
                next_cell = self.__cells[ni][nj]

                # Check wall + visited status
                if not next_cell.visited:
                    if (
                        (direction == "up" and not current.has_top_wall) or
                        (direction == "down" and not current.has_bottom_wall) or
                        (direction == "left" and not current.has_left_wall) or
                        (direction == "right" and not current.has_right_wall)
                    ):
                        current.draw_move(next_cell)
                        if self.__solve_r(ni, nj):
                            return True
                        current.draw_move(next_cell, undo=True)

        return False

