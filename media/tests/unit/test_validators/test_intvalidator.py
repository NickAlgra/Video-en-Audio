from attr import has
import pytest
from media.utils.validators import IntValidator


@pytest.fixture
def create_intval_cls():
    def fn(*args, **kwargs):
        return type('intval_cls', (), {'prop': IntValidator(*args, **kwargs)})
    return fn

@pytest.fixture(params=[
    (-20, -10),
    (-10, 0),
    (-5, 5),
    (1, 1),
    (0, 10),
    (10, 20)
])
def parametrized_bounds(request):
    min_, max_ = request.param
    return {
        'min_value': min_, 
        'max_value': max_
    }

@pytest.mark.parametrize('desired_bounds', [
    (),
    ('min_value',),
    ('max_value',),
    ('min_value', 'max_value')
])
def test_create(create_intval_cls, parametrized_bounds, desired_bounds):
    kwargs = {bound: parametrized_bounds[bound] for bound in desired_bounds}
    cls = create_intval_cls(**kwargs)
    assert isinstance(cls.prop, IntValidator)
    assert cls.prop._prop_name == 'prop'
    expected_bounds = [(bound, value) if bound in desired_bounds else (bound, None) for bound, value in parametrized_bounds.items()]
    for attr, value in expected_bounds:
        assert getattr(cls.prop, attr) == value
    
@pytest.mark.parametrize('min_, max_', [
    (-5, -10),
    (0, -5),
    (2, 1),
    (5, 0),
    (10, 5)
])
def test_create_invalid_bounds(min_, max_, create_intval_cls, error_contains):
    with pytest.raises(ValueError) as ex:
        create_intval_cls(min_, max_)
    assert error_contains(ex, [min_, max_])

# @pytest.mark.parametrize('bound_name', [
#     'min_value', 'max_value'
# ])
# @pytest.mark.parametrize('bound_value', [
#     10.5, 'hello', True, [1,2]
# ])
# def test_create_invalid_bound_type(bound_name, bound_value, create_intval_cls, error_contains):
#     with pytest.raises(TypeError) as ex:
#         create_intval_cls(**{bound_name: bound_value})
#     assert error_contains(ex, [bound_name, bound_value, type(bound_value), int])