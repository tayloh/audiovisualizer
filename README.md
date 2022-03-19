# Small project with the goal of doing audio visualization on a led strip
* Play any song using client software on client computer and the raspberry pi should do led strip audio visualization.
* Stretch goal: Any audio played on the client computer should be captured and visualized using the pi.

## Dependencies:
* pyaudio (use pipwin to install on windows)
* numpy
* matplotlib (currently used for visualization while waiting for leds)

## How to run:
* `git clone`
* cd into directory
* start server: `python pi_server.py`
* start playing a wave file using the client: `python audio_client.py pathtowavefile.wav` 
* A seperate demo of just the audio visualizer is available as well: `python retrosunset.py relative-path-to-directory-with-wav-files`
* E.g. `python retrosunset.py ../wavmusic`
* (The file audio_demo.py can be ignored)

## Demo:
https://www.youtube.com/watch?v=F4yoJkbZ3wE