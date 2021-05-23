import threading
import struct
import socket 
import time             

def CleanFile(Filename):
    File=open(Filename,'w')
    File.truncate()

def Write(Filename,str1):
    with open(Filename, 'ab') as file_object:
        file_object.write(str1)

def Receive():
    global s, g_buff, host_get, port_get
    print("* receiving")
    #Get IP and Port
    data, addr = s.recvfrom(20)
    host_get=addr[0]
    data, addr = s.recvfrom(20)
    port_get=int(data.decode())
    # print(host_get)
    # print(port_get)
    CleanFile("2-3.txt")

    #测试用，已作废代码
    # data, addr = s.recvfrom(1200)
    # buff=data.split(b'\n')
    # m_id=0
    # for i in buff:
    #     print(m_id+1)
    #     print("IP: %s, Port: %d" %(host_get,port_get))
    #     print("Payload: "+str(i+b'\n'))
    #     Write("2-3.txt",i+b'\n')

    for i in range(30):
        data, addr = s.recvfrom(1024)
        g_buff.append(data)
        print(i+1)
        print(data)
        Write("2-3.txt",data)
    # print("* done receiving")

def Send():
    global s
    # print("* sending")
    #IP
    s.sendto(host_3.encode(),(host_2,port_2))
    #Port
    s.sendto(str(port_3).encode(),(host_2,port_2)) 

    f=open("INPUT.txt","rb")
    read=f.read()
    length_str=len(read)
    bytes_in=struct.unpack(length_str*'c',read)
    #data
    # print(len(bytes_in))
    send_str=b''
    for i in bytes_in:
        send_str=send_str+i
        if i==b'\n' :
            s.sendto(send_str,(host_2,port_2))
            # print(send_str)
            send_str=b''
    # print("* done sending")

time_start=time.time()

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
host_3="192.168.43.77"
print("host_3: "+host_3)
port_3=12122
host_2="192.168.43.105"
port_2=12122
host_get=""
port_get=0

s.bind((host_3,port_3))
g_buff=[]

Receive()
Send()
time.sleep(5)
for i in range(30):
    print(i+1)
    print("IP: %s, Port: %d" %(host_get,port_get))
    print("Payload: "+str(g_buff[i]))
    time.sleep(0.1)

s.close()
time_end=time.time()
print("Time is: "+str(time_end-time_start))