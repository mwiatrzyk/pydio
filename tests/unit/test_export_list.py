import pytest

from pydio import _export_list

UUT = _export_list.ExportList


@pytest.fixture
def export():
    return _export_list.ExportList()


def test_export_single_function(export: UUT):

    @export
    def dummy():
        pass

    assert export == ["dummy"]


def test_export_two_functions(export: UUT):
    @export
    def first():
        pass

    @export
    def second():
        pass

    assert export == ["first", "second"]


def test_export_class(export: UUT):

    @export
    class Dummy:
        pass

    assert export == ["Dummy"]


def test_export_fails_if_name_could_not_be_determined(export: UUT):
    with pytest.raises(TypeError) as excinfo:
        export(None)
    assert str(excinfo.value) == "cannot export None; the '__name__' property is missing"
