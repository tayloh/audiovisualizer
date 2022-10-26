import struct
import numpy
import matplotlib.pyplot as plt
import pyaudio

SAMPLE_SIZE = 1024 * 2 # samples taken per sample
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

fft_bins_before_mirror = int(SAMPLE_SIZE / 2)
fft_window = numpy.hanning(SAMPLE_SIZE)

fig, ax = plt.subplots(1, figsize=(15, 7))

x = numpy.linspace(0, SAMPLE_RATE / 2, fft_bins_before_mirror)
line, = ax.semilogx(x, numpy.random.rand(fft_bins_before_mirror), '-', lw=2)
ax.set_xlim(20, SAMPLE_RATE / 2)

ax.xaxis.label.set_color('white')
ax.yaxis.label.set_color('white')

plt.show(block=False)

while True:
    data_raw = stream.read(SAMPLE_SIZE)  
    data_int16 = numpy.array(struct.unpack(str(SAMPLE_SIZE) + "h", data_raw))

    data_int16_windowed = fft_window * data_int16

    data_fft = numpy.fft.rfft(data_int16_windowed)[1:]
    #print(len(data_fft))
    data_fft_magnitude = numpy.abs(data_fft)
    
    data_fft_magnitude_normalized = 2 * data_fft_magnitude / (SAMPLE_SIZE * 2**12)
    line.set_ydata(data_fft_magnitude_normalized)

    #data_fft_magnitude_log10 = numpy.log10(data_fft_magnitude)
    #line.set_ydata(data_fft_magnitude)
    
    fig.canvas.draw()
    fig.canvas.flush_events()