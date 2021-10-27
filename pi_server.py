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

BAR_COUNT = 22
bars = axBars.bar(range(BAR_COUNT), np.random.rand(BAR_COUNT))
axBars.set_ylim(0, 1)
axBars.set_facecolor("k")
blockMemory = [[] for x in range(BAR_COUNT)]

# Frequency ranges
blocks = [20, 50, 125, 250, 500, 1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 
                        10000, 11000, 12000, 13000, 14000, 15000, 16000, 17000, 18000]

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
tcpSocket.settimeout(100) # seconds
print("Listening on:", (IP, PORT))

while True:
    connection, sourceAddr = tcpSocket.accept()

    print("Connection from:", sourceAddr)

    while True:
        data = connection.recv(BUFFER_SIZE)
        if not data:
            break
        try:
            dataInt = struct.unpack(str(CHUNK) + "i", data) # CHUNK number of ints = 3072

            # amplitude graph
            line.set_ydata(dataInt)

            # fast fourier transform log graph
            dataFFT = np.abs(np.fft.fft(dataInt))*2 / (CHUNK * 2**32) # CHUNK in length

            # Each value dataFFT[i] corresponds to 44100/3072 samples
            # I only want to use i=1-1393, the rest of the values are >20kHz

            fftBlocks = []

            # Smooth out the transitions on the bars by remembering previous values
            for i in range(len(blockMemory)):
                if len(blockMemory[i]) == 2:
                    blockMemory[i] = blockMemory[i][1:]
            
            for i in range(1, len(blocks)):
                p = int(blocks[i-1] // 14.36)
                k = int(blocks[i] // 14.36)
                blockMemory[i-1].append(sum(dataFFT[p:k]))

            # dataFFT[0] = 0-14.36 Hz
            # dataFFT[1] = 14.36-28.72 Hz
            # dataFFT[2] = 28.72-43.08 Hz
            # + 14.36 always...
            
            for i in range(BAR_COUNT):
                avg = sum(blockMemory[i]) / len(blockMemory[i])
                fftBlocks.append(avg)

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