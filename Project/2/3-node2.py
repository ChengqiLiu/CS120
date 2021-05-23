import pyaudio
import wave
import sys
import numpy as np
import struct
from scipy import signal,integrate
import matplotlib.pyplot as plt
import threading
import time
import ctypes
import inspect

def byte_to_str(byte):
    temp=int.from_bytes(byte,'big')
    b=bin(temp)[2:]
    len_add=8-len(b)
    return len_add*"0"+b

def Preamble():
    '''Generate preamble signal.'''
    t = np.linspace(0,1, 48000,endpoint = True,dtype = np.float32)
    t=t[0:120]
    f_p = np.concatenate([np.linspace(8000, 12000, 60), np.linspace(12000,8000, 60)])
    preamble_signal = (np.sin(2*np.pi*integrate.cumtrapz(f_p, t))).astype(np.float32)
    return preamble_signal

def PointerBeforeHead(sig,reference,length_head):
    corr=signal.correlate(sig,reference,mode='full',method='fft')
    # 调试用，检验头是否对齐。使用的时候把plt和print三行代码注释掉。
    # plt.plot(corr)
    # plt.show()
    armax=np.argmax(corr)
    ret=armax-length_head
    # print(ret)
    return ret

def PointerBeforeHead_1(sig,reference,length_head):
    corr=signal.correlate(sig,reference,mode='full',method='fft')
    #调试用，检验头是否对齐。使用的时候把plt和print三行代码注释掉。
    # plt.plot(corr)
    # plt.show()
    res=0
    for i in range(len(corr)):
        if corr[i]>45:
            res=i
            break
    ret=res-length_head
    # print(ret)
    return ret

def CleanFile(Filename):
    File=open(Filename,'w')
    File.truncate()

def FindNumberCount(array):
    positive_num=0
    negative_num=0
    for i in array:
        if i<0:
            negative_num+=1
        elif i>0:
            positive_num+=1
    if positive_num>=negative_num:
        return "0"
    else:
        return "1"

def FindNumberAvr(array):
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
        
def DealWithError_2(P):
    KillThread(t_jam)
    KillThread(t_send)
    exit()

def Check(data):
    length=len(data)
    data_use=struct.unpack('f'*int(length/4),data)
    corr=signal.correlate(data_use,pream,mode='full',method='fft')
    check_num=0
    for i in corr:
        if i<0.006:
            check_num+=1
        else:
            check_num=0
        if check_num>100:
            # plt.plot(corr)
            # plt.show()
            return True
    return False

def Write(Filename,str1):
    with open(Filename, 'ab') as file_object:
        file_object.write(str1)

def _async_raise(tid, exctype):
    """raises the exception, performs cleanup if needed"""
    tid = ctypes.c_long(tid)
    if not inspect.isclass(exctype):
        exctype = type(exctype)
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, ctypes.py_object(exctype))
    if res == 0:
        raise ValueError("invalid thread id")
    elif res != 1:
        # """if it returns a number greater than one, you're in trouble,
        # and you should call it again with exc=NULL to revert the effect"""
        ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, None)
        raise SystemError("PyThreadState_SetAsyncExc failed")
 
def KillThread(thread):
    if thread == None:
        print('thread id is None, return....')
        return
    _async_raise(thread.ident, SystemExit)

def MaxInArray(arr):
    num_0=0
    num_1=0
    for i in arr:
        if i=='0':
            num_0+=1
        else:
            num_1+=1
    if num_0>=num_1:
        return '0'
    else:
        return '1'      

def PlayJamming():
    #Open the file
    wf = wave.open("Jamming.wav", 'rb')
    #Play audio
    stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                channels=wf.getnchannels(),
                rate=wf.getframerate(),
                output=True)

    data = wf.readframes(chunk)

    print("* Play Jamming")
    while len(data)>0:
        stream.write(data)
        data = wf.readframes(chunk)
    print("* End Jamming")

    stream.stop_stream()
    stream.close()
    wf.close()

def Receive(P):
    FIND_1=50000
    FIND_2=50

    stream = P.open(format=Format,channels=channels,rate=fs,input=True,frames_per_buffer=chunk)

    t=0
    print("*Start receive")
    frames = []
    for i in range(0, int(fs / chunk * record_time)):
        data = stream.read(chunk)
        frames.append(data)
        
        t+=chunk/4
        if t>15000 and t<590000 and Check(data):
            print("link error!")
            print("Error at: "+str(t))
            DealWithError_2(P)
    print("*End receive")
    
    stream.stop_stream()
    stream.close()

    #Decode
    frames=b''.join(frames)
    frames = np.asarray(struct.unpack('f'*int(len(frames)/4),frames))
    CleanFile("OUTPUT2to1.bin")
    
    wn=2*8000/fs
    b, a = signal.butter(12, wn, 'highpass')
    frames = signal.filtfilt(b, a, frames)
    # plt.plot(frames)
    # plt.show()
    # 调试用，展示整个信号和preamble的相干性
    # res=signal.correlate(frames,pream,mode='full',method='fft')
    # plt.plot(res)
    # plt.show()
    # 调试用，实时纠错
    # fin = open("INPUT2to1.bin","rb")
    # read=fin.read()
    # bytes_in=struct.unpack(len(read)*'c',read)

    pointer=0
    for i in range(n_frame):
        #save the file pointer
        pointer_tell=pointer
        #decode the preamble`
        if i==0:
            sig_to_find_head = frames[pointer:pointer+FIND_1]
            pointer_add=PointerBeforeHead_1(sig_to_find_head,pream,length_head-1)
        else:
            sig_to_find_head = frames[pointer:pointer+FIND_2]
            pointer_add=PointerBeforeHead(sig_to_find_head,pream,length_head-1)
        pointer=pointer_tell+(pointer_add+length_head)
        #decode
        for j in range(i*length_frame,(i+1)*length_frame):
            decode_str=str()
            for k in range(8):
                arr=[]
                str1=''
                for h in range(repeat_n):
                    sig = frames[pointer:pointer+length_sig]
                    pointer+=length_sig
                    sig_mul=sig*signal_0
                    str1=FindNumberAvr(sig_mul)
                    arr.append(str1)
                    if h==repeat_n-1:
                        str1=MaxInArray(arr)
                if str1=='':
                    print("Empty error!")
                decode_str=decode_str+str1
                if k==7:
                    #调试用，实时纠错
                    # stand=byte_to_str(bytes_in[j])
                    # if decode_str!=stand:
                    #     print("id: "+str(j))
                    #     print("decode: "+decode_str)
                    #     print("stand: "+stand)
                    integer=int(decode_str,2)
                    w_byte=integer.to_bytes(1, 'big')
                    Write("OUTPUT2to1.bin",w_byte)
    #tail
    if length_str-length_frame*n_frame !=0:
        #save the file pointer
        pointer_tell=pointer
        #decode the preamble
        sig_to_find_head = frames[pointer:pointer+FIND_2*4]
        sig_to_find_head = np.asarray(struct.unpack('f'*FIND_2,sig_to_find_head))
        pointer_add=PointerBeforeHead(sig_to_find_head,pream,length_head-1)
        pointer=pointer_tell+(pointer_add+length_head)*4
        #decode
        for j in range(length_frame*n_frame,length_str):
            decode_str=str()
            for k in range(8):
                arr=[]
                str1=''
                for h in range(repeat_n):
                    data = frames[pointer:pointer+length_sig*4]
                    pointer+=length_sig*4
                    sig = np.asarray(struct.unpack('f'*length_sig,data))
                    sig_mul=sig*signal_0
                    str1=FindNumberAvr(sig_mul)
                    arr.append(str1)
                    if h==repeat_n-1:
                        str1=MaxInArray(arr)
                if str1=='':
                    print("Empty error!")
                decode_str=decode_str+str1
                if k==7:
                    integer=int(decode_str,2)
                    w_byte=integer.to_bytes(1, 'big')
                    Write("OUTPUT2to1.bin",w_byte)

def Send(P):
    #Read the file "INPUT2to1.bin"
    f = open("INPUT2to1.bin","rb")
    read=f.read()
    bytes_in=struct.unpack(length_str*'c',read)

    stream = P.open(format=Format,channels=channels,rate=fs,output=True)

    print("*Start send")
          
    for i in range(n_frame):
        #Play the preamble
        stream.write(pream.tobytes())
        for j in range(i*length_frame,(i+1)*length_frame):
            str_temp=byte_to_str(bytes_in[j])
            for k in str_temp:
                if k=='1':
                    for h in range(repeat_n):
                        stream.write(signal_1.tobytes())
                elif k=='0':
                    for h in range(repeat_n):
                        stream.write(signal_0.tobytes())
                else:
                    print("error!")
                    exit(1)
    #tail:
    if length_str-length_frame*n_frame!=0:
        #Play the preamble
        stream.write(pream.tobytes())
        for j in range(length_frame*n_frame,length_str):
            str_temp=byte_to_str(bytes_in[j])
            for k in str_temp:
                if k=='1':
                    for h in range(repeat_n):
                        stream.write(signal_1.tobytes())
                elif k=='0':
                    for h in range(repeat_n):
                        stream.write(signal_0.tobytes())
                else:
                    print("error!")
                    exit(1)
    #调试用，增加一段ADD个信号长度的没用的信号
    for i in range(ADD):
        stream.write(signal_0.tobytes())
    print("*Finish send")
    stream.stop_stream()
    stream.close()

time.sleep(1.5)
time_start=time.time()
#变量声明
p = pyaudio.PyAudio()
fs = 48000
seconds = 0.0001
f = 10000
channels = 1
Format = pyaudio.paFloat32
chunk = 1024
length_str=6250
length_frame=10
ADD=3000 #调试用，增加一段ADD个信号长度的没用的信号(耗时ADD*seconds)
more_time=-17 #调试用，多录制的时间

pream=Preamble()
signal_0 = (np.sin(2*np.pi*f*np.arange(0,seconds,1/fs))).astype(np.float32)
signal_1 = (-np.sin(2*np.pi*f*np.arange(0,seconds,1/fs))).astype(np.float32)
length_head=len(pream)
length_sig=len(signal_0)
n_frame = int(length_str/length_frame)
repeat_n=8

record_time=seconds*(length_str*8*repeat_n/length_frame*(5+length_frame))+more_time
play_file="INPUT2to1.bin"

t_jam=threading.Thread(target=PlayJamming,args=())
t_receive=threading.Thread(target=Receive, args=(p,))
t_send=threading.Thread(target=Send, args=(p,))

t_jam.start()
t_receive.start()
t_send.start()
t_send.join()
t_receive.join()
if t_jam.is_alive():
    KillThread(t_jam)

p.terminate()

time_end=time.time()
print("Time is: "+str(time_end-time_start))