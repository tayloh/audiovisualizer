import struct
import numpy
import matplotlib.pyplot as plt
import pyaudio
import wave
import sys
import os

# http://hyperphysics.phy-astr.gsu.edu/hbase/Audio/equal.html

def openWavfileFromArgs():
    if len(sys.argv) < 2:
        print("Plays a wave file.\n\nUsage: %s filename.wav" % sys.argv[0])
        sys.exit(-1)

    # find music file in specific folder (only for me right now)
    fileToPlay = ""

    musicDirectoryRelative = "../../files"

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
    
    return wf


wf = openWavfileFromArgs()

audio = pyaudio.PyAudio()

# SAMPLE_SIZE = 1024 * 2 # samples taken per sample
# FORMAT = pyaudio.paInt16 # per channel size (one channel is 16 bit)
# CHANNELS = 1
# SAMPLE_RATE = 44100 # samples per second: 44100 / 1024 ~ 23ms per sample => 43 fps

SAMPLE_SIZE = 1024 * 2
FORMAT = audio.get_format_from_width(wf.getsampwidth())
CHANNELS = wf.getnchannels()
SAMPLE_RATE = wf.getframerate()

stream = audio.open(
    format=FORMAT,
    channels=CHANNELS,
    rate=SAMPLE_RATE,
    output=True,
)

fft_bins_before_mirror = int(SAMPLE_SIZE / 2)
fft_window = numpy.hanning(SAMPLE_SIZE)


fft_rect_bin_indices = []
fft_rect_bin_avg = []

fig, ax = plt.subplots(1, figsize=(15, 7))

x = numpy.linspace(0, SAMPLE_RATE / 2, fft_bins_before_mirror)
#line, = ax.semilogx(x, numpy.random.rand(fft_bins_before_mirror), '-', lw=2, basex=10)
line, = ax.semilogx(x, numpy.random.rand(fft_bins_before_mirror), '-', lw=2, basex=2)
ax.set_xlim(20, 10240)
#ax.set_xlim(20, 16000) # SAMPLE_RATE / 2
ax.set_facecolor("k")
#fig.set_facecolor("k")

plt.show(block=False)

while True:
    #data_raw = stream.read(SAMPLE_SIZE)  
    data_raw = wf.readframes(SAMPLE_SIZE)
    stream.write(data_raw)

    data_int16 = numpy.array(struct.unpack(str(SAMPLE_SIZE) + "i", data_raw))

    data_int16_windowed = fft_window * data_int16

    data_fft = numpy.fft.rfft(data_int16_windowed)[1:]
    #print(len(data_fft))
    data_fft_magnitude = numpy.abs(data_fft)

    data_fft_magnitude_normalized = 2 * data_fft_magnitude / (SAMPLE_SIZE * 2**30)
    # line.set_ydata(data_fft_magnitude_normalized)

    log2test = numpy.logspace(0, numpy.log2(numpy.log2(SAMPLE_RATE / 2)), fft_bins_before_mirror, base=2)
    log10test = numpy.logspace(0, numpy.log2(numpy.log10(SAMPLE_RATE / 2)), fft_bins_before_mirror, base=10)
    logBigtest = numpy.logspace(0, numpy.log10(SAMPLE_RATE / 2), fft_bins_before_mirror, base=2) # works best when not semilogx graph
    #log10space_scaler = numpy.log10(x)
    data_fft_magnitude_logspace = 2**log2test * data_fft_magnitude_normalized 
    line.set_ydata(data_fft_magnitude_logspace)
    
    fig.canvas.draw()
    fig.canvas.flush_events()