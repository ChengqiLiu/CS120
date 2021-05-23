import socket
import time
import os

time_start=time.time()

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
host='192.168.43.105'
port=12377

for i in range(10):
    print(str(i+1)+":")
    rand_str=os.urandom(20)
    print("Send: "+str(rand_str))
    s.sendto(rand_str,(host,port))
    time.sleep(1)

s.close()
time_end=time.time()
print("Time is: "+str(time_end-time_start))