import struct
import numpy
import matplotlib.pyplot as plt
import pyaudio

SAMPLE_SIZE = 1024 # samples taken per sample
FORMAT = pyaudio.paInt16 # per channel size (one channel is 16 bit)
CHANNELS = 1
SAMPLE_RATE = 44100 # samples per second: 44100 / 1024 ~ 23ms per sample => 43 fps

audio = pyaudio.PyAudio()

stream = audio.open(
    format=FORMAT,
    channels=CHANNELS,
    rate=SAMPLE_RATE,
    input=True,
    output=True,
    frames_per_buffer=SAMPLE_SIZE
)


# data_raw = stream.read(SAMPLE_SIZE)

# data_int16 = struct.unpack(str(SAMPLE_SIZE)+"h", data_raw)

# print(pyaudio.paInt8) # 16
# print(pyaudio.paInt16) # 8
# print(pyaudio.paInt24) # 4
# print(pyaudio.paInt32) # 2
# print(audio.get_format_from_width(2)) # 8

#print(data_raw)
#print(data_int16)

fig, ax = plt.subplots(1, figsize=(12, 6))

# variable for plotting
x = numpy.arange(0, SAMPLE_SIZE)

# create a line object with random data
line, = ax.plot(x, numpy.random.rand(SAMPLE_SIZE), "-r", lw=2)
ax.set_title('Waveform (Amplitude vs. Sample)')
ax.set_xlabel('Sample (%s / 23ms)' % SAMPLE_SIZE)
ax.set_ylabel('Amplitude (16 bit)')
ax.set_ylim(-2**14, 2**14)
ax.set_xlim(0, SAMPLE_SIZE)
ax.set_facecolor("k")

ax.xaxis.label.set_color('white')
ax.yaxis.label.set_color('white')

fig.set_facecolor("k")

plt.show(block=False)

y_max = 2**10

fft_window = numpy.hanning(SAMPLE_SIZE)

while True:
    data_raw = stream.read(SAMPLE_SIZE)  
    data_int16 = numpy.array(struct.unpack(str(SAMPLE_SIZE) + "h", data_raw))

    data_int16_windowed = fft_window * data_int16

    y_max = max(y_max, max(data_int16_windowed))
    ax.set_ylim(-y_max, y_max)
    line.set_ydata(data_int16_windowed)
    
    fig.canvas.draw()
    fig.canvas.flush_events()

