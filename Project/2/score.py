fin=open("INPUT.bin", "rb")
fout=open("OUTPUT.bin", "rb")
strin=fin.read()
strout=fout.read()
length_str=len(strin)
count=0
wrong_num=0
wrong_list=list()
for i in range(length_str):
    if i>=len(strout):
        print("Error length!")
        print(len(strout))
        break
    if strin[i]==strout[i]:
        count+=1
    else:
        wrong_num+=1
        wrong_list.append(i)
print(str(count/length_str*100)+"%")
print("Number of wrong: "+str(wrong_num))
# if wrong_num!=0:
#     print(wrong_list)
