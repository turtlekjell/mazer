import random
import time
from collections import deque

from cell import Cell


DIRECTIONS = (
    ("up", 0, -1),
    ("down", 0, 1),
    ("left", -1, 0),
    ("right", 1, 0),
)

OPPOSITE = {
    "up": "bottom",
    "down": "top",
    "left": "right",
    "right": "left",
}


class Maze:
    """Generate and solve a perfect maze on a rectangular grid or image mask.

    ``mask`` is row-major: mask[row][col] is truthy when that cell belongs to
    the maze. If omitted, every cell is active.
    """

    def __init__(
        self,
        x1,
        y1,
        num_rows,
        num_cols,
        cell_size_x,
        cell_size_y,
        win=None,
        seed=None,
        mask=None,
        animate_delay=0.0,
    ):
        if num_rows < 1 or num_cols < 1:
            raise ValueError("Maze must have at least one row and one column")

        self.__x1 = x1
        self.__y1 = y1
        self.__num_rows = num_rows
        self.__num_cols = num_cols
        self.__cell_size_x = cell_size_x
        self.__cell_size_y = cell_size_y
        self.__win = win
        self.__animate_delay = max(0.0, animate_delay)
        self.__rng = random.Random(seed)
        self.__mask = self._normalize_mask(mask)
        self.__cells = []
        self.__solution_path = []
        self.__start = None
        self.__end = None
        self.__start_opening = None
        self.__end_opening = None

        self.__create_cells()

    @property
    def num_rows(self):
        return self.__num_rows

    @property
    def num_cols(self):
        return self.__num_cols

    @property
    def cells(self):
        return self.__cells

    @property
    def start(self):
        return self.__start

    @property
    def end(self):
        return self.__end

    @property
    def start_opening(self):
        return self.__start_opening

    @property
    def end_opening(self):
        return self.__end_opening

    @property
    def solution_path(self):
        return list(self.__solution_path)

    def _normalize_mask(self, mask):
        if mask is None:
            return [[True for _ in range(self.__num_cols)] for _ in range(self.__num_rows)]

        if len(mask) != self.__num_rows or any(len(row) != self.__num_cols for row in mask):
            raise ValueError("Mask dimensions must match num_rows and num_cols")

        normalized = [[bool(value) for value in row] for row in mask]
        if not any(any(row) for row in normalized):
            raise ValueError("Mask contains no active cells")
        return normalized

    def __create_cells(self):
        self.__cells = [
            [Cell(self.__win, active=self.__mask[row][col]) for row in range(self.__num_rows)]
            for col in range(self.__num_cols)
        ]

        generation_start = self._first_active_cell()
        self.__break_walls(generation_start)
        self.__reset_cells_visited()

        if self._is_full_rectangle():
            self.__start = (0, 0)
            self.__end = (self.__num_cols - 1, self.__num_rows - 1)
            self.__start_opening = "top"
            self.__end_opening = "bottom"
        else:
            self.__start, self.__end = self._choose_mask_endpoints()
            self.__start_opening = self._outside_opening_for(*self.__start)
            self.__end_opening = self._outside_opening_for(*self.__end, avoid=self.__start_opening)
        self._open_wall(self.__start[0], self.__start[1], self.__start_opening)
        self._open_wall(self.__end[0], self.__end[1], self.__end_opening)

        for col in range(self.__num_cols):
            for row in range(self.__num_rows):
                self.__draw_cell(col, row)

    def _first_active_cell(self):
        for row in range(self.__num_rows):
            for col in range(self.__num_cols):
                if self.__mask[row][col]:
                    return col, row
        raise ValueError("Mask contains no active cells")

    def _is_full_rectangle(self):
        return all(all(row) for row in self.__mask)

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
            if self.__animate_delay:
                time.sleep(self.__animate_delay)

    def _active_neighbors(self, i, j):
        for direction, di, dj in DIRECTIONS:
            ni, nj = i + di, j + dj
            if 0 <= ni < self.__num_cols and 0 <= nj < self.__num_rows:
                if self.__cells[ni][nj].active:
                    yield direction, ni, nj

    def __break_walls(self, start):
        """Iterative randomized DFS maze generation.

        This is the same depth-first backtracking algorithm as the original
        project, but it avoids Python's recursion limit on large image masks.
        """
        start_col, start_row = start
        self.__cells[start_col][start_row].visited = True
        stack = [start]

        while stack:
            i, j = stack[-1]
            current = self.__cells[i][j]
            neighbors = [
                (direction, ni, nj)
                for direction, ni, nj in self._active_neighbors(i, j)
                if not self.__cells[ni][nj].visited
            ]

            if not neighbors:
                stack.pop()
                continue

            direction, ni, nj = self.__rng.choice(neighbors)
            neighbor = self.__cells[ni][nj]
            self._remove_wall_between(current, neighbor, direction)
            neighbor.visited = True
            stack.append((ni, nj))

    @staticmethod
    def _remove_wall_between(current, neighbor, direction):
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

    def _open_wall(self, i, j, side):
        cell = self.__cells[i][j]
        setattr(cell, f"has_{side}_wall", False)

    def __reset_cells_visited(self):
        for col in self.__cells:
            for cell in col:
                cell.visited = False

    def _boundary_cells(self):
        boundary = []
        for row in range(self.__num_rows):
            for col in range(self.__num_cols):
                if not self.__mask[row][col]:
                    continue
                for _, di, dj in DIRECTIONS:
                    ni, nj = col + di, row + dj
                    if not (0 <= ni < self.__num_cols and 0 <= nj < self.__num_rows) or not self.__mask[nj][ni]:
                        boundary.append((col, row))
                        break
        return boundary

    def _passage_neighbors(self, i, j):
        current = self.__cells[i][j]
        checks = (
            ("up", 0, -1, current.has_top_wall),
            ("down", 0, 1, current.has_bottom_wall),
            ("left", -1, 0, current.has_left_wall),
            ("right", 1, 0, current.has_right_wall),
        )
        for _, di, dj, has_wall in checks:
            ni, nj = i + di, j + dj
            if has_wall:
                continue
            if 0 <= ni < self.__num_cols and 0 <= nj < self.__num_rows and self.__cells[ni][nj].active:
                yield ni, nj

    def _distances_from(self, start):
        distances = {start: 0}
        queue = deque([start])
        while queue:
            current = queue.popleft()
            for neighbor in self._passage_neighbors(*current):
                if neighbor not in distances:
                    distances[neighbor] = distances[current] + 1
                    queue.append(neighbor)
        return distances

    def _choose_mask_endpoints(self):
        boundary = self._boundary_cells()
        if not boundary:
            only = self._first_active_cell()
            return only, only

        first = boundary[0]
        distances = self._distances_from(first)
        start = max(boundary, key=lambda p: distances.get(p, -1))
        distances = self._distances_from(start)
        end = max(boundary, key=lambda p: distances.get(p, -1))
        return start, end

    def _outside_opening_for(self, i, j, avoid=None):
        candidates = []
        side_defs = (
            ("top", 0, -1),
            ("right", 1, 0),
            ("bottom", 0, 1),
            ("left", -1, 0),
        )
        for side, di, dj in side_defs:
            ni, nj = i + di, j + dj
            outside = not (0 <= ni < self.__num_cols and 0 <= nj < self.__num_rows)
            inactive = not outside and not self.__mask[nj][ni]
            if outside or inactive:
                candidates.append(side)

        if not candidates:
            return "top"
        if avoid in candidates and len(candidates) > 1:
            candidates.remove(avoid)
        return candidates[0]

    def solve(self):
        """Solve the maze and retain the answer path.

        A stack-based DFS avoids recursion-depth failures on detailed masks.
        """
        self.__reset_cells_visited()
        self.__solution_path = []

        stack = [self.__start]
        parent = {self.__start: None}
        self.__cells[self.__start[0]][self.__start[1]].visited = True

        while stack:
            current_pos = stack.pop()
            if current_pos == self.__end:
                break

            i, j = current_pos
            for ni, nj in self._passage_neighbors(i, j):
                next_cell = self.__cells[ni][nj]
                if next_cell.visited:
                    continue
                next_cell.visited = True
                parent[(ni, nj)] = current_pos
                stack.append((ni, nj))
        else:
            return False

        path = []
        cursor = self.__end
        while cursor is not None:
            path.append(cursor)
            cursor = parent[cursor]
        path.reverse()
        self.__solution_path = path

        if self.__win is not None:
            for current_pos, next_pos in zip(path, path[1:]):
                current = self.__cells[current_pos[0]][current_pos[1]]
                next_cell = self.__cells[next_pos[0]][next_pos[1]]
                current.draw_move(next_cell)
                self.__animate()

        return True

    def wall_signature(self):
        """Stable representation useful for tests and reproducible seeds."""
        signature = []
        for row in range(self.__num_rows):
            for col in range(self.__num_cols):
                cell = self.__cells[col][row]
                signature.append((
                    cell.active,
                    cell.has_top_wall,
                    cell.has_right_wall,
                    cell.has_bottom_wall,
                    cell.has_left_wall,
                ))
        return tuple(signature)
