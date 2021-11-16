import enum
from pymediainfo import MediaInfo
import moviepy.editor as mp
from pydub import AudioSegment, silence
import matplotlib.pyplot as plt
from media.utils import validators

class Metadata(enum.Enum):

    def __new__(cls, value, descriptor=validators.BaseValidator, kwargs={}):
        obj = object.__new__(cls)
        obj._value_ = value
        obj.descriptor = descriptor
        obj.kwargs = kwargs
        return obj

    file_name = 'file_name', validators.StringValidator, {
        'min_length': 1, 
        'max_length': 99, 
        'valid_characters': '-_.() abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    }
    general_file_name = 'file_name'

    extension = 'extension', validators.StringValidator, {
        'min_length': 1, 
        'max_length': 5, 
        'valid_characters': '-_.() abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    }
    general_file_extension = 'extension'

    duration = 'duration', validators.IntValidator, {
        'min_value': 1, 
        'max_value': 360000000
    }
    general_duration = 'duration'

    date_created = 'date_created', validators.DateValidator, {
        'formats': (
            '%H:%M:%S %d/%m/%Y',
            '%Z %Y-%m-%d %H:%M:%S.%f'
        )
    }
    general_file_creation_date = 'date_created'

    dummy = 'dummy'


class MediaType(type):

    def __new__(mcls, name, bases, cls_dict):
        cls = super().__new__(mcls, name, bases, cls_dict)
        if hasattr(cls, 'metadata'):
            for prop in cls.metadata:
                descriptor = prop.descriptor(**prop.kwargs)
                descriptor.__set_name__(cls, prop.name)
                setattr(cls, prop.name, descriptor)
        return cls


class Media(metaclass=MediaType):
    
    def __init__(self, file_path):
        if hasattr(self, 'metadata'):
            self.file_path = file_path
            self.read_file_metadata(file_path)


    def read_file_metadata(self, file_path):
        parsed_metadata = MediaInfo.parse(file_path)
        for track in parsed_metadata.tracks:
            data = track.to_data()
            for property in data:
                name = track.track_type.lower() + '_' + property
                try:
                    if Metadata[name] in self.metadata:
                        setattr(self, Metadata[name].value, data[property])
                except KeyError:
                    pass
        
        for prop in self.metadata:
            validators.BaseValidator.validate_exists(prop, getattr(self, prop.value))


class Video(Media):

    metadata = (Metadata.file_name, Metadata.extension, Metadata.duration, Metadata.date_created)

    def extract_audio(self) -> 'Audio':
        clip = mp.VideoFileClip(self.file_path)
        new_filename = self.file_name + ".wav"
        clip.audio.write_audiofile(new_filename)
        return Audio(new_filename)


class Audio(Media):
    
    metadata = (Metadata.file_name, Metadata.extension, Metadata.duration, Metadata.date_created)

    def convert_audio(self, desired_format:str) -> 'Audio':
        clip = mp.AudioFileClip(self.file_path)
        new_filename = self.file_name + '.' + desired_format.rstrip('.')
        clip.write_audiofile(new_filename)
        return Audio(new_filename)

    @property
    def sound_intervals(self):
        if not hasattr(self, '_sound_intervals'):
            self.get_sound_intervals()
        return self._sound_intervals['intervals']

    def get_sound_intervals(self, min_sound_len:int=500, min_silence_len:int=500, silence_thresh:int=-24, seek_step:int=10):
        if not hasattr(self, '_sound_intervals') or self._sound_intervals['args'] != (min_sound_len, min_silence_len, silence_thresh, seek_step):
            segment = AudioSegment.from_file(self.file_path)
            raw_intervals = silence.detect_nonsilent(segment, min_silence_len, silence_thresh, seek_step)
            self._sound_intervals = {
                'intervals': [inter for inter in raw_intervals if inter[1] - inter[0] >= min_sound_len],
                'args': (min_sound_len, min_silence_len, silence_thresh, seek_step)
            }
        return self.sound_intervals

    def plot_silence(self, min_sound_len:int=500, min_silence_len:int=500, silence_thresh:int=-24, seek_step:int=10):
        intervals = self.get_sound_intervals(min_sound_len, min_silence_len, silence_thresh, seek_step)
        xvals = [0]
        yvals = [0]
        for inter in intervals:
            xvals.extend([inter[0],inter[0],inter[1],inter[1]])
            yvals.extend([0,1,1,0])
        xvals.append(self.duration)
        yvals.append(0)
        plt.plot(xvals, yvals)
        plt.show()