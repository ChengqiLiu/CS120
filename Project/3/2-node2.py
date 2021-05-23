import pyaudio
import wave
import sys
import numpy as np
import struct
from scipy import signal,integrate
import matplotlib.pyplot as plt
import threading
import time
import socket
#自己播放自己接收（最棒的！）

def int_to_str(num,length):
    b_n=bin(num)[2:]
    len_0=length-len(b_n)
    return len_0*'0'+b_n

def ip_to_str(stri):
    spl=stri.split('.')
    ret=""
    for i in spl:
        ret=ret+int_to_str(int(i),8)
    return ret

def byte_to_str(byte):
    temp=int.from_bytes(byte,'big')
    b=bin(temp)[2:]
    len_add=8-len(b)
    return len_add*"0"+b

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
        if corr[i]>40:
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

def Write(Filename,str1):
    with open(Filename, 'ab') as file_object:
        file_object.write(str1)

def GetLengthInput(str1):
    global length_str
    """Get  length_str of the file str1"""
    file_temp=open(str1,"rb")
    read_temp=file_temp.read()
    length_str=len(read_temp)

def Record():
    '''Record audio.'''
    global s
    stream = p.open(format=Format,
                channels=channels,
                rate=fs,
                input=True,
                frames_per_buffer=chunk)

    print("* recording")
    frames = []
    for i in range(0, int(fs / chunk * record_time)):
        data = stream.read(chunk)
        frames.append(data)
    # print("* done recording")
    
    stream.stop_stream()
    stream.close()

    #Decode
    frames=b''.join(frames)
    frames = np.asarray(struct.unpack('f'*int(len(frames)/4),frames))
    FIND_1=80000
    FIND_2=50
    #调试用，使解码文件改为播放的文件，而非录制的
    # filename_r="3.wav"

    CleanFile("OUTPUT.txt")
    
    #调试用，去掉开头的一段数据再解码
    # wf.setpos(5000)
    # 调试用，展示整个信号和preamble的相干性
    # res=signal.correlate(frames,pream,mode='full',method='fft')
    # plt.plot(res)
    # plt.show()
    # 调试用，实时纠错
    # fin = open("INPUT.bin","rb")
    # read=fin.read()
    # bytes_in=struct.unpack(len(read)*'c',read)

    #Decode IP and port
    pointer=0
    pointer_tell=pointer
    sig_to_find_head = frames[pointer:pointer+FIND_1]
    pointer_add=PointerBeforeHead_1(sig_to_find_head,pream,length_head-1)
    pointer=pointer_tell+(pointer_add+length_head)
    #IP
    decode_str=""
    for i in range(32):
        sig = frames[pointer:pointer+length_sig]
        pointer+=length_sig
        sig_mul=sig*signal_0
        str1=FindNumberAvr(sig_mul)
        decode_str=decode_str+str1
    ip_temp=""
    for i in range(4):
        integer=int(decode_str[8*i:8*(i+1)],2)
        ip_temp=ip_temp+str(integer)
        if i==3:
            break
        else:
            ip_temp=ip_temp+"."
    print(ip_temp)
    s.sendto(ip_temp.encode(),(host_3,port_3))
    time.sleep(0.1)
    #Port
    decode_str=""
    for i in range(16):
        sig = frames[pointer:pointer+length_sig]
        pointer+=length_sig
        sig_mul=sig*signal_0
        str1=FindNumberAvr(sig_mul)
        decode_str=decode_str+str1
    port_temp=int(decode_str,2)
    # print(port_temp)
    s.sendto(str(port_temp).encode(),(host_3,port_3))
    time.sleep(0.1)
    #Data
    send_str=b''
    for i in range(n_frame):
        #save the file pointer
        pointer_tell=pointer
        #decode the preamble`
        sig_to_find_head = frames[pointer:pointer+FIND_2]
        pointer_add=PointerBeforeHead(sig_to_find_head,pream,length_head-1)
        pointer=pointer_tell+(pointer_add+length_head)
        #decode
        for j in range(i*length_frame,(i+1)*length_frame):
            decode_str=str()
            for k in range(8):
                sig = frames[pointer:pointer+length_sig]
                pointer+=length_sig
                sig_mul=sig*signal_0
                str1=FindNumberAvr(sig_mul)
                decode_str=decode_str+str1
            
            #调试用，实时纠错
            # stand=byte_to_str(bytes_in[j])
            # if decode_str!=stand:
            #     print("id: "+str(j))
            #     print("decode: "+decode_str)
            #     print("stand: "+stand)
            integer=int(decode_str,2)
            w_byte=integer.to_bytes(1, 'big')
            Write("OUTPUT.txt",w_byte)
            send_str=send_str+w_byte
            if w_byte==b'\n' :
                s.sendto(send_str,(host_3,port_3))
                # print(send_str)
                send_str=b''
                time.sleep(0.1)
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
            decode_str=str()
            for k in range(8):
                sig = frames[pointer:pointer+length_sig]
                pointer+=length_sig
                sig_mul=sig*signal_0
                str1=FindNumberAvr(sig_mul)
                decode_str=decode_str+str1
        
            integer=int(decode_str,2)
            w_byte=integer.to_bytes(1, 'big')
            Write("OUTPUT.txt",w_byte)
            send_str=send_str+w_byte
            if w_byte==b'\n':
                s.sendto(send_str,(host_3,port_3))
                # print(send_str)
                send_str=b''
                time.sleep(0.1)
    #测试用，已作废代码
    # s.sendto(send_str,(host_3,port_3))
         
def Play():
    '''Play audio.'''
    global s
    #Read the file "INPUT.txt"
    data, addr = s.recvfrom(20)
    host_1=data.decode()
    data, addr = s.recvfrom(20)
    port_1=int(data.decode())

    bytes_in=[]
    for i in range(30):
        data, addr = s.recvfrom(50)
        data_arr=struct.unpack('c'*len(data),data)
        # print(data)
        bytes_in.extend(data_arr)

    stream = p.open(format=Format,
                channels=channels,
                rate=fs,
                output=True)

    print("* playing")
    #调试用，增加一段ADD个信号长度的没用的信号
    for i in range(ADD):
        stream.write(signal_0.tobytes())

    #IP and port
    stream.write(pream.tobytes())
    ip_str=ip_to_str(host_1)
    for i in ip_str:
        if i=='0':
            stream.write(signal_0.tobytes())
        else:
            stream.write(signal_1.tobytes())
    port_str=int_to_str(port_1,16)
    for i in port_str:
        if i=='0':
            stream.write(signal_0.tobytes())
        else:
            stream.write(signal_1.tobytes())
    
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
    # print("* done playing")


time_start=time.time()
#变量声明
p = pyaudio.PyAudio()
fs = 48000
seconds = 0.0006
f = 6000
channels = 1
Format = pyaudio.paFloat32
chunk = 1024
length_str=0
length_frame=20
ADD=500 #调试用，增加一段ADD个信号长度的没用的信号(耗时ADD*seconds)
more_time=0.3 #调试用，多录制的时间

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
socket.setdefaulttimeout(10)
host_2="192.168.43.105"
port_2=12122
host_3="192.168.43.77"
port_3=12122
s.bind((host_2,port_2))
print("host2: "+host_2)

#get length_str
GetLengthInput("INPUT.txt")
# print(length_str)

pream=Preamble()
length_head=len(pream)
signal_0=(np.sin(2*np.pi*f*np.arange(0,seconds,1/fs))).astype(np.float32)
signal_1=(-np.sin(2*np.pi*f*np.arange(0,seconds,1/fs))).astype(np.float32)
length_sig=len(signal_0)
n_frame = int(length_str/length_frame)

record_time=seconds*(length_str*8/length_frame*(10+length_frame)+ADD)+more_time
play_file="INPUT.bin"

Record()
Play()
time.sleep(5)

p.terminate()
s.close()

print("* Finish.")
time_end=time.time()
print("Time is: "+str(time_end-time_start))
