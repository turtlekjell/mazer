from tkinter import Tk, BOTH, Canvas
from cell import Cell
from geometry import Point, Line
from maze import Maze

#remove
class Point:
    def __init__(self, x, y):
        self.x = x  # horizontal
        self.y = y  # vertical

#remove 
class Line:
    def __init__(self, point1, point2):
        self.point1 = point1
        self.point2 = point2

    def draw(self, canvas, fill_color):
        canvas.create_line(
            self.point1.x,
            self.point1.y,
            self.point2.x,
            self.point2.y,
            fill=fill_color,
            width=2
        )


class Window:
    def __init__(self, width, height):
        self.__root = Tk()
        self.__root.title("Maze Solver")
        self.__root.protocol("WM_DELETE_WINDOW", self.close)

        self.__canvas = Canvas(self.__root, width=width, height=height)
        self.__canvas.pack(fill=BOTH, expand=1)

        self.__running = False

    def redraw(self):
        self.__root.update_idletasks()
        self.__root.update()

    def wait_for_close(self):
        self.__running = True
        while self.__running:
            self.redraw()

    def close(self):
        self.__running = False

    def draw_line(self, line, fill_color):
        line.draw(self.__canvas, fill_color)


# MAIN
if __name__ == "__main__":
    num_cols = 16
    num_rows = 12
    cell_size = 50
    padding = 20

    width = num_cols * cell_size + padding
    height = num_rows * cell_size + padding

    win = Window(width, height)

    maze = Maze(
        x1=padding // 2,
        y1=padding // 2,
        num_rows=num_rows,
        num_cols=num_cols,
        cell_size_x=cell_size,
        cell_size_y=cell_size,
        win=win,
        seed=0
    )

    solved = maze.solve()
    print("Solved?" , solved)


    win.wait_for_close()
