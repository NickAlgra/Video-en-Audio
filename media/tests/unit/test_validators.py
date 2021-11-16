import pytest
from media.utils import validators
from datetime import datetime

@pytest.fixture
def thing():
    class Thing:
        prop = validators.BaseValidator()
    return Thing()

@pytest.fixture
def bounds_args():
    return {
        'name': 'prop',
        'lower': 1,
        'upper': 10,
    }

class TestBaseValidator:

    def test_validate_exists(self):
        validators.BaseValidator.validate_exists('prop', 123)

    def test_validate_exists_invalid(self):
        with pytest.raises(ValueError):
            validators.BaseValidator.validate_exists('prop', None)

    def test_validate_type(self):
        validators.BaseValidator.validate_type('prop', 123, int)
        validators.BaseValidator.validate_type('prop', 'hello', (int, str))
        validators.BaseValidator.validate_type('prop', [1,2], list)
        
    def test_validate_type_invalid(self):
        with pytest.raises(TypeError):
            validators.BaseValidator.validate_type('prop', 123, str)
            validators.BaseValidator.validate_type('prop', 123, (str, list))

    def test_validate_bounds_valid(self, bounds_args):
        validators.BaseValidator.validate_bounds(value=5, **bounds_args)
    
    def test_validate_bounds_exceed_lower(self, bounds_args):
        with pytest.raises(ValueError):
            validators.BaseValidator.validate_bounds(value=0, **bounds_args)
            
    def test_validate_bounds_exceed_upper(self, bounds_args):
        with pytest.raises(ValueError):
            validators.BaseValidator.validate_bounds(value=11, **bounds_args)

    def test_create(self, thing):
        t = thing
        assert isinstance(type(thing).prop, validators.BaseValidator)

    def test_get_set(self, thing):
        assert thing.prop == None
        thing.prop = 'hello'
        assert thing.prop == 'hello'


@pytest.fixture
def intval_args():
    return {
        'min_value': 1,
        'max_value': 10,
    }


@pytest.fixture
def polygon(intval_args):
    class Polygon:
        sides = validators.IntValidator(**intval_args)
    return Polygon()


class TestIntValidator:

    def test_create(self, polygon, intval_args):
        for key, value in intval_args.items():
            assert getattr(type(polygon).sides, key) == value
        polygon.sides = 5

    def test_create_invalid_min_max(self, intval_args):
        with pytest.raises(ValueError) as ex:
            intval_args['min_value'] = 11
            class Polygon:
                sides = validators.IntValidator(**intval_args)
    
    def test_invalid_type(self, polygon):
        with pytest.raises(TypeError):
            polygon.sides = 'hello'

    def test_exceed_min(self, polygon):
        with pytest.raises(ValueError):
            polygon.sides = 0
    
    def test_exceed_max(self, polygon):
        with pytest.raises(ValueError):
            polygon.sides = 100


@pytest.fixture
def strval_args():
    return {
        'min_length': 1,
        'max_length': 5,
    }


@pytest.fixture
def person(strval_args):
    class Person:
        name = validators.StringValidator(**strval_args)
    return Person()

class TestStringValidator:

    def test_validate_chars(self):
        validators.StringValidator.validate_chars('prop', 'helloworld', 'abcdefghijklmnopqrstuvwxyz')
        
    def test_validate_chars_invalid(self):
        with pytest.raises(ValueError):
            validators.StringValidator.validate_chars('prop', 'hello_world', 'abcdefghijklmnopqrstuvwxyz')

    def test_create(self, person, strval_args):
        for key, value in strval_args.items():
            assert getattr(type(person).name, key) == value
        person.name = 'Nick'

    def test_create_invalid_min_max(self, strval_args):
        with pytest.raises(ValueError) as ex:
            strval_args['min_length'] = 6
            class Person:
                name = validators.StringValidator(**strval_args)

    def test_invalid_type(self, person):
        with pytest.raises(TypeError):
            person.name = 123

    def test_exceed_min(self, person):
        with pytest.raises(ValueError):
            person.name = ''
        
    def test_exceed_max(self, person):
        with pytest.raises(ValueError):
            person.name = 'Nicholas'


@pytest.fixture
def dateval_args():
    return {
        'formats': (
            '%H:%M:%S %d/%m/%Y',
        ),
        'earliest': datetime.utcfromtimestamp(946728000),
        'latest': datetime.utcnow()
    }


@pytest.fixture
def calender(dateval_args):
    class Calender:
        date = validators.DateValidator(**dateval_args)
    return Calender()


class TestDateValidator:

    def test_str_to_datetime(self):
        gold_std = datetime(year=2020, month=11, day=15, hour=13, minute=14, second=25)
        assert validators.DateValidator.str_to_datetime("13:14:25 15/11/2020", ('%H:%M:%S %d/%m/%Y',)) == gold_std

    def test_str_to_datetime_invalid(self):
        with pytest.raises(ValueError):
            validators.DateValidator.str_to_datetime("13-14-25 15-11-2020", ('%H:%M:%S %d/%m/%Y', "%d/%m/%Y %H:%M:%S"))

    def test_create(self, calender, dateval_args):
        for key, value in dateval_args.items():
            assert getattr(type(calender).date, key) == value
        calender.date = "13:14:25 15/11/2020"

    def test_create_invalid_min_max(self, dateval_args):
        with pytest.raises(ValueError) as ex:
            dateval_args['earliest'] = datetime(year=3000, month=1, day=1)
            class Calender:
                date = validators.DateValidator(**dateval_args)

    def test_invalid_type(self, calender):
        with pytest.raises(TypeError):
            calender.date = 13142515112020

    def test_exceed_min(self, calender):
        with pytest.raises(ValueError):
            calender.date = "13:14:25 15/11/1999"

    def test_exceed_min(self, calender):
        with pytest.raises(ValueError):
            calender.date = "13:14:25 15/11/3021"