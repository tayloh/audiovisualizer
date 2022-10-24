import tkinter as tk
import time
import random
import pyaudio
import wave
import struct
import numpy as np
import threading
import queue
import sys
import os

def rgb_to_hex(rgb):
    """Converts tuple (r, g, b) to corresponding hexadecimal string.
    """
    return "#%02x%02x%02x" % rgb 

def computeSignalEnergy(signal, mode="all"):
    if mode == "all":
        return sum(signal) / len(signal)
    if mode == "bass":
        # approx 0-100 Hz
        return sum(signal[2:6]) / len(signal[2:6])

def computeVariance(avg, data):
    denom = len(data) if len(data) > 0 else 1
    return sum([(x - avg)**2 for x in data]) / denom

def easingFunction(x):
    if x < 0.5:
        return 4*x**3
    else:
        return (x-1)*(2*x-2)**2 + 1

class NonBlockingAudioVisualizer:
    """
    Audio playback and visualizer on a separate thread.
    (Currently used specifically for my animation hence the very specific values 
    when appending data to the visualizer_data list, yes, this is bad design but I'm lazy).
    """

    # number of audio samples (frames) to read at once
    CHUNK_SIZE = 1024 * 2

    # number of frequencies represented by each datapoint from the FFT result
    # since the frequency band is 0-44100, magic number is how many
    # frequencies each band will have
    MAGIC_NUMBER = 44100 / CHUNK_SIZE 

    def __init__(self, frequency_blocks = [], bass_color = [150, 52, 181], treble_color = [181, 25, 28]):
        """Returns a NonBlockingAudioVisualizer object.
        """
        self.song_queue = queue.Queue()

        self.visualizer_thread = None
        self.visualizer_data = [] # dont acces this, it might be under construction
        self.visualizer_data_last = []

        self.energy_history_length = 32
        self.beat_mode = "bass"
        self.beat = 0
        self.beat_persistence = 60/160
        self.beat_std = 1.1
        self.time_last_beat = time.time()

        if not frequency_blocks:
            self.frequency_blocks = [
                20, 50, 100, 150, 250, 500, 1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 
                10000, 11000, 12000, 13000, 14000, 15000, 16000, 17000, 18000]
        else:
            self.frequency_blocks = frequency_blocks
        
        self.bar_count = len(self.frequency_blocks) - 1

        self.bar_colors = [
        [
        bass_color[0] + t*(treble_color[0]-bass_color[0]) / self.bar_count, 
        bass_color[1] + t*(treble_color[1]-bass_color[1]) / self.bar_count, 
        bass_color[2] + t*(treble_color[2]-bass_color[2]) / self.bar_count, 
        0.5
        ] 
        for t in range(self.bar_count)]

        self.is_playing = False
        self.skip = False
    
    def get_last_visualizer_data(self):
        """Returns the last computed visualization data.
        """
        return self.visualizer_data_last
    
    def get_beat(self):
        return self.beat

    def play_next(self):
        """Plays the next song in the queue and computes visualization.
        """
        
        if self.song_queue.empty():
            print("Queue is empty")
            return

        if self.is_playing:
            self.skip = True
            self.visualizer_thread.join()


        filepath = self.song_queue.get()
        print("Playing file", filepath)

        self.audio = pyaudio.PyAudio()
        self.wavefile = wave.open(filepath, "rb")

        self.format = self.audio.get_format_from_width(self.wavefile.getsampwidth())
        self.channels = self.wavefile.getnchannels()
        self.samplerate = self.wavefile.getframerate()

        self.stream = self.audio.open(
            format=self.format,
            channels=self.channels,
            rate=self.samplerate,
            output=True
        )

        self.skip = False
        self.visualizer_thread = threading.Thread(target=self._visualizer, daemon=True)
        self.visualizer_thread.start()

    def stop(self):
        """Stops the current song.
        """
        self.skip = True
    
    def empty_queue(self):
        """Empties the queue of songs.
        """
        while not self.song_queue.empty:
            temp = self.song_queue.get()

    def add_to_queue(self, filepath):
        """Adds a song to the queue (via relative file path).
        """
        self.song_queue.put(filepath)


    def _visualizer(self):
        """Internal method. Does audio playback and computes audio visualization data.
        """
        magic = NonBlockingAudioVisualizer.MAGIC_NUMBER
        self.is_playing = True

        chunk_size = NonBlockingAudioVisualizer.CHUNK_SIZE
        audio_data = self.wavefile.readframes(chunk_size)
        block_memory = [[] for x in range(self.bar_count)]

        E_history = np.zeros(self.energy_history_length)

        while len(audio_data) > 0 and not self.skip:
            self.stream.write(audio_data)
            audio_data = self.wavefile.readframes(chunk_size)
            try:
                dataInt = struct.unpack(str(chunk_size) + "i", audio_data)
            except struct.error:
                print("unpack error")
            
            data_fft = np.abs(np.fft.fft(dataInt))*2.7 / (chunk_size * 2**32)

            fftBlocks = []

            for i in range(len(block_memory)):
                if len(block_memory[i]) == 2:
                    block_memory[i] = block_memory[i][1:]

            for i in range(1, len(self.frequency_blocks)):
                p = int(self.frequency_blocks[i-1] / magic + 0.5)
                k = int(self.frequency_blocks[i] / magic + 0.5)
                block_memory[i-1].append(sum(data_fft[p:k]))

            for i in range(self.bar_count):
                avg = 0
                if len(block_memory[i]) == 2:
                    avg = block_memory[i][0] * 0.65 + block_memory[i][1] * 0.35
                else: 
                    avg = sum(block_memory[i]) / len(block_memory[i])
                fftBlocks.append(avg)
            
            for bar, i in zip(fftBlocks, range(self.bar_count)):
                color = (int(self.bar_colors[i][0]), int(self.bar_colors[i][1]), int(self.bar_colors[i][2]))
                self.visualizer_data.append(
                    ( 
                150 + i*900/self.bar_count, 720/2 + 45, 
                150 + i*900/self.bar_count+900/self.bar_count, 720/2 + 45 - bar*720/4,
                rgb_to_hex(color)
                    )
                )
            self.visualizer_data_last = self.visualizer_data
            self.visualizer_data = []


            # Beat detection
            E = computeSignalEnergy(data_fft, mode=self.beat_mode)
            E_history = np.roll(E_history, 1)
            E_history[0] = E
            E_history_no_zeros = E_history[E_history != 0]
            avg = np.average(E_history_no_zeros)
            variance = computeVariance(avg, E_history_no_zeros)
            std = np.sqrt(variance)
            threshold = -12*std + 1.55
            threshold = max(threshold, 1.1)
            cond_persistence = (time.time() - self.time_last_beat) >= self.beat_persistence
            cond1 = E > avg + self.beat_std*std 
            cond3 = cond3 = E > threshold * avg 
            if cond1 and cond_persistence:
                self.beat = 1
                self.time_last_beat = time.time()
            elif (time.time() - self.time_last_beat) < self.beat_persistence:
                self.beat = easingFunction(1 - (time.time() - self.time_last_beat) / self.beat_persistence)
            else:
                self.beat = 0
            
        
        self.is_playing = False
    
        
class Line3D:
    """
    Represents a 3D line.
    """

    def __init__(self, x0, x1, y0, y1, z0, z1) -> None:
        self.x0 = x0
        self.x1 = x1

        self.y0 = y0
        self.y1 = y1

        self.z0 = z0
        self.z1 = z1
    
    def get_projected_coordinates(self, focal_dist, canvas_dims):
        """Gets the projected coordinates of the 3D line onto the 2D canvas.
        Using perspective(?) projection.
        """
        width = canvas_dims[0]
        height = canvas_dims[1]

        x0_proj = focal_dist*(self.x0 / self.z0) + (width / 2)
        x1_proj = focal_dist*(self.x1 / self.z1) + (width / 2)
        y0_proj = focal_dist*(self.y0 / self.z0) + (height / 2)   
        y1_proj = focal_dist*(self.y1 / self.z1) + (height / 2)   

        return x0_proj, x1_proj, y0_proj, y1_proj


### I am too lazy to modularize this part right now ###
### Animation script ###

# Init random
SEED = 123
random.seed(SEED)

# Canvas dimensions
WIDTH = 1200
HEIGHT = 720

# Camera proporties
CAMERA = (0, 40, 0) # x=0, y=40, z=0 are default 
FOCAL_DISTANCE = HEIGHT / 2

# Line positions
LINE_XPOS1 = -WIDTH/2
LINE_XPOS2 = WIDTH/2
LINE_YPOS = CAMERA[1]
LINE_ZPOS = 300 # starting position for horizontal lines
Z_SPEED_PER_SECOND = 80

# need to make sure there are no "double lines" at certain intervals
# not really sure what's causing them, Answer: it was floating point precision ;_;

NUM_VERT_LINES = 40
NUM_HORIZ_LINES = 20
NUM_STARS = 20
HORIZ_LINE_ZSPACING = LINE_ZPOS / NUM_HORIZ_LINES

SUN_RADIUS = 110
SUN_WIDTH = 10

# Animation stuff
animation_speed = 1000
is_start = True # very hacky way to do this but w/e
t = 0
running = True
dt = 0.01 # time difference between frames, initial value

# Draw lists
horizontal_lines = []
stars = []
vertical_lines = []

# Init all line objects that we are going to need
back_line = Line3D(LINE_XPOS1, LINE_XPOS2, LINE_YPOS, LINE_YPOS, LINE_ZPOS, LINE_ZPOS)

# Horizontal lines
for i in range(NUM_HORIZ_LINES):
    starting_zpos = LINE_ZPOS - i*HORIZ_LINE_ZSPACING

    horizontal_lines.append(Line3D(LINE_XPOS1, LINE_XPOS2, 
        LINE_YPOS, LINE_YPOS, 
        starting_zpos , starting_zpos))

# Stars
for i in range(NUM_STARS):
    stars.append((random.randint(0, WIDTH), random.randint(0, HEIGHT/2)))

# Vertical lines
for i in range(NUM_VERT_LINES):
    x_pos = -WIDTH/2 + i*(WIDTH/NUM_VERT_LINES)
    vert_line = Line3D(x_pos, x_pos, LINE_YPOS, LINE_YPOS, 1, LINE_ZPOS)
    vertical_lines.append(vert_line)

# Gradient calculation
gradient_rects = []
purple = [70, 0, 90]
black = [8, 0, 0]
num_gradient = 16
offset = 45
for i in range(num_gradient):
    color = [0, 0, 0]
    color[0] = purple[0] + i*(black[0] - purple[0])/(num_gradient - 1)
    color[1] = purple[1] + i*(black[1] - purple[1])/(num_gradient - 1)
    color[2] = purple[2] + i*(black[2] - purple[2])/(num_gradient - 1)
    r, g, b = int(color[0]), int(color[1]), int(color[2])
    y0 = HEIGHT/2 + offset + i*((HEIGHT/2 - offset)/num_gradient)
    y1 = y0 + (HEIGHT/2 - offset)/num_gradient
    hex_val = rgb_to_hex((r, g, b))
    gradient_rects.append((0, y0, WIDTH, y1, hex_val))

# Create the audio visualizer
# freq = [60, 120, 250, 500, 750, 1000, 2000, 3000, 4000, 5000, 6000, 18000]
# freq = [20, 100, 150, 250, 400, 600, 800, 1000]
#freqs = [20, 100, 250, 500, 1000, 2000, 4000, 8000, 16000]#, 6000, 7000, 8000, 9000, 
                #10000, 11000, 15000, 20000]
#freqs = [30, 70, 170, 310, 600, 1000, 3000, 6000, 12000, 14000, 16000] winamp
#freqs = [0, 60*1, 60*2, 60*4, 60*8, 60*16, 60*32, 60*64, 60*128, 60*256]
#audio_visualizer = NonBlockingAudioVisualizer(frequency_blocks=freqs)
audio_visualizer = NonBlockingAudioVisualizer()

# Check music directory
if len(sys.argv) < 2:
    print("Usage: %s relative-path-to-directory-with-wav-files" % sys.argv[0])
    sys.exit(-1)


def addSongsInDirAndPlay():
    """If queue is empty, adds all files from the music directory
    and plays first file.
    If queue is not empty, plays next file.
    """
    if audio_visualizer.song_queue.empty():
        relative_path = sys.argv[1] if sys.argv[1].endswith("/") else sys.argv[1] + "/"

        for file in os.listdir(relative_path):
            if file.split(".")[-1] == "wav":
                audio_visualizer.add_to_queue(relative_path + file)
    
    audio_visualizer.play_next()

addSongsInDirAndPlay()

# tk stuff
def on_click(event):
    """When clicking the canvas.
    """
    addSongsInDirAndPlay()

def on_closing():
    """When closing the tk window.
    """
    global running
    running = False

def on_resize(event):
    """When resizing the window.
    """
    width, height = event.width, event.height
    # TODO scale the animation, need to make it more modular for this
    global WIDTH, HEIGHT
    WIDTH = width
    HEIGHT = height

# Init tk
root = tk.Tk()
root.protocol("WM_DELETE_WINDOW", on_closing)
canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, bg="#120008")
canvas.bind("<Button-1>", on_click)
canvas.pack(fill="both", expand=True)
#canvas.bind("<Configure>", on_resize)

absolute_starting_time = time.time()

def lerp(t, p0, p1):
    p = [0, 0, 0]
    p[0] = (1-t)*p0[0] + t*p1[0]
    p[1] = (1-t)*p0[1] + t*p1[1]
    p[2] = (1-t)*p0[2] + t*p1[2]
    return (int(p[0]), int(p[1]), int(p[2]))


# Draw loop
while running:
    start = time.time()
    # Uncomment to check if the lines are uniformly spread
    # for a in range(1, NUM_HORIZ_LINES):
    #     if abs(horizontal_lines[a-1].z0 - horizontal_lines[a].z0) > 0.01 + HORIZ_LINE_ZSPACING or abs(horizontal_lines[a-1].z0 - horizontal_lines[a].z0) < HORIZ_LINE_ZSPACING - 0.01:
    #         print("not uniform", abs(horizontal_lines[a-1].z0 - horizontal_lines[a].z0))

    # TODO should not do this if im concerned with performance?
    canvas.delete("all")

    beat_color_stop0 = [18, 0, 8]
    beat_color_stop1 = [130/5, 4, 38] if random.random() < 0.5 else [181/5, 25/5, 28/5]
    canvas.configure(background=rgb_to_hex(lerp(audio_visualizer.get_beat(), beat_color_stop0, beat_color_stop1)))

    # Draw flickering stars
    for x, y in stars:
        size = random.randint(1, 2)
        color = "#DDDDDD"
        # beat = audio_visualizer.get_beat()
        # if beat:
        #     size = 2 + beat * 2 

        canvas.create_oval(x-size, y-size, x+size, y+size, fill=color)
    
    # Draw the sun
    # sun_size = SUN_RADIUS + audio_visualizer.get_beat() * SUN_RADIUS * 0.1
    # canvas.create_oval(WIDTH/2 - sun_size, (HEIGHT-300)/2 - sun_size,
    # WIDTH/2 + sun_size, (HEIGHT-300)/2 + sun_size, fill=rgb_to_hex((181, 25, 28)))
    canvas.create_oval(WIDTH/2 - SUN_RADIUS, (HEIGHT-300)/2 - SUN_RADIUS,
    WIDTH/2 + SUN_RADIUS, (HEIGHT-300)/2 + SUN_RADIUS, fill=rgb_to_hex((181, 25, 28)))

    # Draw the gradient background
    for rect in gradient_rects:
        x0, y0, x1, y1, color = rect[0], rect[1], rect[2], rect[3], rect[4]
        canvas.create_rectangle(x0, y0, x1, y1, fill=color, outline=color)

    # Draw vertical lines
    for line in vertical_lines:
        x0, x1, y0, y1 = line.get_projected_coordinates(FOCAL_DISTANCE, (WIDTH, HEIGHT))
        canvas.create_line(x0, y0, x1, y1, width=3, fill="magenta")
    
    # Draw one horizontal line at the back to counter the bumping
    x0, x1, y0, y1 = back_line.get_projected_coordinates(FOCAL_DISTANCE, (WIDTH, HEIGHT))
    canvas.create_line(x0, y0, x1, y1, width=3, fill="magenta")

    # Draw the horizontal lines and have them move along the z-axis
    for line in horizontal_lines:
        x0, x1, y0, y1 = line.get_projected_coordinates(FOCAL_DISTANCE, (WIDTH, HEIGHT))
        canvas.create_line(x0, y0, x1, y1, width=3, fill="magenta")
        
        # Have their speed be dependent on how fast this is being run
        # Turns out this is unstable because of floating point precision
        # Not found a way to fix this so just gonna run with -1 and sleep
        # line.z0 = line.z0 - Z_SPEED_PER_SECOND * dt
        # line.z1 = line.z1 - Z_SPEED_PER_SECOND * dt
        line.z0 -= 1
        line.z1 -= 1
        if line.z0 <= 0:
            # Reset the lines z position
            line.z0 = LINE_ZPOS
            line.z1 = LINE_ZPOS

    # Draw the visualizer data
    visualizer_rects = audio_visualizer.get_last_visualizer_data()

    for x0, y0, x1, y1, color in visualizer_rects:
        canvas.create_rectangle(x0, y0+1, x1, y1+1, fill=color, outline=color)
    
    # Update and measure frame time
    canvas.update()
    
    time.sleep(1/1000)
    
    end = time.time()
    dt = end - start
