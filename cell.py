from geometry import Point, Line


class Cell:
    def __init__(self, win=None, active=True):
        self.has_left_wall = True
        self.has_right_wall = True
        self.has_top_wall = True
        self.has_bottom_wall = True
        self.active = active

        self._x1 = -1
        self._y1 = -1
        self._x2 = -1
        self._y2 = -1
        self._win = win
        self.visited = False

    def draw(self, x1, y1, x2, y2, fill_color="black"):
        self._x1, self._y1 = x1, y1
        self._x2, self._y2 = x2, y2

        if self._win is None or not self.active:
            return

        if self.has_top_wall:
            self._win.draw_line(Line(Point(x1, y1), Point(x2, y1)), fill_color)
        if self.has_right_wall:
            self._win.draw_line(Line(Point(x2, y1), Point(x2, y2)), fill_color)
        if self.has_bottom_wall:
            self._win.draw_line(Line(Point(x1, y2), Point(x2, y2)), fill_color)
        if self.has_left_wall:
            self._win.draw_line(Line(Point(x1, y1), Point(x1, y2)), fill_color)

    def draw_move(self, to_cell, undo=False):
        if self._win is None:
            return

        color = "gray" if undo else "red"
        x1 = (self._x1 + self._x2) // 2
        y1 = (self._y1 + self._y2) // 2
        x2 = (to_cell._x1 + to_cell._x2) // 2
        y2 = (to_cell._y1 + to_cell._y2) // 2
        self._win.draw_line(Line(Point(x1, y1), Point(x2, y2)), color)
