import socket
import ssl
from unittest.mock import Mock

import httplib2
import pytest

from calendar_transport import CalendarHttp, FallbackHTTPSConnection


V6 = (socket.AF_INET6, socket.SOCK_STREAM, 6, '', ('2001:db8::1', 443, 0, 0))
V6_OTHER = (socket.AF_INET6, socket.SOCK_STREAM, 6, '', ('2001:db8::2', 443, 0, 0))
V4 = (socket.AF_INET, socket.SOCK_STREAM, 6, '', ('192.0.2.1', 443))


def connection_with_sockets(monkeypatch, addresses, sockets):
    connection = FallbackHTTPSConnection('www.googleapis.com', timeout=60, proxy_info=None)
    connection._context = Mock()
    monkeypatch.setattr(socket, 'getaddrinfo', Mock(return_value=addresses))
    monkeypatch.setattr(socket, 'socket', Mock(side_effect=sockets))
    return connection


def test_ipv6_timeout_falls_back_to_ipv4_before_other_ipv6(monkeypatch):
    ipv6, ipv4 = Mock(), Mock()
    ipv6.connect.side_effect = TimeoutError('IPv6 timed out')
    connection = connection_with_sockets(monkeypatch, [V6, V6_OTHER, V4], [ipv6, ipv4])

    connection.connect()

    ipv6.connect.assert_called_once_with(V6[4])
    ipv6.close.assert_called_once()
    ipv6.settimeout.assert_called_once_with(5)
    ipv4.connect.assert_called_once_with(V4[4])
    assert [call.args[0] for call in ipv4.settimeout.call_args_list] == [5, 60]
    connection._context.wrap_socket.assert_called_once_with(ipv4, server_hostname='www.googleapis.com')
    assert connection.sock is connection._context.wrap_socket.return_value


def test_working_ipv6_does_not_try_ipv4(monkeypatch):
    ipv6 = Mock()
    connection = connection_with_sockets(monkeypatch, [V6, V4], [ipv6])
    connection.connect()
    socket.socket.assert_called_once_with(*V6[:3])


def test_all_addresses_fail(monkeypatch):
    ipv6, ipv4 = Mock(), Mock()
    ipv6.connect.side_effect = TimeoutError('IPv6 timed out')
    ipv4.connect.side_effect = ConnectionRefusedError('IPv4 refused')
    connection = connection_with_sockets(monkeypatch, [V6, V4], [ipv6, ipv4])
    with pytest.raises(ConnectionRefusedError, match='IPv4 refused'):
        connection.connect()
    ipv6.close.assert_called_once()
    ipv4.close.assert_called_once()


def test_certificate_error_is_not_retried(monkeypatch):
    ipv6 = Mock()
    connection = connection_with_sockets(monkeypatch, [V6, V4], [ipv6])
    connection._context.wrap_socket.side_effect = ssl.SSLCertVerificationError('bad certificate')
    with pytest.raises(ssl.SSLCertVerificationError):
        connection.connect()
    ipv6.close.assert_called_once()
    socket.socket.assert_called_once()


def test_proxy_keeps_library_connection_handling(monkeypatch):
    connection = FallbackHTTPSConnection('www.googleapis.com', timeout=60)
    connection.proxy_info = Mock()
    original_connect = Mock()
    monkeypatch.setattr(httplib2.HTTPSConnectionWithTimeout, 'connect', original_connect)
    connection.connect()
    original_connect.assert_called_once()


def test_transport_uses_fallback_connection(monkeypatch):
    request = Mock(return_value=('response', b''))
    monkeypatch.setattr(httplib2.Http, 'request', request)
    assert CalendarHttp().request('https://www.googleapis.com/test') == ('response', b'')
    assert request.call_args.kwargs['connection_type'] is FallbackHTTPSConnection
