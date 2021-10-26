import sys
from pymediainfo import MediaInfo
import moviepy.editor as mp
from pprint import pprint
import matplotlib.pyplot as plt
import numpy as np
import subprocess as sp
from pydub import AudioSegment, silence


class Audio:
    
    def __init__(self, file:'str') -> None:
        self.meta = {}
        # Use pymediainfo to get the metadata for a file.
        # The relevant metadata is picked from the appropriate 'tracks' and added to the object as a dict.
        try:
            self.meta['file_name'] = file
            self.meta['name'], self.meta['extension'] = file.rsplit('.', 1)
            self.full_metadata = MediaInfo.parse(file)
            for track in self.full_metadata.tracks:
                data = track.to_data()
                if track.track_type == "General":
                    self.meta['duration'] = data['duration']
                    self.meta['file_size'] = data['file_size']
                    self.meta['format'] = data['format']
                    self.meta['date_created'] = data['file_creation_date']

                elif track.track_type == "Audio":
                    self.meta['bit_rate'] = data['bit_rate']
                    self.meta['sampling_rate'] = data['sampling_rate']
        except KeyError as key:
            raise KeyError("{} could not be found in the metadata for file '{}'".format(key, file))
        except:
            raise Exception("Metadata for file '{}' could not be parsed or is missing".format(file))

        # Check file name for correct type, length and illegal filename characters
        if not isinstance(self.meta['file_name'], str):
            raise TypeError("File name is not a string for file '{}'".format(file))
        if len(self.meta['file_name']) > 256:
            raise ValueError("File name is longer than the maximum 256 characters for file '{}'".format(file))
        valid_filename_chars = '-_.() abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        for c in self.meta['file_name']:
            if not c in valid_filename_chars:
                raise ValueError("File name contains illegal character '{}' for file '{}'".format(c, file))

        # Check duration for correct type and range
        if not isinstance(self.meta['duration'], int):
            raise TypeError("Duration is not an integer for file '{}'".format(file))
        if not self.meta['duration'] in range(360000000):  # Max duration of 100 hours.
            raise ValueError("Duration is not between 0 and 100 hours for file '{}'".format(file))

        # Check creation date for correct type
        if not isinstance(self.meta['date_created'], str):
            raise TypeError("Creation date is not a string for file '{}'".format(file))

    def print_metadata(self, *args:'str') -> None:
        """Prints the requested metadata, or all if not specified."""
        if args:
            for arg in args:
                try:
                    print("{}: {}".format(arg, self.meta[arg]))
                except KeyError as err:
                    print("{} is not included in the metadata.".format(err))
        else:
            for k,v in self.meta.items():
                print("{}: {}".format(k,v))

    def get_sound_intervals(self, min_sound_len:'int'=500, min_silence_len:'int'=500, silence_thresh:'int'=-24, seek_step:'int'=10) -> list:
        """Returns a list of sound intervals (a list containing a start and an end time in milliseconds)."""
        # If sound intervals weren't already generated, do so and save them to the object
        if not (hasattr(self, 'sound_intervals') and self.sound_intervals['attr'] == [min_sound_len, min_silence_len, silence_thresh, seek_step]):
            self.sound_intervals = {'attr': [min_sound_len, min_silence_len, silence_thresh, seek_step]}
            segment = AudioSegment.from_file(self.meta['file_name'])
            raw_intervals = silence.detect_nonsilent(segment, min_silence_len, silence_thresh, seek_step)
            self.sound_intervals['intervals'] = [inter for inter in raw_intervals if inter[1] - inter[0] >= min_sound_len]
        return self.sound_intervals

    def plot_silence(self, *args, **kwargs) -> None:
        """Generates a pyplot showing sound and silence."""
        intervals = self.get_sound_intervals(*args, **kwargs)['intervals']
        xvals = [0]
        yvals = [0]
        for inter in intervals:
            if inter[1] - inter[0] >= 500:
                xvals.extend([inter[0],inter[0],inter[1],inter[1]])
                yvals.extend([0,1,1,0])
        xvals.append(self.meta['duration'])
        yvals.append(0)
        plt.plot(xvals, yvals)
        plt.show()


def get_duration(file):
    media_info = MediaInfo.parse(file)
    return media_info.tracks[0].to_data()['duration']

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


def plot_silence(file):
    # MAKE BETTER CHECK
    segment = AudioSegment.from_file(file)

    sound = silence.detect_nonsilent(segment, min_silence_len=500, silence_thresh=-24, seek_step=10)
    print(sound)
    xvals = [0]
    yvals = [0]
    for interval in sound:
        if interval[1] - interval[0] >= 500:
            xvals.append(interval[0])
            xvals.extend(interval)
            xvals.append(interval[1])
            yvals.extend([0,1,1,0])

    xvals.append(get_duration(file))
    yvals.append(0)
    print(xvals)
    print(yvals)
    plt.plot(xvals, yvals)
    plt.show()

    #command = ['ffmpeg', '-i', file, '-f', 'wav', '-']
    #pipe = sp.Popen(command, stdout=sp.PIPE, bufsize = 10**8)
    #raw = pipe.stdout.read(44100*30)
    #arr = np.fromstring(raw, dtype="int16")
    #print(arr)
    #print(len(raw))
    #print(len(arr))
    #plt.plot(arr)
    #plt.show()




def main(): 
    #get_metadata("30.09.21 SudwestFryslan Raad.wav")
    #extract_audio("30.09.21 SudwestFryslan Raad", "mp4", "mp3")
    #convert_audio("30.09.21 SudwestFryslan Raad", "mp3", "wav")
    #make_sound_array("sample.wav")
    #plot_silence('30.09.21 SudwestFryslan Raad.wav')
    test = Audio('sample.wav')
    print(test.meta)

if __name__ == '__main__':
    main()