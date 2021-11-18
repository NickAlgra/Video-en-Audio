from datetime import datetime
from collections.abc import Sequence
from typing import Union


class BaseValidator:

    def __set_name__(self, owner, prop_name):
        self._prop_name = prop_name

    def __get__(self, instance, owner):
        if instance is None:
            return self
        else:
            return instance.__dict__.get(self._prop_name)
            
    def __set__(self, instance, value):
        value = self.validate(self._prop_name, value)
        instance.__dict__[self._prop_name] = value

    def validate(self, name, value):
        self.validate_exists(name, value)
        return value

    @staticmethod
    def validate_exists(name, value):
        if value is None:
            raise ValueError(f"{name} should not be None")
    
    @staticmethod
    def validate_type(name, value, desired_types:Union[type, tuple[type, ...]]):
        """Determine if value is of any of the desired types.

        Args:
            name (str): Name of the property being checked.
            value (Any): Value of the property being checked.
            desired_types (type | tuple[type, ...]): The types which value is allowed to be.

        Raises:
            TypeError: If value is not any of the desired types.
        """
        if not isinstance(value, desired_types):
            raise TypeError(f"{name} should be of type {desired_types}, not type {type(value)}")

    @staticmethod
    def validate_bounds(name, value, lower, upper):
        if lower is not None and value < lower:
            raise ValueError(f"{name} should be at least {lower}, but is currently {value}")
        if upper is not None and value > upper:
            raise ValueError(f"{name} should be at most {upper}, but is currently {value}")


class StringValidator(BaseValidator):

    def __init__(self, min_length:int=0, max_length:int=None, valid_characters:Sequence=None) -> None:
        super().__init__()

        for v in (min_length, max_length):
            self.validate_type(v, v, desired_types=(int, type(None)))
        if max_length is not None and min_length > max_length:
            raise ValueError(f"Minimum length {min_length} cannot be greater than maximum length {max_length}")
        self.min_length = min_length
        self.max_length = max_length

        self.validate_type('valid_characters', valid_characters, desired_types=(Sequence, type(None)))
        self.valid_characters = valid_characters
    
    def validate(self, name, value):
        value = super().validate(name, value)
        self.validate_type(name, value, desired_types=str)
        self.validate_bounds(f'len({name})', len(value), lower=self.min_length, upper=self.max_length)
        self.validate_chars(name, value, valid_chars=self.valid_characters)
        return value

    @staticmethod
    def validate_chars(name, value, valid_chars):
        if valid_chars is not None:
            for char in value:
                if char not in valid_chars:
                    raise ValueError(f"{name} contains invalid character '{char}'")


class IntValidator(BaseValidator):

    def __init__(self, min_value:int=None, max_value:int=None) -> None:
        super().__init__()

        for v in (min_value, max_value):
            self.validate_type(v, v, (int, type(None)))
        if min_value is not None and max_value is not None and min_value > max_value:
            raise ValueError(f"Minimum value {min_value} cannot be greater than maximum value {max_value}")
        self.min_value = min_value
        self.max_value = max_value
    
    def validate(self, name:str, value):
        value = super().validate(name, value)
        self.validate_type(name, value, desired_types=int)
        self.validate_bounds(name, value, lower=self.min_value, upper=self.max_value)
        return value


class DateValidator(BaseValidator):
    
    def __init__(self, formats:tuple[str, ...]=None, earliest:datetime=None, latest:datetime=None):
        super().__init__()
        if formats is not None:
            for fmt in formats:
                self.validate_type('format', fmt, desired_types=str)
        self.formats = formats

        for date in (earliest, latest):
            self.validate_type('date', date, desired_types=(datetime, type(None)))
            
        if earliest is not None and latest is not None and earliest > latest:
            raise ValueError(f"Earliest date {earliest} cannot be later than latest date {latest}")
        self.earliest = earliest
        self.latest = latest

    def validate(self, name, value):
        value = super().validate(name, value)
        self.validate_type(name, value, (str, datetime))
        if isinstance(value, str):
            if self.formats is None:
                raise TypeError(f"Date for {name} was given as string but no formats were specified")
            value = self.str_to_datetime(value, self.formats)
        self.validate_bounds(name, value, lower=self.earliest, upper=self.latest)
        return value

    @staticmethod
    def str_to_datetime(date:str, formats:tuple[str, ...]) -> datetime:
        for fmt in formats:
            try:
                return datetime.strptime(date, fmt)
            except ValueError:
                pass
        raise ValueError(f"Date {date} does not match any of the specified formats {formats}")