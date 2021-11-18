import pytest
from media.utils.validators import BaseValidator


@pytest.mark.parametrize('valid_value', [
    123, 0, 'hello', '', 10.5, 0.0, [1,2], [], True, False
])
def test_validate_exists(valid_value):
    """Test if validate_exists raises no exceptions when provided with existing values."""
    BaseValidator.validate_exists('prop', valid_value)

def test_validate_exists_invalid():
    """Test if validate_exists raises the correct ValueError exception when provided with a None value."""
    with pytest.raises(ValueError) as ex:
        BaseValidator.validate_exists('prop', None)
    assert 'prop' in str(ex)


@pytest.mark.parametrize('value, correct_types', [
    (123, int), 
    ('hello', str), 
    ([1,2], list), 
    (True, bool), 
    ('hello', (int, float, str))
])
def test_validate_type(value, correct_types):
    """Test if validate_type raises no exceptions when checking if a value is of correct type(s)."""
    BaseValidator.validate_type('prop', value, correct_types)

@pytest.mark.parametrize(['value', 'wrong_types'], [
    (123, str), 
    (123, float), 
    ('hello', int), 
    ((1,2), list), 
    (10.5, int), 
    (123, (str, float))
])    
def test_validate_type_invalid(value, wrong_types, error_contains):
    """Test if validate_type raises the correct TypeError exception when checking if a value is of wrong type(s)."""
    with pytest.raises(TypeError) as ex:
        BaseValidator.validate_type('prop', value, wrong_types)
    assert error_contains(ex, ['prop', type(value), wrong_types])


@pytest.fixture(params=[
    (-20, -10),
    (-10, 0),
    (-5, 5),
    (1, 1),
    (0, 10),
    (10, 20)
])
def bounds_args(request):
    lower, upper = request.param
    return {
        'name': 'prop',
        'lower': lower,
        'upper': upper
    }

def test_validate_bounds_valid(bounds_args):
    """Test if validate_bounds raises no exceptions when checking if correct values fall within correct bounds."""
    valid_values = range(bounds_args['lower'], bounds_args['upper']+1)
    for val in valid_values:
        BaseValidator.validate_bounds(value=val, **bounds_args)

def test_validate_bounds_exceed_lower(bounds_args, error_contains):
    """Test if validate_bounds raises the correct ValueError exception if the values fall below the lower bound."""
    too_low_values = range(bounds_args['lower']-5, bounds_args['lower'])
    for val in too_low_values:
        with pytest.raises(ValueError) as ex:
            BaseValidator.validate_bounds(value=val, **bounds_args)
        assert error_contains(ex, [bounds_args['name'], val, bounds_args['lower']])
        
def test_validate_bounds_exceed_upper(bounds_args, error_contains):
    """Test if validate_bounds raises the correct ValueError exception if the values fall above the upper bound."""
    too_high_values = range(bounds_args['upper']+1, bounds_args['upper']+6)
    for val in too_high_values:
        with pytest.raises(ValueError) as ex:
            BaseValidator.validate_bounds(value=val, **bounds_args)
        assert error_contains(ex, [bounds_args['name'], val, bounds_args['upper']])


@pytest.fixture
def baseval_cls():
    return type('basic_cls', (), {'prop': BaseValidator()})

def test_create_class(baseval_cls):
    """Test if a class using a BaseValidator attribute can be succesfully created."""
    cls = baseval_cls
    assert hasattr(cls, 'prop')
    assert isinstance(cls.prop, BaseValidator)
    assert cls.prop._prop_name == 'prop'

def test_create_object(baseval_cls) -> None:
    """Test if an object of a class using a BaseValidator attribute can be succesfully created."""
    obj = baseval_cls()
    assert hasattr(obj, 'prop')

def test_get_set(baseval_cls):
    """Test if a BaseValidator attribute can be succesfully set and retrieved."""
    obj = baseval_cls()
    assert obj.prop == None
    obj.prop = 'hello'
    assert obj.prop == 'hello'