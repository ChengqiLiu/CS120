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
        l_temp=str1[i*Len_frame:(i+1)*Len_frame]
        l_ham=HammingCode(l_temp,Len_frame)
        #Play the preamble
        stream.write(pream.tobytes())
        for j in l_ham:
            if j==1:
                stream.write(signal_1.tobytes())
            elif j==0:
                stream.write(signal_0.tobytes())
            else:
                print("error!")
                exit(1)
    #tail:
    if length_str-Len_frame*n_frame!=0:
        l_temp=str1[i*Len_frame:(i+1)*Len_frame]
        l_ham=HammingCode(l_temp,Len_frame)
        #Play the preamble
        stream.write(pream.tobytes())
        for j in l_ham:
            if j==1:
                stream.write(signal_1.tobytes())
            elif j==0:
                stream.write(signal_0.tobytes())
            else:
                print("error!")
                exit(1)
    #调试用，增加一段ADD个信号长度的没用的信号
    for i in range(100):
        stream.write(signal_0.tobytes())
    print("* done playing")

def NParity(length):
    i=0
    pow=1
    while pow<=length+i:
        i+=1
        pow*=2
    return i

def EmptyParityBits(data,length):
    n=NParity(length)
    i=0 #loop counter
    j=0 #parity bits number
    k=0 #data bits number
    pow=1 #2**j
    list1=list()
    while i <n+length:
        if i== pow-1:
            list1.insert(i,0)
            j+=1
            pow*=2
        else:
            list1.insert(i,int(data[k]))
            k+=1
        i+=1
    return list1

def HammingCode(data,length):
    n=NParity(length)
    list1=EmptyParityBits(data,length)
    i=0 #loop counter for j
    j=0 #2**i-1, index of parity bits
    while j<length+n:
        list1[j]=0
        k=j #index
        while k<length+n:
            list1[j]^=list1[k]
            if (k+2)%(j+1)==0:
                k+=j+2
            else:
                k+=1
        i+=1
        j=(j+1)*2-1
    return list1

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
length_frame=10
ADD=0  #调试用，增加一段ADD个信号长度的没用的信号(耗时0.01s)

pream=Preamble()
signal_0 = (np.sin(2*np.pi*f*np.arange(0,seconds,1/fs))).astype(np.float32)

length_head=len(pream)
length_sig=len(signal_0)

play_file="INPUT.txt"
Play(seconds,Format,channels,f,fs,length_frame,ADD,play_file,p)
p.terminate()

time_end=time.time()
print("Time is: "+str(time_end-time_start))