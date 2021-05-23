import pyaudio
import wave
import sys
import numpy as np
import struct
from scipy import signal, integrate
import matplotlib.pyplot as plt
import time
#解码

def Preamble():
    '''Generate preamble signal.'''
    t = np.linspace(0,1, 48000,endpoint = True,dtype = np.float32)
    t=t[0:480]
    f_p = np.concatenate([np.linspace(2500, 8000, 240), np.linspace(8000,2500, 240)])
    preamble_signal = (np.sin(2*np.pi*integrate.cumtrapz(f_p, t))).astype(np.float32)
    return preamble_signal

def PointerBeforeHead(sig,reference,length_head):
    corr=signal.correlate(sig,reference,mode='full',method='fft')
    #调试用，检验头是否对齐。使用的时候把plt和print三行代码注释掉。
    # plt.plot(corr)
    # plt.show()
    ret=np.argmax(corr)-length_head
    # print(ret)
    return ret

def PointerBeforeHead_1(sig,reference,length_head):
    corr=signal.correlate(sig,reference,mode='full',method='fft')
    #调试用，检验头是否对齐。使用的时候把plt和print三行代码注释掉。
    # plt.plot(corr)
    # plt.show()
    res=0
    for i in range(len(corr)):
        if corr[i]>8:
            res=i
            break
    ret=res-length_head
    # print(ret)
    return ret

def Correlation(signal, reference):
    corrSum = np.zeros(len(signal)-len(reference))
    for i in range(0, len(signal)-len(reference)):
        sum = 0
        for j in range(0, len(reference)):
            sum = sum + signal[i+j] * reference[j]
        corrSum[i] = sum
    return corrSum

def CleanFile(Filename):
    File=open(Filename,'w')
    File.truncate()

def FindNumberSum(array):
    #调试用
    # plt.plot(array)
    # plt.show()
    sum=0
    for i in array:
        sum+=i
    if sum>=0:
        return "0"
    else:
        return "1"
    
def Write(Filename,str1):
    with open(Filename, 'a') as file_object:
        file_object.write(str1)

def Record(Chunk,Format,Channels,Rate,Time,Filename,P):
    '''Record audio.'''
    stream = P.open(format=Format,
                channels=Channels,
                rate=Rate,
                input=True,
                frames_per_buffer=Chunk)

    print("* recording")
    frames = []
    for i in range(0, int(Rate / Chunk * Time)):
        data = stream.read(Chunk)
        frames.append(data)
    print("* done recording")

    stream.stop_stream()
    stream.close()

    wf = wave.open(Filename, 'wb')
    wf.setnchannels(Channels)
    wf.setsampwidth(P.get_sample_size(Format))
    wf.setframerate(Rate)
    wf.writeframes(b''.join(frames))
    wf.close()

def NParity(length):
    i=0
    pow=1
    while pow<=length+i:
        i+=1
        pow*=2
    return i

def HammingDecode(data):
    length=len(data)

    #generate a new parity list
    list_new_p=list()
    i=0 #loop counter for j
    j=0 #2**i-1, index of parity bits
    while j<length:
        parity=0
        k=j #index
        while k<length:
            parity^=data[k]
            if (k+2)%(j+1)==0:
                k+=j+2
            else:
                k+=1
        list_new_p.append(parity)
        i+=1
        j=(j+1)*2-1
    # print(list_new_p) #调试用

    #revise wrong data
    sum=0
    pow=1 #2**i
    for j in list_new_p:
        sum+=j*pow
        pow*=2
    if sum!=0 and sum<=length:
        print("wrong data: "+str(sum-1)) #调试用
        data[sum-1]= 0 if data[sum-1]==1 else 1
    
    #generate data list
    list_ret=list()
    i=2
    j=3 #2**(an integer)-1
    while i<length:
        list_ret.append(data[i])
        if i==j-1:
            i+=2
            j=(j+1)*2-1
        else:
            i+=1
    return list_ret

time_start=time.time()

#Decode
p = pyaudio.PyAudio()
fs = 48000
seconds = 0.001
f = 2000
channels = 1
Format = pyaudio.paFloat32
chunk = 1024
length_str=10000
length_frame=10
length_ham_frame=NParity(length_frame)+length_frame
ADD=0  #调试用，增加一段ADD个信号长度的没用的信号(耗时ADD*0.001s)
more_time=2 #调试用，多录制的时间
record_file="3-record.wav"

record_time=seconds*(length_str/length_frame*(10+length_ham_frame)+ADD)+more_time
Record(chunk,Format,channels,fs,record_time,record_file,p)
p.terminate()

pream=Preamble()
signal_0 = (np.sin(2*np.pi*f*np.arange(0,seconds,1/fs))).astype(np.float32)
#signal_1 = (-np.sin(2*np.pi*f*np.arange(0,seconds,1/fs))).astype(np.float32)

length_sig=len(signal_0)
length_head=len(pream)
#length of one frame:

#Decode
FIND_1=70000
FIND_2=300
n_frame = int(length_str/length_frame)
#调试用，使解码文件改为播放的文件，而非录制的
# filename_r="3.wav"

CleanFile("OUTPUT.txt")
wf = wave.open(record_file, 'rb')

#调试用，去掉开头的一段数据再解码
# wf.setpos(51000)
# 调试用，展示整个信号和preamble的相干性
# pointer_tell=wf.tell()
# data = wf.readframes(50000)
# sig = np.asarray(struct.unpack('f'*50000,data))
# res=signal.correlate(sig,pream,mode='full',method='fft')
# plt.plot(res)
# plt.show()
# wf.setpos(pointer_tell)

pointer=0
for i in range(n_frame):
    #save the file pointer
    pointer_tell=wf.tell()
    #decode the preamble
    if i==0:
        sig_to_find_head = wf.readframes(FIND_1)
        sig_to_find_head = np.asarray(struct.unpack('f'*FIND_1,sig_to_find_head))
        pointer_add=PointerBeforeHead_1(sig_to_find_head,pream,length_head-1)
    else:
        sig_to_find_head = wf.readframes(FIND_2)
        sig_to_find_head = np.asarray(struct.unpack('f'*FIND_2,sig_to_find_head))
        pointer_add=PointerBeforeHead(sig_to_find_head,pream,length_head-1)
    pointer=pointer_tell+pointer_add+length_head
    wf.setpos(pointer)
    #decode
    l_temp=list()
    for j in range(i*length_ham_frame,(i+1)*length_ham_frame):
        data = wf.readframes(length_sig)
        sig = np.asarray(struct.unpack('f'*length_sig,data))
        sig_mul=sig*signal_0
        str1=FindNumberSum(sig_mul)
        l_temp.append(int(str1))
    l_ret=HammingDecode(l_temp)
    for k in l_ret:
        Write("OUTPUT.txt",str(k))
#tail
if length_str-length_frame*n_frame !=0:
    #save the file pointer
    pointer_tell=wf.tell()
    #decode the preamble
    sig_to_find_head = wf.readframes(FIND_2)
    sig_to_find_head = np.asarray(struct.unpack('f'*FIND_2,sig_to_find_head))
    pointer_add=PointerBeforeHead(sig_to_find_head,pream,length_head-1)
    pointer=pointer_tell+pointer_add+length_head
    wf.setpos(pointer)
    #decode
    l_temp=list()
    for j in range(i*length_ham_frame,(i+1)*length_ham_frame):
        data = wf.readframes(length_sig)
        sig = np.asarray(struct.unpack('f'*length_sig,data))
        sig_mul=sig*signal_0
        str1=FindNumberSum(sig_mul)
        l_temp.append(int(str1))
    l_ret=HammingDecode(l_temp)
    for k in l_ret:
        Write("OUTPUT.txt",str(k))

time_end=time.time()
print("Time is: "+str(time_end-time_start))