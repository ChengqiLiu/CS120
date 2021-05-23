import matplotlib.pyplot as plt

fin=open("INPUT1to2.bin", "rb")
fout=open("OUTPUT1to2.bin", "rb")
strin=fin.read()
strout=fout.read()
length_str=len(strin)
count=0
wrong_num=0
wrong_list=list()
pl=[]
for i in range(length_str):
    if i>=len(strout):
        print("Error length!")
        print(len(strout))
        break
    if strin[i]==strout[i]:
        count+=1
        pl.append(0)
    else:
        wrong_num+=1
        wrong_list.append(i)
        pl.append(1)
print(str(count/length_str*100)+"%")
print("Number of wrong: "+str(wrong_num))
# if wrong_num!=0:
#     print(wrong_list)
plt.plot(pl)
plt.show()
