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
import select
import os

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

def byte_to_str(byte,n_byte=1):
    temp=int.from_bytes(byte,'big')
    b=bin(temp)[2:]
    len_add=8*n_byte-len(b)
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
    global host_p
    host_p=ip_temp
    #Data
    
    global send
    for i in range(10):
        #save the file pointer
        pointer_tell=pointer
        #decode the preamble`
        sig_to_find_head = frames[pointer:pointer+FIND_2]
        pointer_add=PointerBeforeHead(sig_to_find_head,pream,length_head-1)
        pointer=pointer_tell+(pointer_add+length_head)
        #decode
        send_str=b""
        for j in range(24):
            decode_str=""
            for k in range(8):
                sig = frames[pointer:pointer+length_sig]
                pointer+=length_sig
                sig_mul=sig*signal_0
                str1=FindNumberAvr(sig_mul)
                decode_str=decode_str+str1
            
            integer=int(decode_str,2)
            w_byte=integer.to_bytes(1, 'big')
            send_str=send_str+w_byte
        send.append(send_str)
        # print(send_str)

def Play():
    stream = p.open(format=Format,
                channels=channels,
                rate=fs,
                output=True)

    # print("* playing")
    #调试用，增加一段ADD个信号长度的没用的信号
    for i in range(ADD):
        stream.write(signal_0.tobytes())
    #Data
    global times
    for i in range(10):
        #Play the preamble
        stream.write(pream.tobytes())
        #time slot
        t_d=struct.pack('d',times[i])
        t_str=byte_to_str(t_d,8)
        for s in t_str:
            if s=='1':
                stream.write(signal_1.tobytes())
            elif s=='0':
                stream.write(signal_0.tobytes())
            else:
                print("error!")
                exit(1)
        #bytes
        s_bytes=struct.unpack(24*"c",r_data[i])
        for j in s_bytes:
            str_temp=byte_to_str(j)
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

def CheskSum(data):
    """计算校验和，返回一个int16的整数"""
    n=len(data)
    m=n % 2
    sum=0
    for i in range(0, n - m ,2):
        sum += (data[i]) + ((data[i+1]) << 8)#传入data以每两个字节（十六进制）通过ord转十进制，第一字节在低位，第二个字节在高位
    if m:
        sum += (data[-1])
    #将高于16位与低16位相加
    sum = (sum >> 16) + (sum & 0xffff)
    sum += (sum >> 16) #如果还有高于16位，将继续与低16位相加
    answer = ~sum & 0xffff
    #  主机字节序转网络字节序列（参考小端序转大端序）
    answer = answer >> 8 | (answer << 8 & 0xff00)
    return answer

def Ping(host,send):
    """传输数据长度为24 bytes"""
    #由于windows 的默认长度是40 bytes，因此数据段大小应该是32 bytes，但是8个bytes被用于时间戳
    data_type = 8 # ICMP Echo Request
    data_code = 0 # must be zero
    data_ID = 0 #Identifier
    data_Sequence = 1 #Sequence number

    dst_addr = socket.gethostbyname(host)
    for i in range(10):
        payload_body=send[i]
        send_time = time.time()
        #初始打包成二进制数据
        icmp_packet = struct.pack('>BBHHHd24s',data_type,data_code,0,data_ID,data_Sequence+i,send_time,payload_body)
        #获取校验和
        icmp_chesksum = CheskSum(icmp_packet) 
        #把校验和传入，再次打包
        icmp_packet = struct.pack('>BBHHHd24s',data_type,data_code,icmp_chesksum,data_ID,data_Sequence+i,send_time,payload_body)

        rawsocket = socket.socket(socket.AF_INET,socket.SOCK_RAW,socket.getprotobyname("icmp"))
        rawsocket.sendto(icmp_packet,(dst_addr,80))#使用默认端口80

        global times, r_data
        while True:
            #实例化select对象，可读rawsocket，可写为空，可执行为空，超时时间
            what_ready = select.select([rawsocket], [], [])
            #没有返回可读的内容，判断超时
            if what_ready[0] == []:  # Timeout
                times.append(-1)
                break
            time_received = time.time()
            #接收包
            received_packet, addr = rawsocket.recvfrom(1024)
            icmpHeader=received_packet[20:28]
            received_t=received_packet[28:36]
            time_get=struct.unpack(">d", received_t)[0]
            r_data.append(received_packet[36:])
            #反转编码
            type_c, code, CheckSum, packet_id, sequence = struct.unpack(">BBHHH", icmpHeader)
            if type_c == 0 and sequence == data_Sequence+i:
                times.append(time_received-time_get)
                break

time_start=time.time()
#变量声明
p = pyaudio.PyAudio()
fs = 48000
seconds = 0.0006
f = 6000
channels = 1
Format = pyaudio.paFloat32
chunk = 1024
length_str=24*10
length_frame=24
ADD=1000 #调试用，增加一段ADD个信号长度的没用的信号(耗时ADD*seconds)
more_time=2 #调试用，多录制的时间
host_p=""
send=[]

pream=Preamble()
length_head=len(pream)
signal_0=(np.sin(2*np.pi*f*np.arange(0,seconds,1/fs))).astype(np.float32)
signal_1=(-np.sin(2*np.pi*f*np.arange(0,seconds,1/fs))).astype(np.float32)
length_sig=len(signal_0)
n_frame = int(length_str/length_frame)

record_time=seconds*(length_str*8/length_frame*(10+length_frame)+ADD)+more_time

Record()
print(host_p)
# print(send)
times=[]
r_data=[]
Ping(host_p,send)
# print(times)
Play()

p.terminate()

time_end=time.time()
# print("Time is: "+str(time_end-time_start))