from geometry import Point, Line

class Cell:
    def __init__(self, win=None):
        self.has_left_wall = True
        self.has_right_wall = True
        self.has_top_wall = True
        self.has_bottom_wall = True

        self.__x1 = -1
        self.__y1 = -1
        self.__x2 = -1
        self.__y2 = -1

        self.__win = win

        self.visited = False


    def draw(self, x1, y1, x2, y2, fill_color="black"):
        self.__x1, self.__y1 = x1, y1
        self.__x2, self.__y2 = x2, y2

        if self.__win is None:
            return

        # Draw each wall based on presence
        if self.has_top_wall:
            self.__win.draw_line(Line(Point(x1, y1), Point(x2, y1)), fill_color)
        else:
            self.__win.draw_line(Line(Point(x1, y1), Point(x2, y1)), "#d9d9d9")

        if self.has_right_wall:
            self.__win.draw_line(Line(Point(x2, y1), Point(x2, y2)), fill_color)
        else:
            self.__win.draw_line(Line(Point(x2, y1), Point(x2, y2)), "#d9d9d9")

        if self.has_bottom_wall:
            self.__win.draw_line(Line(Point(x1, y2), Point(x2, y2)), fill_color)
        else:
            self.__win.draw_line(Line(Point(x1, y2), Point(x2, y2)), "#d9d9d9")

        if self.has_left_wall:
            self.__win.draw_line(Line(Point(x1, y1), Point(x1, y2)), fill_color)
        else:
            self.__win.draw_line(Line(Point(x1, y1), Point(x1, y2)), "#d9d9d9")

    def draw_move(self, to_cell, undo=False):
        if self.__win is None:
            return
        
        color = "gray" if undo else "red"

        x1 = (self.__x1 + self.__x2) // 2
        y1 = (self.__y1 + self.__y2) // 2
        x2 = (to_cell.__x1 + to_cell.__x2) // 2
        y2 = (to_cell.__y1 + to_cell.__y2) // 2

        self.__win.draw_line(Line(Point(x1, y1), Point(x2, y2)), color)
