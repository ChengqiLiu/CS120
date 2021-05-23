import pyaudio
import wave
import sys
import numpy as np
import struct
from scipy import signal, integrate
import matplotlib.pyplot as plt
import time
#播放

def Preamble():
    '''Generate preamble signal.'''
    t = np.linspace(0,1, 48000,endpoint = True,dtype = np.float32)
    t=t[0:480]
    f_p = np.concatenate([np.linspace(2500, 8000, 240), np.linspace(8000,2500, 240)])
    preamble_signal = (np.sin(2*np.pi*integrate.cumtrapz(f_p, t))).astype(np.float32)
    return preamble_signal

def Play(Seconds,Format,Channels,F,Rate,Len_frame,ADD,Filename,P):
    #Read the file "INPUT.txt"
    f = open(Filename,"r",encoding="utf-8")
    str1 = f.read()
    length_str=len(str1)
    n_frame = int(length_str/Len_frame)

    pream=Preamble()
    signal_0 = (np.sin(2*np.pi*F*np.arange(0,Seconds,1/Rate))).astype(np.float32)
    signal_1 = (-np.sin(2*np.pi*F*np.arange(0,Seconds,1/Rate))).astype(np.float32)

    stream = P.open(format=Format,
                channels=Channels,
                rate=Rate,
                output=True)

    print("* playing")
    #调试用，增加一段ADD个信号长度的没用的信号
    for i in range(ADD):
        stream.write(signal_0.tobytes())
        
    for i in range(n_frame):
        #Play the preamble
        stream.write(pream.tobytes())
        for j in range(i*Len_frame,(i+1)*Len_frame):
            if str1[j]=='1':
                stream.write(signal_1.tobytes())
            elif str1[j]=='0':
                stream.write(signal_0.tobytes())
            else:
                print("error!")
                exit(1)
    #tail:
    if length_str-Len_frame*n_frame!=0:
        #Play the preamble
        stream.write(pream.tobytes())
        for j in range(Len_frame*n_frame,length_str):
            if str1[j]=='1':
                stream.write(signal_1.tobytes())
            elif str1[j]=='0':
                stream.write(signal_0.tobytes())
            else:
                print("error!")
                exit(1)
    for i in range(100):
        stream.write(signal_0.tobytes())
    print("* done playing")

time_start=time.time()

#变量声明
p = pyaudio.PyAudio()
fs = 48000
seconds = 0.001
f = 2000
channels = 1
Format = pyaudio.paFloat32
chunk = 1024
length_str=10000
length_frame=100
ADD=0  #调试用，增加一段ADD个信号长度的没用的信号(耗时0.01s)
more_time=1.5 #调试用，多录制的时间

pream=Preamble()
signal_0 = (np.sin(2*np.pi*f*np.arange(0,seconds,1/fs))).astype(np.float32)

length_head=len(pream)
length_sig=len(signal_0)

play_file="INPUT.txt"
Play(seconds,Format,channels,f,fs,length_frame,ADD,play_file,p)
p.terminate()

time_end=time.time()
print("Time is: "+str(time_end-time_start))