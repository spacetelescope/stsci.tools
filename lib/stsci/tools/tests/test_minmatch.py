from __future__ import absolute_import

import pytest

from ..minmatch import MinMatchDict, AmbiguousKeyError

BASEKEYS = tuple(['test', 'text', 'ten'])
BASEVALUES = tuple([1, 2, 10])


@pytest.fixture
def mmd_keys():
    keys = list(BASEKEYS)
    return keys


@pytest.fixture
def mmd_values():
    values = list(BASEVALUES)
    return values


@pytest.fixture
def mmd():
    d = MinMatchDict()
    for value in zip(*[BASEKEYS, BASEVALUES]):
        d.add(*value)
    return d


def test_ambiguous_assignment_key(mmd):
    with pytest.raises(AmbiguousKeyError):
        mmd['te'] = 5


def test_ambiguous_assignment_get_t(mmd):
    with pytest.raises(AmbiguousKeyError):
        mmd.get('t')


def test_ambiguous_assignment_get_tes(mmd):
    with pytest.raises(AmbiguousKeyError):
        mmd.get('te')


def test_ambiguous_assignment_del_tes(mmd):
    with pytest.raises(AmbiguousKeyError):
        del mmd['te']


def test_invalid_key_assignment(mmd):
    with pytest.raises(KeyError):
        mmd['t']


def test_dict_sort(mmd, mmd_keys):
    result = [key for key, _ in sorted(mmd.items())]
    assert result[0] == 'ten'
    assert result[-1] == 'text'


@pytest.mark.parametrize('key', mmd_keys())
def test_get_values(mmd, key):
    assert mmd.get(key)


def test_missing_key_returns_none(mmd):
    assert mmd.get('teq') is None


def test_getall(mmd, mmd_values):
    return mmd.getall('t')


def test_getall_returns_expected_values(mmd, mmd_values):
    result = mmd.getall('t')
    for value in mmd_values:
        assert value in result


def test_del_key(mmd):
    del mmd['test']


def test_del_keys(mmd, mmd_keys):
    for key in mmd_keys:
        del mmd[key]


def test_clear_dict(mmd):
    mmd.clear()
    assert mmd == dict()


def test_has_key(mmd, mmd_keys):
    for key in mmd_keys:
        # Ditch last character in string
        if len(key) > 3:
            key = key[:-1]

        assert mmd.has_key(key, exact=False)


def test_has_key_exact(mmd, mmd_keys):
    for key in mmd_keys:
        assert mmd.has_key(key, exact=True)


def test_key_in_dict(mmd, mmd_keys):
    for key in mmd_keys:
        assert key in mmd


def test_update_dict(mmd):
    new_dict = dict(ab=0)
    mmd.update(new_dict)
    assert 'test' in mmd and 'ab' in mmd
