from pydio import _utils


class TestConstant:

    def test_repr(self):
        UUT = _utils.Constant('UUT')
        assert repr(UUT) == 'UUT'
