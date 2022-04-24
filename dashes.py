import time
import tkinter as tk
import random

class DashController:

    def __init__(self, num_dashes, colors, movemodel, tkCanvas) -> None:
        self.num_dashes = num_dashes
        self.colors = colors
        self.movemodel = movemodel
        self.tkCanvas = tkCanvas
        self.draw_buffer = []
        self.create_dashes()

    def create_dashes(self):
        for n in range(self.num_dashes):
            x = -1920
            y = (1080 / self.num_dashes) * n
            width = 1920/2
            height = 1080 / self.num_dashes
            color = self.colors[random.randint(0, len(self.colors)-1)]
            speed = random.randint(5, 10)
            dash = Dash(x, y, width, height, color, speed)
            self.draw_buffer.append(dash)

            x2 = 0
            y2 = (1080 / self.num_dashes) * n
            width = 1920/2
            height = 1080 / self.num_dashes
            color = self.colors[random.randint(0, len(self.colors)-1)]
            dash = Dash(x2, y2, width, height, color, speed)
            self.draw_buffer.append(dash)

    def update(self):
        for n in range(len(self.draw_buffer)):

            if self.draw_buffer[n].x > 1920:
                color = self.colors[random.randint(0, len(self.colors)-1)]
                self.draw_buffer[n].change_color(color)

            self.draw_buffer[n].move(self.movemodel)

    def draw(self):
        self.tkCanvas.delete("all")

        for dash in self.draw_buffer:
            self.tkCanvas.create_rectangle(
                dash.x, dash.y, 
                dash.x + dash.width, dash.y + dash.height, 
                fill=dash.color, 
                outline=dash.color)
        
        self.tkCanvas.update()
    
         

class Dash:

    def __init__(self, x, y, width, height, color, speed) -> None:
        self.width = width
        self.height = height
        self.color = color
        self.x = x
        self.y = y
        self.speed = speed

    def move(self, movemodel):
        self.x = movemodel(self.x, self.speed)

    def change_color(self, color):
        self.color = color




running = True

def on_closing():
    global running
    running = False

def on_closing_wrapper(event):
    on_closing()

root = tk.Tk()
root.attributes("-fullscreen", True)
root.protocol("WM_DELETE_WINDOW", on_closing)
canvas = tk.Canvas(root, width=1920, height=1080, bg="#000000")
canvas.bind("<Button-1>", on_closing_wrapper)
canvas.pack(fill="both", expand=True)

def scale_between(x, x_min, x_max, a, b):
    return (b-a) * (x - x_min)/(x_max - x_min) + a

def movemodel(x, speed):
    if x > 1920:
        x = -1920
    
    min_x = 200
    max_x = 400

    abs_x = abs(x)

    #scaled_x = scale_between(abs_x, 10, 1920, min_x, max_x)
    scaled_x = abs_x

    speedx = 1.05*(scaled_x/10) + speed

    x += speedx

    return x

colors = ["#800080", "#20b2aa", "#ff6666", "#088da5", "#3399ff", "#cc0000"]
colors2 = ["#003300", "#00FF00"]
controller = DashController(20, colors2, movemodel, canvas)

while running:

    controller.draw()
    controller.update()
    
    time.sleep(0.01)
