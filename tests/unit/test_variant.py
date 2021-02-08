# ---------------------------------------------------------------------------
# tests/unit/test_variant.py
#
# Copyright (C) 2021 Maciej Wiatrzyk <maciej.wiatrzyk@gmail.com>
#
# This file is part of PyDio library and is released under the terms of the
# MIT license: http://opensource.org/licenses/mit-license.php.
#
# See LICENSE.txt for details.
# ---------------------------------------------------------------------------
from pydio.variant import Variant


class TestVariant:

    def test_create_variant(self):
        uut = Variant('foo', bar=42)
        assert uut.key == 'foo'
        assert uut.kwargs == {'bar': 42}
        assert str(uut) == "<Variant(key='foo', kwargs={'bar': 42})>"

    def test_check_equality_between_two_variants(self):
        assert Variant('foo') == Variant('foo')
        assert Variant('foo') != Variant('foo', a=1)
        assert Variant('foo', a=1) == Variant('foo', a=1)
        assert Variant('foo') != Variant('bar')
