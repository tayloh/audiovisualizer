import pyaudio
import wave
import sys
import struct
import matplotlib.pyplot as plt
import numpy
import time
import os

# FFT output explained: https://www.youtube.com/watch?v=3aOaUv3s8RY
# Windowing: https://digitalsoundandmusic.com/2-3-10-windowing-the-fft/
# https://ciphrd.com/2019/09/01/audio-analysis-for-advanced-music-visualization-pt-1/

CHUNK_SIZE = 1024*2 # num samples
NUM_RECTS = 128 #128

def openWavfileFromArgs():
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
    
    return wf

def getRectAmplitudes(num_rects, fft_values):
    result = []

    # since DFT is symmetric around middle
    # only use half of the values
    freqs_per_band = len(fft_values) // (2*num_rects)

    for i in range(num_rects):
        result.append(sum(fft_values[freqs_per_band*i:freqs_per_band*(i+1)]))
    
    return result

def computeSignalEnergy(signal, mode="all"):
    if mode == "all":
        return sum(signal) / len(signal)
    if mode == "bass":
        return sum(signal[2:6]) / len(signal[2:6])
    if mode == "mixed":
        return (sum(signal[2:6]) + sum(signal[13:36])) / (len(signal[2:6]) + len(signal[13:36]))
    if mode == "lowhat":
        return sum(signal[13:36]) / len(signal[13:36])

def computeVariance(avg, data):
    denom = len(data) if len(data) > 0 else 1
    return sum([(x - avg)**2 for x in data]) / denom

def easingFunction(x):
    if x < 0.5:
        return 4*x**3
    else:
        return (x-1)*(2*x-2)**2 + 1

wf = openWavfileFromArgs()

# pyaudio for audio streaming
p = pyaudio.PyAudio()

# get values from wav header
FORMAT = p.get_format_from_width(wf.getsampwidth())
CHANNELS = wf.getnchannels()
SAMPLERATE = wf.getframerate()


# open a stream and set values that we got from wav header
stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=SAMPLERATE,
                output=True)


raw_data = wf.readframes(CHUNK_SIZE)

#fig, (beat_graph, energy_history, barplot) = plt.subplots(3)
#fig, (beat_graph, energy_history, energy_lowhat) = plt.subplots(3)
fig, (beat_graph, energy_history) = plt.subplots(2)

# bars = barplot.bar(range(NUM_RECTS), numpy.random.rand(NUM_RECTS))
# barplot.set_ylim(0, 1)

energy_max_x = 32
line, = energy_history.plot(numpy.linspace(0, energy_max_x, energy_max_x), numpy.linspace(0.5, 0.5, energy_max_x), color="red")
lineAvg, = energy_history.plot(numpy.linspace(0, energy_max_x, energy_max_x), numpy.linspace(0.5, 0.5, energy_max_x), color="green")
lineC, = energy_history.plot(numpy.linspace(0, energy_max_x, energy_max_x), numpy.linspace(0.5, 0.5, energy_max_x), color="blue")
energy_history.set_ylim(0, 0.005)
energy_history.set_xlim(0, energy_max_x)
highest_seen_energy = 0

# line_lowhat, = energy_lowhat.plot(numpy.linspace(0, energy_max_x, energy_max_x), numpy.linspace(0.5, 0.5, energy_max_x), color="red")
# lineAvg_lowhat, = energy_lowhat.plot(numpy.linspace(0, energy_max_x, energy_max_x), numpy.linspace(0.5, 0.5, energy_max_x), color="green")
# lineC_lowhat, = energy_lowhat.plot(numpy.linspace(0, energy_max_x, energy_max_x), numpy.linspace(0.5, 0.5, energy_max_x), color="blue")
# energy_lowhat.set_ylim(0, 0.02)
# energy_lowhat.set_xlim(0, energy_max_x)

beat_std = 1.05

max_beat_persistence = 60 / 160
beat_persistence = max_beat_persistence
time_last_beat = time.time()

line_beat, = beat_graph.plot(numpy.linspace(0, energy_max_x, energy_max_x), numpy.linspace(1, 1, energy_max_x), color="purple")
beat_graph.set_ylim(0, 2)
beat_graph.set_xlim(0, energy_max_x)
beat_history = numpy.zeros(energy_max_x)

fig.show()
fig.canvas.draw()
fig.canvas.flush_events()

E_History = numpy.zeros(energy_max_x)
E_avg = 0
step = 0

#E_History_lowhat = numpy.zeros(energy_max_x)
#E_avg_lowhat = 0

while len(raw_data) > 0:
    stream.write(raw_data)

    try:
        amplitude_data_ints = numpy.array(struct.unpack(str(CHUNK_SIZE) + "i", raw_data))
        fft_data = numpy.abs(numpy.fft.fft(amplitude_data_ints)) / ((CHUNK_SIZE)*2**32)
        #fft_data = fft_data / max(fft_data))
        #normalized_v = fft_data / numpy.sqrt(numpy.sum(fft_data**2))

        E = computeSignalEnergy(fft_data, mode="bass")
        #E_lowhat = computeSignalEnergy(fft_data, mode="lowhat")

        highest_seen_energy = max(E, highest_seen_energy)
        energy_history.set_ylim(0, highest_seen_energy*2)

        E_History = numpy.roll(E_History, 1)
        E_History[0] = E

        #E_History_lowhat = numpy.roll(E_History_lowhat, 1)
        #E_History_lowhat[0] = E_lowhat

        E_history_no_zeros = E_History[E_History != 0]
        #E_history_lowhat_no_zeros = E_History_lowhat[E_History_lowhat != 0]

        line.set_ydata(E_History)
        #line_lowhat.set_ydata(E_History_lowhat)
        avg = numpy.average(E_history_no_zeros)
        #avg_lowhat = numpy.average(E_history_lowhat_no_zeros)

        lineAvg.set_ydata(avg)
        #lineAvg_lowhat.set_ydata(avg_lowhat)

        variance = computeVariance(avg, E_history_no_zeros)
        #variance_lowhat = computeVariance(avg_lowhat, E_history_lowhat_no_zeros)

        std = numpy.sqrt(variance)
        #std_lowhat = numpy.sqrt(variance_lowhat)

        lineC.set_ydata(avg + beat_std*std)
        threshold = -12*std + 1.55
        threshold = max(threshold, 1.1)
        #lineC.set_ydata(threshold * avg)
        #print(threshold)
        #print(variance)
        #print(avg, avg+0.5*avg)
        #lineC_lowhat.set_ydata(avg_lowhat + beat_std*std_lowhat)
        amps = getRectAmplitudes(NUM_RECTS, fft_data)

        beat_history = numpy.roll(beat_history, 1)

        # or E_lowhat > avg_lowhat + beat_std*std_lowhat
        # Is a beat
        cond1 = E > avg + beat_std*std 
        cond3 = E > threshold * avg
        cond_persistence = (time.time() - time_last_beat) >= beat_persistence
        if cond1 and cond_persistence:
            #print((avg + std) / avg)
            time_last_beat = time.time()
            beat_history[0] = 1
        elif (time.time() - time_last_beat) < beat_persistence:
            beat_history[0] = easingFunction(1 - (time.time() - time_last_beat) / beat_persistence)
        else:
            beat_history[0] = 0
        
        line_beat.set_ydata(beat_history)

        # for bar, amp in zip(bars, amps):
        #     bar.set_height(amp)
        #     if E > avg + std:
        #         bar.set_color([1, 0, 0])
        #     else:
        #         bar.set_color([0, 0, 0])

    except struct.error:
        pass
    
    step+=1
    # if step == energy_max_x: 
    #     E_History.fill(0) # cant reset if I want the variance things to work
    #     beat_history.fill(0)
    step %= energy_max_x

    raw_data = wf.readframes(CHUNK_SIZE)

    fig.canvas.draw()  
    fig.canvas.flush_events()