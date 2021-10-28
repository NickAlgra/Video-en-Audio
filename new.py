from pymediainfo import MediaInfo
import moviepy.editor as mp
import matplotlib.pyplot as plt
from pydub import AudioSegment, silence

class Media:
    """A class for an media fragment.

    Attributes:
    meta (dict): contains the metadata of the file.

    Methods:
    print_metadata(): 
        Prints the requested metadata, or all if not specified.
    """
    
    def __init__(self, file:'str') -> None:
        """Initialises the metadata for the given file.

        Parameters:
        file (str): complete name of the file
        """
        self.meta = {}
        self.meta['file_name'] = file
        split_name = file.rsplit('.', 1)
        if len(split_name) < 2:
            raise ValueError("No extension found for file '{}'".format(file))
        self.meta['name'], self.meta['extension'] = split_name
        # Use pymediainfo to get the metadata for a file.
        # The relevant metadata is picked from the appropriate 'tracks' and added to the object as a dict.
        try:
            self.full_metadata = MediaInfo.parse(file)
            for track in self.full_metadata.tracks:
                data = track.to_data()
                if track.track_type == "General":
                    self.meta['duration'] = data['duration']
                    self.meta['file_size'] = data['file_size']
                    self.meta['format'] = data['format']
                    self.meta['date_created'] = data['file_creation_date']

                elif track.track_type == "Video":
                    self.meta['video_bit_rate'] = data['bit_rate']
                    self.meta['frame_rate'] = data['frame_rate']
                    self.meta['height'] = data['height']
                    self.meta['width'] = data['width']

                elif track.track_type == "Audio":
                    self.meta['audio_bit_rate'] = data['bit_rate']
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

    def print_metadata(self, *args:'list') -> None:
        """Prints the requested metadata, or all if not specified.

        Available metadata:
        General:
            file_name (str): complete name of the file.
            name (str): file name without extension.
            extension (str): extension of the file.
            duration (int): duration of the file in ms.
            file_size (int): size of the file in bytes.
            format (str): format of the file.
            date_created (str): date and time the file was created as "UCT YYYY-MM-DD hh:mm:ss.sss".

        Video:
            video_bit_rate (int): bit rate of the video in bps.
            frame_rate (float): frame rate of the video in fps.
            height (int): height of the video in px.
            width (int): width of the video in px.

        Audio:
            audio_bit_rate (int): bit rate of audio in bps.
            sampling_rate (int): sampling rate of audio in Hz
        """
        if args:
            for arg in args:
                try:
                    print("{}: {}".format(arg, self.meta[arg]))
                except KeyError as err:
                    print("{} is not included in the metadata.".format(err))
        else:
            for k,v in self.meta.items():
                print("{}: {}".format(k,v))


class Audio(Media):
    """A class for an audio fragment.

    Attributes:
    meta (dict): contains the metadata of the file.

    Methods:
    print_metadata(): 
        Prints the requested metadata, or all if not specified.
    get_sound_intervals(min_sound_len:'int'=500, min_silence_len:'int'=500, silence_thresh:'int'=-24, seek_step:'int'=10):
        Returns a list of sound intervals (a list containing a start and an end time in milliseconds).
    plot_silence(min_sound_len:'int'=500, min_silence_len:'int'=500, silence_thresh:'int'=-24, seek_step:'int'=10):
        Generates a pyplot showing sound and silence.
    convert_audio(desired_format:'str'):
        Converts the the audio to a new file in the desired format, and returns a new Audio object for the new file.
    """

    def convert_audio(self, desired_format:'str'):
        """Converts the the audio to a new file in the desired format, and returns a new Audio object for the new file.

        Parameters:
        desired_format (str): desired format of the new audio file, e.g. 'mp3'.

        Returns:
        Audio object: A new audio object for the newly made file.
        """
        clip = mp.AudioFileClip(self.meta['file_name'])
        new_filename = self.meta['name']+"."+desired_format.lstrip('.')
        clip.write_audiofile(new_filename)
        return Audio(new_filename)

    def get_sound_intervals(self, min_sound_len:'int'=500, min_silence_len:'int'=500, silence_thresh:'int'=-24, seek_step:'int'=10) -> list:
        """Returns a list of sound intervals (a list containing a start and an end time in milliseconds).
        
        Parameters:
        min_sound_len (int): minimum length in millisecond a sound interval has to be to be detected, defaulting to 500 ms.
        min_silence_len (int): minimum length in millisecond a silence interval has to be to be detected, defaulting to 500 ms.
        silence_thresh (int): the upper bound for how quiet is silent in dFBS.
        seek_step (int): step size for interating over the segment in ms.

        Returns:
        list[[start,end]]: the start and end timestamps of a sound segment, in ms.
        """

        # If sound intervals weren't already generated, do so and save them to the object
        if not (hasattr(self, 'sound_intervals') and self.sound_intervals['attr'] == [min_sound_len, min_silence_len, silence_thresh, seek_step]):
            self.sound_intervals = {'attr': [min_sound_len, min_silence_len, silence_thresh, seek_step]}
            segment = AudioSegment.from_file(self.meta['file_name'])
            raw_intervals = silence.detect_nonsilent(segment, min_silence_len, silence_thresh, seek_step)
            self.sound_intervals['intervals'] = [inter for inter in raw_intervals if inter[1] - inter[0] >= min_sound_len]
        return self.sound_intervals

    def plot_silence(self, *args, **kwargs) -> None:
        """Generates a pyplot showing sound and silence.

        Parameters:
        min_sound_len (int): minimum length in millisecond a sound interval has to be to be detected, defaulting to 500 ms.
        min_silence_len (int): minimum length in millisecond a silence interval has to be to be detected, defaulting to 500 ms.
        silence_thresh (int): the upper bound for how quiet is silent in dFBS.
        seek_step (int): step size for interating over the segment in ms.
        """

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


class Video(Media):
    """A class for an video fragment.

    Attributes:
    meta (dict): contains the metadata of the file.

    Methods:
    print_metadata(): 
        Prints the requested metadata, or all if not specified.
    extract_audio(desired_format:'str'):
        Extracts the audio and saves to a new file in the desired format, and returns a new Audio object.
    """

    def extract_audio(self, desired_format:'str'):
        """Extracts the audio and saves to a new file in the desired format, and returns a new Audio object.

        Parameters:
        desired_format (str): desired format of the new audio file, e.g. 'mp3'.

        Returns:
        Audio object: A new audio object for the newly made file.
        """
        clip = mp.VideoFileClip(self.meta['file_name'])
        new_filename = self.meta['name']+"."+desired_format.lstrip('.')
        clip.audio.write_audiofile(new_filename)
        return Audio(new_filename)


def main(): 
    pass

if __name__ == '__main__':
    main()