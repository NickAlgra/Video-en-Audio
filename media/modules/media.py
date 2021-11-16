import enum
from typing import Any
from pymediainfo import MediaInfo
import moviepy.editor as mp
from pydub import AudioSegment, silence
import matplotlib.pyplot as plt
from media.utils import validators

class Metadata(enum.Enum):
    """Enumeration containing supported types of metadata and their appropriate data descriptors."""
    def __new__(cls:type, name:str, descriptor:type=validators.BaseValidator, kwargs={}) -> 'Metadata':
        """Create a new Metadata member.

        Args:
            value (str): Name the attribute to store this metadata should have. Also used as _value_.
            descriptor (type, optional): Data descriptor classes should use to store this kind of
                metadata. Defaults to validators.BaseValidator.
            kwargs (dict, optional): Keyword arguments that should be passed when instantiating 
                the descriptor. Defaults to {}.

        Returns:
            Metadata: New Metadata member.
        """
        obj = object.__new__(cls)
        obj._value_ = name
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


class MediaType(type):
    """Metaclass for Media (sub)classes.
    
    For each Metadata in the class 'metadata' attribute, create a new data descriptor attribute
    using the descriptor type and arguments as specified in the Metadata enum.
    """
    def __new__(mcls, name, bases, cls_dict):
        cls = super().__new__(mcls, name, bases, cls_dict)
        if hasattr(cls, 'metadata'):
            for prop in cls.metadata:
                descriptor = prop.descriptor(**prop.kwargs)
                descriptor.__set_name__(cls, prop.name)
                setattr(cls, prop.name, descriptor)
        return cls


class Media(metaclass=MediaType):
    """Base class to represent media files.
    
    Args:
        file (str): File name (+ path).
    """
    def __init__(self, file:str) -> None:
        if hasattr(self, 'metadata'):
            self._file = file
            self.read_file_metadata(file)

    def __str__(self) -> str:
        return f"{type(self).__name__}({self.file})"

    def __repr__(self) -> str:
        return f"{type(self).__name__}(file='{self.file}')"

    @property
    def file(self) -> str:
        """str: File name (+ path) this object represents."""
        return self._file

    def read_file_metadata(self) -> None:
        """Parse and store metadata from file as specified in class metadata."""
        parsed_metadata = MediaInfo.parse(self.file)
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
    """Class to represent video files. 
    
    Attributes:
        metadata (tuple[Metadata]): The types of supported metadata.
    """
    metadata = (Metadata.file_name, Metadata.extension, Metadata.duration, Metadata.date_created)

    def extract_audio(self) -> 'Audio':
        """Extract the audio as a .wav file and save it under the same name.

        Returns:
            Audio: Audio object of the newly extracted audio file.
        """
        clip = mp.VideoFileClip(self.file)
        new_filename = self.file_name + ".wav"
        clip.audio.write_audiofile(new_filename)
        return Audio(new_filename)


class Audio(Media):
    """Class to represent audio files.
    
    Attributes:
        metadata (tuple[Metadata]): The types of supported metadata.
    """
    metadata = (Metadata.file_name, Metadata.extension, Metadata.duration, Metadata.date_created)

    def convert_audio(self, desired_format:str) -> 'Audio':
        """Convert the audio into the desired format and save it under the same name.

        Args:
            desired_format (str): The extension of the new audio file, e.g. 'mp3'.

        Returns:
            Audio: Audio object of the newly extracted audio file.
        """
        clip = mp.AudioFileClip(self.file)
        new_filename = self.file_name + '.' + desired_format.rstrip('.')
        clip.write_audiofile(new_filename)
        return Audio(new_filename)

    @property
    def sound_intervals(self) -> list[tuple[int, int]]:
        """list[tuple[int, int]]: Intervals in milliseconds where sound is present.
        
        If sound intervals are not currently cached, calls self.get_sound_intervals() to generate them.
        """
        if not hasattr(self, '_sound_intervals'):
            self.get_sound_intervals()
        return self._sound_intervals['intervals']

    def get_sound_intervals(self, min_sound_len:int=500, min_silence_len:int=500, silence_thresh:int=-24, seek_step:int=10) -> list[tuple[int, int]]:
        """Calculate intervals in milliseconds during where sound is present and store them in a cache.

        Args:
            min_sound_len (int, optional): Minimum length of a sound for it to be registered (in ms). Defaults to 500.
            min_silence_len (int, optional): Minimum length of silence for it to be registered (in ms). Defaults to 500.
            silence_thresh (int, optional): Upper bound for quietness of a silence (in dFBS). Defaults to -24.
            seek_step (int, optional): Step size for interating over the segment (in ms). Defaults to 10.

        Returns:
            list[tuple[int, int]]: Intervals in milliseconds where sound is present.
        """
        if not hasattr(self, '_sound_intervals') or self._sound_intervals['args'] != (min_sound_len, min_silence_len, silence_thresh, seek_step):
            segment = AudioSegment.from_file(self.file)
            raw_intervals = silence.detect_nonsilent(segment, min_silence_len, silence_thresh, seek_step)
            self._sound_intervals = {
                'intervals': [tuple(inter) for inter in raw_intervals if inter[1] - inter[0] >= min_sound_len],
                'args': (min_sound_len, min_silence_len, silence_thresh, seek_step)
            }
        return self.sound_intervals

    def plot_silence(self, min_sound_len:int=500, min_silence_len:int=500, silence_thresh:int=-24, seek_step:int=10):
        """Generate a pyplot showing sound and silence.

        Args:
            min_sound_len (int, optional): Minimum length of a sound for it to be registered (in ms). Defaults to 500.
            min_silence_len (int, optional): Minimum length of silence for it to be registered (in ms). Defaults to 500.
            silence_thresh (int, optional): Upper bound for quietness of a silence (in dFBS). Defaults to -24.
            seek_step (int, optional): Step size for interating over the segment (in ms). Defaults to 10.
        """
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