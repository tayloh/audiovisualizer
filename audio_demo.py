
import pyaudio
import wave
import sys
import struct
import matplotlib.pyplot as plt
import numpy
import time
import socket

# client stuff:
IP = "127.0.0.1"
PORT = 65432

tcpSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tcpSocket.connect((IP, PORT))

if len(sys.argv) < 2 or not sys.argv[1].endswith(".wav"):
    print("Plays a wave file.\n\nUsage: %s filename.wav" % sys.argv[0])
    sys.exit(-1)

wf = wave.open(sys.argv[1], 'rb')

# pyaudio for audio streaming
p = pyaudio.PyAudio()

# get values from wav header
CHUNK = 1024 * 2 # had to increase chunk size or it started to lag
FORMAT = p.get_format_from_width(wf.getsampwidth())
CHANNELS = wf.getnchannels()
SAMPLERATE = wf.getframerate()


# open a stream and set values that we got from wav header
stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=SAMPLERATE,
                output=True)


# visuals
fig, (ax, axFFT) = plt.subplots(2)

# fft stuff
xFFT = numpy.linspace(0, SAMPLERATE, CHUNK)
lineFFT, = axFFT.semilogx(xFFT, numpy.random.rand(CHUNK), "tab:purple")
axFFT.set_ylim(0, 1)
axFFT.set_xlim(20, SAMPLERATE/2)
axFFT.set_facecolor("k")

# just initiate the plot with CHUNK nr om random y values, will update in while loop
x = numpy.arange(0, 2*CHUNK, 2)
line, = ax.plot(x, numpy.random.rand(CHUNK), "g")
ax.set_ylim(-2**32, 2**32)
ax.set_xlim(0, CHUNK)
ax.set_facecolor("k")

fig.set_facecolor("k")
fig.show()

nameOfFile = sys.argv[1].split("/")[-1]
print(f"Playing: {nameOfFile}!")

timeStartPlaying = time.time()

# read data
# each frame contains 4 bytes of data (2 bytes per channel, since sample resolution is 16 bit)
# so we get 4 * CHUNK bytes
# frame:
#   samples:
#       channel1: 16 bits
#       channel2: 16 bits
# Size of frame is 32 bits or 4 bytes
data = wf.readframes(CHUNK)

unpack_errors = 0

# So, how many times does this loop run per second? 
# It gets 2048 frames per loop, so, I guess 44100 / 2048?
# Let's measure it... 
# Yup, that checked out.
# But... how do we know the loop won't run faster or slower than that?
loopCount = 0
# send data to audio stream
while len(data) > 0:

    # write frames to the audio stream to make sound
    stream.write(data)
    tcpSocket.sendall(data)
    # reads frames, maybe this one reads frames in the speed specified by samplerate?
    data = wf.readframes(CHUNK)

    # dataInt is an array of ints of size CHUNK!
    try:
        dataInt = struct.unpack(str(CHUNK) + "i", data)

        # amplitude graph
        line.set_ydata(dataInt)

        # fast fourier transform log graph
        lineFFT.set_ydata(numpy.abs(numpy.fft.fft(dataInt))*2 / (CHUNK * 2**32))
    except struct.error as e:
        unpack_errors += 1
        # print(f"({unpack_errors}) Could not unpack wav data: ", e)

    loopCount += 1
    fig.canvas.draw()
    fig.canvas.flush_events()

timeStopPlaying = time.time()
songLengthInSeconds = timeStopPlaying - timeStartPlaying

print("Writes per second:", loopCount / songLengthInSeconds)
print("Song ended!")

# close tcp socket
tcpSocket.close()

# close the audio stream
stream.stop_stream()
stream.close()

p.terminate()