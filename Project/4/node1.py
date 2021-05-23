import pyaudio
import wave
import sys
import numpy as np
import struct
from scipy import signal,integrate
import matplotlib.pyplot as plt
import threading
import time


def byte_to_str(byte):
    temp=int.from_bytes(byte,'big')
    b=bin(temp)[2:]
    len_add=8-len(b)
    return len_add*"0"+b

def num_to_str(num,bits):
    b=bin(num)[2:]
    len_add=bits-len(b)
    return len_add*"0"+b

def arr_to_str(arr):
    str_ret=str()
    for i in arr:
        if i==0:
            str_ret=str_ret+'0'
        elif i==1:
            str_ret=str_ret+'1'
        else:
            print("ERROR_arr_to_str")
    return str_ret

def Preamble():
    '''Generate preamble signal.'''
    t = np.linspace(0,1, 48000,endpoint = True,dtype = np.float32)
    t=t[0:120]
    f_p = np.concatenate([np.linspace(2000, 8000, 60), np.linspace(8000,2000, 60)])
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
        if corr[i]>33:
            res=i
            break
    ret=res-length_head
    # print(ret)
    return ret

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
    if sum!=0:
        # print("wrong data: "+str(sum-1)) #调试用
        if sum<len(data):
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
    # print(len(array))
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

def Receive(P,record_time,write_file=False,path=""):
    if write_file:
        CleanFile(path)
        fp=open(path,'ab')
    else:
        str_ret=b""

    FIND_1=80000
    FIND_2=50

    stream = P.open(format=Format,channels=channels,rate=fs,input=True,frames_per_buffer=chunk)

    print("*Start receive")
    frames = []
    for i in range(0, int(fs / chunk * record_time)):
        data = stream.read(chunk)
        frames.append(data)
    # print("*End receive")
    
    stream.stop_stream()
    stream.close()

    #Decode
    frames=b''.join(frames)
    FIND_1=len(frames)
    frames = np.asarray(struct.unpack('f'*int(len(frames)/4),frames))
    

    # wn=2*8000/fs
    #另一种思路
    # b, a = signal.butter(12, wn, 'highpass')
    # frames = signal.filtfilt(b, a, frames)
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

    #decode the preamble`
    pointer=0
    sig_to_find_head = frames[pointer:pointer+FIND_1]
    pointer_add=PointerBeforeHead_1(sig_to_find_head,pream,length_head-1)
    pointer=(pointer_add+length_head)
    #length
    decode_str=str()
    for i in range(32):
        sig = frames[pointer:pointer+length_sig]
        pointer+=length_sig
        sig_mul=sig*signal_0
        str1=FindNumberAvr(sig_mul)
        decode_str=decode_str+str1
    length_str=int(decode_str,2)
    # print("len:  ",length_str)
    n_frame=int(length_str/length_frame)
    #data
    for i in range(n_frame):
        #save the file pointer
        pointer_tell=pointer
        #decode the preamble`
        sig_to_find_head = frames[pointer:pointer+FIND_2]
        pointer_add=PointerBeforeHead(sig_to_find_head,pream,length_head-1)
        pointer=pointer_tell+(pointer_add+length_head)
        #decode
        for j in range(i*length_frame,(i+1)*length_frame):
            arr=[]
            for k in range(12):
                sig = frames[pointer:pointer+length_sig]
                pointer+=length_sig
                sig_mul=sig*signal_0
                str1=FindNumberAvr(sig_mul)
                arr.append(int(str1))
                
            decode_arr=HammingDecode(arr)
            decode_str=arr_to_str(decode_arr)
            integer=int(decode_str,2)
            w_byte=integer.to_bytes(1, 'big')
            if write_file:
                fp.write(w_byte)
            else:
                str_ret=str_ret+w_byte
    #tail
    if length_str-length_frame*n_frame !=0:
        #save the file pointer
        pointer_tell=pointer
        #decode the preamble
        sig_to_find_head = frames[pointer:pointer+FIND_2]
        pointer_add=PointerBeforeHead(sig_to_find_head,pream,length_head-1)
        pointer=pointer_tell+(pointer_add+length_head)
        #decode
        for j in range(length_frame*n_frame,length_str):
            arr=[]
            for k in range(12):
                sig = frames[pointer:pointer+length_sig]
                pointer+=length_sig
                sig_mul=sig*signal_0
                str1=FindNumberAvr(sig_mul)
                arr.append(int(str1))
                
            decode_arr=HammingDecode(arr)
            decode_str=arr_to_str(decode_arr)
            integer=int(decode_str,2)
            w_byte=integer.to_bytes(1, 'big')
            if write_file:
                fp.write(w_byte)
            else:
                str_ret=str_ret+w_byte

    if write_file:
        fp.close()
        return None
    # print(str_ret.decode("utf8","ignore"))
    return str_ret.decode("utf8","ignore")

def Send_byte(P,bytes_in):
    length_str=len(bytes_in)
    n_frame=int(length_str/length_frame)
    
    stream = P.open(format=Format,channels=channels,rate=fs,output=True)

    print("*Start send")
    #Play the preamble
    #length
    stream.write(pream.tobytes())
    str_l=num_to_str(length_str,32)
    for i in str_l:
        if i=="1":
            stream.write(signal_1.tobytes())
        elif i=="0":
            stream.write(signal_0.tobytes())
        else:
            print("error!")
            exit(1)
    #data
    for i in range(n_frame):
        #Play the preamble
        stream.write(pream.tobytes())
        for j in range(i*length_frame,(i+1)*length_frame):
            str_temp=byte_to_str(bytes_in[j])
            str_temp=HammingCode(str_temp,8)
            for k in str_temp:
                if k==1:
                    stream.write(signal_1.tobytes())
                elif k==0:
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
            str_temp=HammingCode(str_temp,8)
            for k in str_temp:
                if k==1:
                    stream.write(signal_1.tobytes())
                elif k==0:
                    stream.write(signal_0.tobytes())
                else:
                    print("error!")
                    exit(1)
    #调试用，增加一段ADD个信号长度的没用的信号
    # for i in range(ADD):
    #     stream.write(signal_0.tobytes())
    # print("*Finish send")
    stream.stop_stream()
    stream.close()

def Send(P,str_send):
    time.sleep(1)
    bytes_in=[e.encode() for e in str_send]
    Send_byte(P,bytes_in)

def Send_file(P,path):
    f=open(path,"rb")
    read=f.read()
    bytes_in=struct.unpack(length_str*'c',read)
    Send_byte(P,bytes_in)
    f.close()


#变量声明
p = pyaudio.PyAudio()
fs = 48000
seconds = 0.0002
f = 6000
channels = 1
Format = pyaudio.paFloat32
chunk = 1024
length_frame=10

pream=Preamble()
signal_0 = (np.sin(2*np.pi*f*np.arange(0,seconds,1/fs))).astype(np.float32)
signal_1 = (-np.sin(2*np.pi*f*np.arange(0,seconds,1/fs))).astype(np.float32)
length_head=len(pream)
length_sig=len(signal_0)

while True:
    str_in=input("Please input:\n")
    l_in=str_in.split(" ")
    l_in=[e for e in l_in if e !=""]
    if l_in[0]=="USER":
        Send(p,str_in)
        time.sleep(2)
        print(Receive(p,3))
        continue
    elif l_in[0]=="PASS":
        Send(p,str_in)
        time.sleep(2)
        print(Receive(p,3))
        continue
    elif l_in[0]=="HOST":
        Send(p,str_in)
        time.sleep(3)
        print(Receive(p,3))
        continue
    elif l_in[0]=="CONNECT":
        Send(p,str_in)
        time.sleep(3)
        str_g=Receive(p,7)
        if str_g=="exit":
            print("Error Connection!")
            exit()
        print(str_g)
    elif l_in[0]=="PWD":
        Send(p,str_in)
        time.sleep(1)
        print(Receive(p,3))
        continue
    elif l_in[0]=="CWD":
        Send(p,str_in)
        time.sleep(1)
        print(Receive(p,4))
        continue
    elif l_in[0]=="LIST":
        Send(p,str_in)
        input("Press enter to start transmission:\n")
        print(Receive(p,8))
        continue
    elif l_in[0]=="PASV":
        Send(p,str_in)
        time.sleep(1)
        print(Receive(p,3))
        continue
    elif l_in[0]=="RETR":
        Send(p,str_in)
        input("Press enter to start transmission:\n")
        Receive(p,15,True,l_in[2])
    elif l_in[0]=="TEST":
        Send(p,str_in)
        input("Press enter to start transmission:\n")
        print(Receive(p,5))
        continue
    elif l_in[0]=="QUIT":
        Send(p,str_in)
        break