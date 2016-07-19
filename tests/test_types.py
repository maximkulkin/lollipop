import pytest
from zephyr.types import String


class TestString:
    def test_loading(self):
        assert String().load('foo') == 'foo'

    def test_dumping(self):
        assert String().dump('foo') == 'foo'
