# Takes visualization data from the audio_client and displays it on leds.

import socket
import struct
import numpy as np
import matplotlib.pyplot as plt

CHUNK = 3 * 1024 # this had to be fine tuned to work with: gui update delay - stream delay - music playing

############ Visuals ############ (temp, TODO: led strip)
fig, (ax, axFFT, axBars) = plt.subplots(3)

# should not need to hardcode this mby
SAMPLERATE = 44100

# fft stuff
xFFT = np.linspace(0, SAMPLERATE, CHUNK)
lineFFT, = axFFT.semilogx(xFFT, np.random.rand(CHUNK), "tab:purple")
axFFT.set_ylim(0, 1)
axFFT.set_xlim(20, SAMPLERATE/2)
axFFT.set_facecolor("k")

# just initiate the plot with CHUNK nr on random y values, will update in while loop later
x = np.arange(0, 2*CHUNK, 2)
line, = ax.plot(x, np.random.rand(CHUNK), "g")
ax.set_ylim(-2**32/2, 2**32/2)
ax.set_xlim(0, CHUNK)
ax.set_facecolor("k")

bars = axBars.bar(range(60), np.random.rand(60))

fig.set_facecolor("k")
fig.show()
fig.canvas.draw()
fig.canvas.flush_events()
############ Visuals ############

############ Listener ############
IP = "127.0.0.1"
PORT = 65432
BUFFER_SIZE = CHUNK * 4 # size of each chunk of audioframes in bytes

tcpSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tcpSocket.bind((IP, PORT))

tcpSocket.listen()
tcpSocket.settimeout(10) # seconds
print("Listening on:", (IP, PORT))

while True:
    connection, sourceAddr = tcpSocket.accept()

    print("Connection from:", sourceAddr)

    while True:
        data = connection.recv(BUFFER_SIZE)
        if not data:
            break
        try:
            dataInt = struct.unpack(str(CHUNK) + "i", data)
            #connection.send(b"any")

            # amplitude graph
            line.set_ydata(dataInt)

            # fast fourier transform log graph
            dataFFT = np.abs(np.fft.fft(dataInt))*2 / (CHUNK * 2**32) # CHUNK in length

            # TODO: Try to divide the fft data into 60 blocks depending on frequency range
            #       and use a bar diagram to simulate the led strip
            #       3072 / 60 = 51.2 fft values per bar (average)
            # TODO: no, this doesn't work because the first 50 values are like the first 80% of the spectrum
            #       so the first bar is always going to be super high
            #       this needs to be custom, or have som log increase thingy
            fftBlocks = [sum(dataFFT[x*51:(x+1)*51]) for x in range(60)]

            for bar, block in zip(bars, fftBlocks):
                bar.set_height(block)

            lineFFT.set_ydata(dataFFT)

        except struct.error:
            print("Unpack error.")
    
        fig.canvas.draw()
        fig.canvas.flush_events()

    connection.close()

tcpSocket.close()

############ Listener ############