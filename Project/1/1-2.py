import pyaudio
import wave
import sys
import threading

def Record(Chunk,Format,Channels,Rate,Seconds,Filename,P):
    '''Record audio.'''
    stream = P.open(format=Format,
                channels=Channels,
                rate=Rate,
                input=True,
                frames_per_buffer=Chunk)

    print("* recording")
    frames = []
    for i in range(0, int(Rate / Chunk * Seconds)):
        data = stream.read(Chunk)
        frames.append(data)
    print("* done recording")

    stream.stop_stream()
    stream.close()

    wf = wave.open(Filename, 'wb')
    wf.setnchannels(Channels)
    wf.setsampwidth(P.get_sample_size(Format))
    wf.setframerate(Rate)
    wf.writeframes(b''.join(frames))
    wf.close()

def Play(Chunk,Filename,P):
    '''Play audio.'''
    wf = wave.open(Filename, 'rb')
    stream = P.open(format=P.get_format_from_width(wf.getsampwidth()),
                channels=wf.getnchannels(),
                rate=wf.getframerate(),
                output=True)

    data = wf.readframes(Chunk)

    print("* playing")
    while len(data)>0:
        stream.write(data)
        data = wf.readframes(Chunk)
    print("* done playing")

    stream.stop_stream()
    stream.close() 
    wf.close()

#Do the task
CHUNK = 1024
FORMAT = pyaudio.paFloat32
CHANNELS = 1
RATE = 48000
SECONDS = 12
FILENAME_1 = "1-2-play.wav" #the file to be played
FILENAME_2 = "1-2-record.wav" #the file to store the result

p = pyaudio.PyAudio()

t_record=threading.Thread(target=Record, args=(CHUNK,FORMAT,CHANNELS,RATE,SECONDS,FILENAME_2,p))
t_play=threading.Thread(target=Play, args=(CHUNK,FILENAME_1,p))

t_record.start()
t_play.start()
t_play.join()
t_record.join()

#Verification:
Play(CHUNK,FILENAME_2,p)

p.terminate()


#Works Cited:
#https://stackoverflow.com/questions/8299303/generating-sine-wave-sound-in-python
#https://blog.csdn.net/cdlwhm1217096231/article/details/99704267 