import pyaudio
import numpy as np

p = pyaudio.PyAudio()
volume = 1
fs = 48000
seconds =5
f1 = 1000.0
f2 = 10000.0

stream = p.open(format=pyaudio.paFloat32,
                channels=1,
                rate=fs,
                output=True)
signal = np.sin(2*np.pi*np.arange(fs*seconds)*f1/fs)+np.sin(2*np.pi*np.arange(fs*seconds)*f2/fs)
samples = (signal/2).astype(np.float32)

print("* playing")
stream.write((volume*samples).tobytes())
print("* done playing")
   
stream.stop_stream()
stream.close()
p.terminate()

#Works Cited:
#https://blog.csdn.net/c602273091/article/details/46502527#%E5%BD%95%E9%9F%B3