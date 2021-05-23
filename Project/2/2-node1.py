import pyaudio
import wave
import sys
import numpy as np
import struct
from scipy import signal, integrate
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
    t=t[0:60]
    f_p = np.concatenate([np.linspace(2000, 8000, 30), np.linspace(8000,2000, 30)])
    preamble_signal = (np.sin(2*np.pi*integrate.cumtrapz(f_p, t))).astype(np.float32)
    return preamble_signal

def Check(data):
    length=len(data)
    data_use=struct.unpack('f'*int(length/4),data)
    corr=signal.correlate(data_use,pream,mode='full',method='fft')
    check_num=0
    # plt.plot(corr)
    # plt.show()
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

def DealWithError_Play():
    KillThread(t_send)
    exit()

def Send(P):
    #Read the file "INPUT.bin"
    f = open("INPUT.bin","rb")
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
                    stream.write(signal_1.tobytes())
                elif k=='0':
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
                    stream.write(signal_1.tobytes())
                elif k=='0':
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

def Response(P):
    global stream
    i=0
    respon_times=0
    TIME=1
    FIND_1=8000
    print("*start send response: ")
    stream = P.open(format=Format,channels=channels,rate=fs,input=True,frames_per_buffer=chunk)
    while i<n_frame:
        if respon_times>2+1:
            print("link error!")
            exit()
        t=0
        frames = []
        for w in range(0, int(fs / chunk * TIME)):
            data = stream.read(chunk)
            frames.append(data)

            t+=chunk/4
            if t>FIND_1 and t<FIND_1+57000 and Check(data)==True:
                print("link error!")
                print("Error at time: "+str(t))
                DealWithError_Play()
        else:
            continue
        stream.stop_stream()
        stream.close()
        frames=b''.join(frames)
        # 调试用，展示整个信号和preamble的相干性
        # sig = np.asarray(struct.unpack('f'*int(len(frames)/4),frames))
        # res=signal.correlate(sig,pream,mode='full',method='fft')
        # plt.plot(res)
        # plt.show()

        #Decode head
        sig_to_find_head = frames[:FIND_1*4]
        sig_to_find_head = np.asarray(struct.unpack('f'*FIND_1,sig_to_find_head))
        pointer_add=PointerBeforeHead_1(sig_to_find_head,pream,length_head-1)
        if pointer_add==-1000:
            print("S:-1000 "+str(i)+" for response: "+str(respon_times))
            #Resend
            respon_times+=1
            sema.release()
            continue
        pointer=0+(pointer_add+length_head)*4
        #Decode data
        integer=-1
        decode_str=str()
        for j in range(2):
            data = frames[pointer:pointer+length_sig*4]
            pointer+=length_sig*4
            sig = np.asarray(struct.unpack('f'*length_sig,data))
            sig_mul=sig*signal_0
            str1=FindNumberAvr(sig_mul)
            decode_str=decode_str+str1
            if j==1:
                integer=int(decode_str,2)
        if integer==i%4:
            print("send success! "+str(i)+" for response: "+str(respon_times))
            respon_times=0
            sema.release()
        else:
            print("Wrong response "+str(i)+" for response: "+str(respon_times))
            print(str(integer)+" "+str(i%4))
            #Resend
            sema.release()

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


time_start=time.time()

#变量声明
p = pyaudio.PyAudio()
fs = 48000
seconds = 0.0001
f = 6000
channels = 1
Format = pyaudio.paFloat32
chunk = 1024
length_str=6250
length_frame=50
ADD=1000  #调试用，增加一段ADD个信号长度的没用的信号(耗时0.01s)
more_time=0.5 #调试用，多录制的时间

pream=Preamble()
signal_0 = (np.sin(2*np.pi*f*np.arange(0,seconds,1/fs))).astype(np.float32)
signal_1 = (-np.sin(2*np.pi*f*np.arange(0,seconds,1/fs))).astype(np.float32)
length_head=len(pream)
length_sig=len(signal_0)
n_frame = int(length_str/length_frame)

t_send=threading.Thread(target=Send, args=(p,))
t_response=threading.Thread(target=Response, args=(p,))

t_response.start()
t_send.start()
t_send.join()

time.sleep(3)
if t_response.isAlive():
    print("*end send response: ")
    KillThread(t_response)

    p.terminate()
    time_end=time.time()
    print("Time is: "+str(time_end-time_start))
else:
    exit()