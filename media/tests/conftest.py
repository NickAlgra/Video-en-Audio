import pytest

@pytest.fixture(scope='session')
def error_contains():
    def fn(ex, args):
        for arg in args:
            if str(arg) not in str(ex):
                return False
        return True
    return fn