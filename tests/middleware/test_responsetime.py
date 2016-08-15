#
# tests/test_http_request.py
#

import pytest
import growler
from unittest import mock


@pytest.fixture
def rt():
    return growler.middleware.ResponseTime()


@pytest.fixture
def req():
    return mock.MagicMock()


@pytest.fixture
def res():
    m = mock.MagicMock()
    m.headers = []
    return m


def test_standard_responsetime_format(rt):
    assert rt.format_timediff(4.2e-2) == '42.0'


def test_rounding_responsetime_format():
    rt = growler.middleware.ResponseTime(digits=5)
    assert rt.format_timediff(4.22384132e-2) == '42.23841'


def test_units_responsetime_format():
    rt = growler.middleware.ResponseTime(digits=5, units='s')
    assert rt.format_timediff(4.22384132e-2) == '0.04224'


def test_response(rt, req, res):
    rt(req, res)
    assert res.events.on.called
    cb = res.events.on.call_args_list[0][0][1]

    assert not res.set.called
    cb()
    assert res.set.called

    assert res.set.call_args_list[0][0][0] == 'X-Response-Time'
    assert res.set.call_args_list[0][0][1].endswith('ms')


def test_response_noclobber(rt, req, res):
    res.headers = ['X-Response-Time']
    rt.clobber_header = False
    rt(req, res)
    assert res.events.on.called
    cb = res.events.on.call_args_list[0][0][1]

    assert not res.set.called
    cb()
    assert not res.set.called


def test_response_clobber(rt, req, res):
    res.headers = ['X-Response-Time']
    rt.clobber_header = True
    rt(req, res)
    assert res.events.on.called
    cb = res.events.on.call_args_list[0][0][1]

    assert not res.set.called
    cb()
    assert res.set.called


def test_response_nosuffix(rt, req, res):
    rt.suffix = False
    rt.clobber_header = False
    rt(req, res)
    assert res.events.on.called
    cb = res.events.on.call_args_list[0][0][1]

    assert not res.set.called
    cb()
    assert res.set.called
    assert not res.set.call_args_list[0][0][1].endswith('ms')


def test_response_set_header(req, res):
    header = 'Fooo'
    rt = growler.middleware.ResponseTime(header=header)
    rt(req, res)
    assert res.events.on.called
    cb = res.events.on.call_args_list[0][0][1]
    assert not res.set.called
    cb()
    assert res.set.called
    assert res.set.call_args_list[0][0][0] == header


def test_response_log_out(req, res):
    m = mock.MagicMock()
    rt = growler.middleware.ResponseTime(log=m)
    rt(req, res)
    m.assert_not_called()
    cb = res.events.on.call_args_list[0][0][1]
    cb()
    # print(m.mock_calls)
    assert m.info.called
    assert isinstance(m.info.call_args_list[0][0][0], str)
