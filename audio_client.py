# Takes a music file, plays it, does the fft and amplitude calculations. 
# Sends the results to the pi server.

import sys
import os
import time
import socket
import pyaudio
import wave

############ Check user input ############
if len(sys.argv) < 2:
    print("Plays a wave file.\n\nUsage: %s filename.wav" % sys.argv[0])
    sys.exit(-1)

# find music file in specific folder (only for me right now)
fileToPlay = ""

musicDirectoryRelative = "../files"

# if / then assume exact path
if sys.argv[1].find("/") != -1 and sys.argv[1].endswith(".wav"):
    fileToPlay = sys.argv[1]

# else, look for the song file in the music folder
else:
    for file in os.listdir(musicDirectoryRelative):
        if file.endswith(".wav") and file.find(sys.argv[1]) != -1:
            fileToPlay = musicDirectoryRelative + "/" + file

try:
    wf = wave.open(fileToPlay, 'rb')
except FileNotFoundError:
    print("File not found.")
    sys.exit(-1)
############ Check user input ############

############ Sender ############
IP = "127.0.0.1"
PORT = 65432

attempts = 10
tcpSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

while attempts:
    try:
        print(f"({10-attempts}) Attempting to connect...")
        tcpSocket.connect((IP, PORT))
        break
    except ConnectionRefusedError:
        attempts -= 1
        time.sleep(2)
############ Sender ############

############ Play audio and stream data to pi ############
# pyaudio for audio streaming
p = pyaudio.PyAudio()

# get values from wav header
CHUNK = 3 * 1024 # (2* 1024) had to increase chunk size or it started to lag
FORMAT = p.get_format_from_width(wf.getsampwidth())
CHANNELS = wf.getnchannels()
SAMPLERATE = wf.getframerate()


# open a stream and set values that we got from wav header
stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=SAMPLERATE,
                output=True)


nameOfFile = fileToPlay.split("/")[-1]
print(f"Playing: {nameOfFile}!")


# read data
# each frame contains 4 bytes of data (2 bytes per channel, since sample resolution is 16 bit)
# so we get 4 * CHUNK bytes
# frame:
#   samples:
#       channel1: 16 bits
#       channel2: 16 bits
# Size of frame is 32 bits or 4 bytes
data = wf.readframes(CHUNK)

# So, how many times does this loop run per second? 
# It gets 2048 frames per loop, so, I guess 44100 / 2048?
# Let's measure it... 
# Yup, that checked out.
# But... how do we know the loop won't run faster or slower than that?

try:
    # send data to audio stream
    while len(data) > 0:

        # send the data before playing it...
        tcpSocket.sendall(data)

        # wait for a response before playing the data - hacky solution?
        #tcpSocket.recv(256)

        # write frames to the audio stream to make sound
        stream.write(data)

        # reads frames, maybe this one reads frames in the speed specified by samplerate?
        data = wf.readframes(CHUNK)

except KeyboardInterrupt:
    print("Stopped playing...")

except:
    print("Server exited...")

############ Play audio and stream data to pi ############

############ Shutdown ############
print("Song ended!")

# close tcp socket
tcpSocket.close()

# close the audio stream
stream.stop_stream()
stream.close()

p.terminate()

############ Shutdown ############

