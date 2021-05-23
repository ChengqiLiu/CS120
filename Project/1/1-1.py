import pyaudio
import wave
import sys


CHUNK = 1024
FORMAT = pyaudio.paFloat32
CHANNELS = 1
RATE = 48000
SECONDS = 12
FILENAME = "1-1.wav"

p = pyaudio.PyAudio()

#Record audio
stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK)

print("* recording")
frames = []
for i in range(0, int(RATE / CHUNK * SECONDS)):
    data = stream.read(CHUNK)
    frames.append(data)
print("* done recording")

stream.stop_stream()
stream.close()

#Write into the file "FILENAME"
wf = wave.open(FILENAME, 'wb')
wf.setnchannels(CHANNELS)
wf.setsampwidth(p.get_sample_size(FORMAT))
wf.setframerate(RATE)
wf.writeframes(b''.join(frames))
wf.close()

#Open the file
wf = wave.open(FILENAME, 'rb')
#Play audio
stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                channels=wf.getnchannels(),
                rate=wf.getframerate(),
                output=True)

data = wf.readframes(CHUNK)

print("* playing")
while len(data)>0:
    stream.write(data)
    data = wf.readframes(CHUNK)
print("* done playing")

stream.stop_stream()
stream.close()
wf.close()

p.terminate()  

#Works Cited:
#https://stackoverflow.com/questions/8299303/generating-sine-wave-sound-in-python