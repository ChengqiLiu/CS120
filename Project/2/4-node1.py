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

def byte_to_str_8(byte):
    temp=int.from_bytes(byte,'big')
    b=bin(temp)[2:]
    len_add=64-len(b)
    return len_add*"0"+b

def Preamble():
    '''Generate preamble signal.'''
    t = np.linspace(0,1, 48000,endpoint = True,dtype = np.float32)
    t=t[0:30]
    f_p = np.concatenate([np.linspace(2000, 8000, 15), np.linspace(8000,2000, 15)])
    preamble_signal = (np.sin(2*np.pi*integrate.cumtrapz(f_p, t))).astype(np.float32)
    return preamble_signal

def Check(data):
    global p_num
    length=len(data)
    data_use=struct.unpack('f'*int(length/4),data)
    corr=signal.correlate(data_use,pream,mode='full',method='fft')
    p_num-=0.1
    for i in corr:
        if i>13:
            if p_num!=0:
                break
            return True
    return False

def Check_e(data):
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

def PointerBeforeHead(sig,reference,length_head):
    corr=signal.correlate(sig,reference,mode='full',method='fft')
    # 调试用，检验头是否对齐。使用的时候把plt和print三行代码注释掉。
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
        if corr[i]>7.4:
            res=i
            break
    ret=res-length_head
    # print(ret)
    return ret

def DealWithError_2(P):
    if t_send.isAlive():
        KillThread(t_send)
    exit()

def CleanFile(Filename):
    File=open(Filename,'w')
    File.truncate()

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

def Write(Filename,str1):
    with open(Filename, 'ab') as file_object:
        file_object.write(str1)

def Receive(P):
    '''Receive audio.'''
    FIND_1=50000
    FIND_2=50

    stream=P.open(format=Format,channels=channels,rate=fs,input=True,frames_per_buffer=chunk)

    frames=[]
    t=0
    t_temp=time.time()
    check_t=True
    print("*Start receive")
    for i in range(0, int(fs / chunk * record_time)):
        data=stream.read(chunk)
        frames.append(data)

        t+=chunk/4
        if  t>17000 and t<75000 and Check_e(data):
            print("link error!")
            print("Error at: "+str(t))
            DealWithError_2(P)
        if  Check(data) and check_t:
            t_temp=time.time()
            check_t=False
    # print("*End receive")
    
    stream.stop_stream()
    stream.close()

    #Decode
    frames=b''.join(frames)
    CleanFile("OUTPUT.bin")
    
    # 调试用，展示整个信号和preamble的相干性
    # sig=np.asarray(struct.unpack('f'*int(len(frames)/4),frames))
    # res=signal.correlate(sig,pream,mode='full',method='fft')
    # plt.plot(res)
    # plt.show()
    # 调试用，实时纠错
    # fin=open("INPUT.bin","rb")
    # read=fin.read()
    # bytes_in=struct.unpack(len(read)*'c',read)
    pointer=0
    for i in range(n_frame):
        #save the file pointer
        pointer_tell=pointer
        #decode the preamble`
        if i==0:
            sig_to_find_head=frames[pointer:pointer+FIND_1*4]
            sig_to_find_head=np.asarray(struct.unpack('f'*FIND_1,sig_to_find_head))
            pointer_add=PointerBeforeHead_1(sig_to_find_head,pream,length_head-1)
        else:
            sig_to_find_head=frames[pointer:pointer+FIND_2*4]
            sig_to_find_head=np.asarray(struct.unpack('f'*FIND_2,sig_to_find_head))
            pointer_add=PointerBeforeHead(sig_to_find_head,pream,length_head-1)
        pointer=pointer_tell+(pointer_add+length_head)*4
        #decode time
        decode_str=str()
        for s in range(64):
            data=frames[pointer:pointer+length_sig*4]
            pointer+=length_sig*4
            sig=np.asarray(struct.unpack('f'*length_sig,data))
            sig_mul=sig*signal_0
            str1=FindNumberAvr(sig_mul)
            decode_str=decode_str+str1
            if s==63:
                t_byte=int(decode_str,2).to_bytes(8,'big')
                t_d=struct.unpack('d',t_byte)[0]
                mac_time=t_d-t_temp
                TH=(length_frame+length_head)/mac_time/1000
                # print(t_d)
                if mac_time>4:
                    print("TIMEOUT!")
                elif mac_time<0.001 or mac_time!=mac_time:
                    # print("Decode error!")
                    pass
                else:
                    print("NODE1 TH: "+str(TH)+" kbps")
                    # print("mac_time: "+str(mac_time)+" s")
                if t_d> 1600000000 and t_d<1700000000:
                    t_temp=t_d
        #decode data
        for j in range(i*length_frame,(i+1)*length_frame):
            decode_str=str()
            for k in range(8):
                data=frames[pointer:pointer+length_sig*4]
                pointer+=length_sig*4
                sig=np.asarray(struct.unpack('f'*length_sig,data))
                sig_mul=sig*signal_0
                str1=FindNumberAvr(sig_mul)
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
                    Write("OUTPUT.bin",w_byte)
    #tail
    if length_str-length_frame*n_frame !=0:
        #save the file pointer
        pointer_tell=pointer
        #decode the preamble
        sig_to_find_head=frames[pointer:pointer+FIND_2*4]
        sig_to_find_head=np.asarray(struct.unpack('f'*FIND_2,sig_to_find_head))
        pointer_add=PointerBeforeHead(sig_to_find_head,pream,length_head-1)
        pointer=pointer_tell+(pointer_add+length_head)*4
        #decode
        for j in range(length_frame*n_frame,length_str):
            decode_str=str()
            for k in range(8):
                data=frames[pointer:pointer+length_sig*4]
                pointer+=length_sig*4
                sig=np.asarray(struct.unpack('f'*length_sig,data))
                sig_mul=sig*signal_0
                str1=FindNumberAvr(sig_mul)
                decode_str=decode_str+str1
                if k==7:
                    integer=int(decode_str,2)
                    w_byte=integer.to_bytes(1, 'big')
                    Write("OUTPUT.bin",w_byte)

def Send(P):
    #Read the file "INPUT.bin"
    f=open("INPUT.bin","rb")
    read=f.read()
    bytes_in=struct.unpack(length_str*'c',read)

    stream=P.open(format=Format,channels=channels,rate=fs,output=True)

    print("*Start send")
          
    for i in range(n_frame):
        #Play the preamble
        stream.write(pream.tobytes())
        #Play the time slot
        t=time.time()
        # print(t)
        t_d=struct.pack('d',t)
        t_str=byte_to_str_8(t_d)
        for s in t_str:
            if s=='1':
                stream.write(signal_1.tobytes())
            elif s=='0':
                stream.write(signal_0.tobytes())
            else:
                print("error!")
                exit(1)
        #play the data
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
    # print("*End send")


#变量声明
p=pyaudio.PyAudio()
fs=48000
seconds=0.0001
f=8000
channels=1
Format=pyaudio.paFloat32
chunk=1024
length_str=6250
length_frame=50
ADD=1000 #调试用，增加一段ADD个信号长度的没用的信号(耗时ADD*seconds)
more_time=1.5 #调试用，多录制的时间
n_frame=int(length_str/length_frame)

pream=Preamble()
signal_0=(np.sin(2*np.pi*f*np.arange(0,seconds,1/fs))).astype(np.float32)
signal_1=(-np.sin(2*np.pi*f*np.arange(0,seconds,1/fs))).astype(np.float32)
length_head=len(pream)
length_sig=len(signal_0)
p_num=length_frame
record_time=seconds*(n_frame*8*(length_head/length_sig+length_frame)+ADD)+more_time

t_receive=threading.Thread(target=Receive, args=(p,))
t_send=threading.Thread(target=Send, args=(p,))

t_receive.start()
time.sleep(1)#同步传输调整
t_send.start()
t_send.join()
t_receive.join()

p.terminate()

