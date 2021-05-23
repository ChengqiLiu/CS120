import socket 
import time             
 
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
host='192.168.43.105'
print(host)
port=12377

s.bind((host,port))
for i in range(10):
    print(str(i+1)+":")
    data, addr = s.recvfrom(20)
    print("IP: %s, Port: %d" %(addr[0],addr[1]))
    print("Payload: "+str(data))
    time.sleep(1)

s.close()
