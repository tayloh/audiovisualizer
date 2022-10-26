import struct
import numpy
import matplotlib.pyplot as plt
import pyaudio
import wave
import sys
import os

# http://hyperphysics.phy-astr.gsu.edu/hbase/Audio/equal.html
# https://github.com/aiXander/Realtime_PyAudio_FFT

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

def getBinIndexFromFreq(freq, sample_size, sample_rate):
    freqs_per_bin = sample_rate / sample_size
    index = int(freq / freqs_per_bin) # Ceil - 1 => int truncate
    return index

def getBinIndicesFromFrequencyList(freq_list, sample_size, sample_rate):
    ret = []
    for i in range(len(freq_list)):
        binIdx = getBinIndexFromFreq(freq_list[i], sample_size, sample_rate)
        ret.append(binIdx)
    return ret

def computeEnergyAvgFromIndicesAndFFT(indices, fft_data):
    ret = []
    for i in range(1, len(indices)):
        lower = indices[i-1]
        upper = indices[i]
        avg_energy_in_bin = sum(fft_data[lower:upper]) / (upper-lower)
        ret.append(avg_energy_in_bin)
        
    return ret


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
print(SAMPLE_RATE)

stream = audio.open(
    format=FORMAT,
    channels=CHANNELS,
    rate=SAMPLE_RATE,
    output=True,
)

fft_bins_before_mirror = int(SAMPLE_SIZE / 2)
fft_window = numpy.hanning(SAMPLE_SIZE)

frequencies = [25*x for x in range(180)]
#frequencies += [3500 + 100*x for x in range(70)] #3500-10450
# frequencies = [0, 50, 100, 150, 200, 250, 300, 350, 400, 4000, 5000, 6000, 7000, 8000, 9000, 
#                 10000, 11000, 12000, 13000, 14000, 15000, 16000, 17000, 18000]

fft_rect_bin_indices = getBinIndicesFromFrequencyList(frequencies, SAMPLE_SIZE, SAMPLE_RATE)
num_rect_bins = len(frequencies)-1
fft_rect_bin_avg = numpy.zeros(num_rect_bins)
history_length = 10
fft_bin_energy_history = [[] for x in range(len(fft_rect_bin_avg))]

print(fft_rect_bin_indices)

fig, ax = plt.subplots(1, figsize=(15, 7))

x = numpy.linspace(0, SAMPLE_RATE / 2, num_rect_bins)
line, = ax.plot(x, numpy.random.rand(num_rect_bins), '-', lw=2)
#line, = ax.semilogx(x, numpy.random.rand(fft_bins_before_mirror), '-', lw=2, basex=2)
#ax.set_xlim(0, 18000)
#ax.set_xlim(20, 16000) # SAMPLE_RATE / 2
ax.set_facecolor("k")
fig.set_facecolor("k")

plt.show(block=False)

band_buffer = numpy.zeros(len(x))
buffer_decrease = numpy.zeros(len(x))

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
    
    # TODO just use np.logspace(0, np.log2(22050), 1024, base=2) instead X
    log2test2 = numpy.logspace(0, numpy.log2(SAMPLE_RATE / 2), fft_bins_before_mirror, base=2)
    data_fft_magnitude_logspace = log2test2 * data_fft_magnitude_normalized

    fft_rect_bin_avg = computeEnergyAvgFromIndicesAndFFT(fft_rect_bin_indices, data_fft_magnitude_logspace)

    # TODO https://www.youtube.com/watch?v=lEUuC3LQnzs Try the buffers X
    # TODO https://www.youtube.com/watch?v=mHk3ZiKNH48 Very weird way of normalization that seems to work awfully well /

    # TODO could use np.logspace(0, np.log10(22050), 1024, base=2), note log10
    # but then need to carefully choose the frequency ranges again, check the github repo for how to

    # TODO ? gaussian smoothing, calc. bins, mean value equalization

    # for i in range(len(fft_bin_energy_history)):
    #     fft_bin_energy_history[i] = fft_bin_energy_history[i] + [fft_rect_bin_avg[i]]
    #     if (len(fft_bin_energy_history[i]) == history_length + 1):
    #         fft_bin_energy_history[i] = fft_bin_energy_history[i][1:]

    # fft_smoothed = numpy.zeros(len(fft_rect_bin_avg))

    # for i in range(len(fft_smoothed)):
    #     threshold = sum(fft_bin_energy_history[i]) / history_length
    #     if fft_rect_bin_avg[i] < threshold:
    #         fft_smoothed[i] = fft_bin_energy_history[i][-2] - threshold*0.1
            
    #     else:
    #         fft_smoothed[i] = fft_rect_bin_avg[i]

    for i in range(len(x)):
        if (fft_rect_bin_avg[i] > band_buffer[i]):
            band_buffer[i] = fft_rect_bin_avg[i]
        else:
            #buffer_decrease[i] = (band_buffer[i] - fft_rect_bin_avg[i]) / 4
            buffer_decrease[i] = band_buffer[i] / 8
            band_buffer[i] -= buffer_decrease[i]

    line.set_ydata(band_buffer)
    #line.set_ydata(fft_rect_bin_avg)
    #line.set_ydata(fft_smoothed)
    
    fig.canvas.draw()
    fig.canvas.flush_events()