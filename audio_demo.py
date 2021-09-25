
import pyaudio
import wave
import sys
import struct
import matplotlib.pyplot as plt
import numpy

if len(sys.argv) < 2:
    print("Plays a wave file.\n\nUsage: %s filename.wav" % sys.argv[0])
    sys.exit(-1)

wf = wave.open(sys.argv[1], 'rb')

# instantiate PyAudio (1)
p = pyaudio.PyAudio()


CHUNK = 1024 * 2 # had to increase chunk size or it started to lag
FORMAT = p.get_format_from_width(wf.getsampwidth())
CHANNELS = wf.getnchannels()
SAMPLERATE = wf.getframerate()


# open stream (2)
stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=SAMPLERATE,
                output=True)



fig, (ax, axFFT) = plt.subplots(2)
x = numpy.arange(0, 2*CHUNK, 2)

# fft stuff
xFFT = numpy.linspace(0, SAMPLERATE, CHUNK)
lineFFT, = axFFT.semilogx(xFFT, numpy.random.rand(CHUNK), "tab:purple")
axFFT.set_ylim(0, 1)
axFFT.set_xlim(20, SAMPLERATE/2)
axFFT.set_facecolor("k")

# just initiate the plot with CHUNK nr om random y values, will update in while loop
line, = ax.plot(x, numpy.random.rand(CHUNK), "g")
ax.set_ylim(-2**32, 2**32)
ax.set_xlim(0, CHUNK)
ax.set_facecolor("k")

fig.set_facecolor("k")
fig.show()

# read data
data = wf.readframes(CHUNK)

# play stream (3)
# prevent it from crashing when song ends.. or not
while len(data) > CHUNK:
    stream.write(data)
    data = wf.readframes(CHUNK)
    dataInt = struct.unpack(str(CHUNK) + "i", data)

    # dataInt is an array of ints!
    line.set_ydata(dataInt)
    lineFFT.set_ydata(numpy.abs(numpy.fft.fft(dataInt))*2 / (CHUNK * 2**32))
    fig.canvas.draw()
    fig.canvas.flush_events()

# stop stream (4)
stream.stop_stream()
stream.close()

# close PyAudio (5)
p.terminate()