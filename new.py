from pymediainfo import MediaInfo
import moviepy.editor as mp
from pprint import pprint
import matplotlib.pyplot as plt
import numpy as np
import subprocess as sp


def get_metadata(file):
    media_info = MediaInfo.parse(file)
    for track in media_info.tracks:
        if track.track_type == "General":
            print("General Track data:")
            pprint(track.to_data())
        elif track.track_type == "Video":
            print("Video Track data:")
            pprint(track.to_data())
        elif track.track_type == "Audio":
            print("Audio Track data:")
            pprint(track.to_data())


def extract_audio(filename, inputformat, outputformat):
    clip = mp.VideoFileClip(filename+"."+inputformat)
    clip.audio.write_audiofile(filename+"."+outputformat)


def convert_audio(filename, inputformat, outputformat):
    clip = mp.AudioFileClip(filename+"."+inputformat)
    clip.write_audiofile(filename+"."+outputformat)


def detect_silence(file):
    command = ['ffmpeg', '-i', file, '-f', 'wav', '-']
    pipe = sp.Popen(command, stdout=sp.PIPE, bufsize = 10**8)
    raw = pipe.stdout.read(44100*30)
    arr = np.fromstring(raw, dtype="int16")
    print(arr)
    print(len(raw))
    print(len(arr))
    plt.plot(arr)
    plt.show()




def main(): 
    #get_metadata("30.09.21 SudwestFryslan Raad.mp4")
    #extract_audio("30.09.21 SudwestFryslan Raad", "mp4", "mp3")
    #convert_audio("30.09.21 SudwestFryslan Raad", "mp3", "wav")
    #make_sound_array("sample.wav")
    detect_silence('sample.wav')

if __name__ == '__main__':
    main()